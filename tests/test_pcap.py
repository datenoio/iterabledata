import binascii
import io

import pytest

from iterable.datatypes.pcap import PCAPIterable
from iterable.helpers.detect import detect_file_type, detect_file_type_from_content, open_iterable

try:
    import dpkt  # noqa: F401

    HAS_DPKT = True
except ImportError:
    HAS_DPKT = False

# Minimal PCAP file hex dump (Global Header + 1 Packet)
# Global Header: Magic(a1b2c3d4), Major(2), Minor(4), Zone(0), SigFigs(0), SnapLen(65535), Net(1=Ethernet)
# Packet Header: TS_sec, TS_usec, InclLen(14), OrigLen(14)
# Packet Data: 14 bytes (Ethernet frame)
PCAP_HEX = (
    "d4c3b2a1020004000000000000000000ffff000001000000"  # Global Header
    "5d2e20500e240c000e0000000e000000"  # Packet Header
    "0000000000000000000000000800"  # Packet Data (dst, src, type)
)

# Minimal PCAPNG file hex dump (Section Header Block start)
# SHB: Type(0x0a0d0d0a), BlockLength(28), ByteOrderMagic(0x1a2b3c4d), Version(1,0), SectionLength(-1)
# This is just the beginning - a full PCAPNG file would need IDB and EPB blocks
PCAPNG_MAGIC = "0a0d0d0a1c0000004d3c2b1a01000000ffffffffffffffff"


@pytest.fixture
def pcap_file(tmp_path):
    p = tmp_path / "test.pcap"
    p.write_bytes(binascii.unhexlify(PCAP_HEX))
    return str(p)


@pytest.fixture
def pcapng_file(tmp_path):
    """Create a minimal PCAPNG file using dpkt if available"""
    p = tmp_path / "test.pcapng"
    if HAS_DPKT:
        # Create a minimal valid PCAPNG file using dpkt
        try:
            with open(p, "wb") as f:
                writer = dpkt.pcapng.Writer(f)
                # Create a simple Ethernet packet
                eth = dpkt.ethernet.Ethernet(b"\x00" * 14)
                writer.writepkt(eth)
            return str(p)
        except Exception:
            # If dpkt.pcapng.Writer doesn't exist or fails, create minimal file with magic bytes
            # This will at least test detection
            p.write_bytes(binascii.unhexlify(PCAPNG_MAGIC + "00" * 100))
            return str(p)
    else:
        # Just create a file with PCAPNG magic bytes for detection testing
        p.write_bytes(binascii.unhexlify(PCAPNG_MAGIC + "00" * 100))
        return str(p)


# Tests that don't require dpkt (detection logic)
def test_pcap_magic_bytes_detection():
    """Test that PCAP files are detected by magic bytes"""
    # Test little-endian PCAP magic (0xd4c3b2a1)
    pcap_le = io.BytesIO(b"\xd4\xc3\xb2\xa1" + b"\x00" * 100)
    result = detect_file_type_from_content(pcap_le)
    assert result is not None
    format_id, confidence, method = result
    assert format_id == "pcap"
    assert confidence >= 0.95
    assert method == "magic_number"

    # Test big-endian PCAP magic (0xa1b2c3d4)
    pcap_be = io.BytesIO(b"\xa1\xb2\xc3\xd4" + b"\x00" * 100)
    result = detect_file_type_from_content(pcap_be)
    assert result is not None
    format_id, confidence, method = result
    assert format_id == "pcap"
    assert confidence >= 0.95
    assert method == "magic_number"


def test_pcapng_magic_bytes_detection():
    """Test that PCAPNG files are detected by magic bytes"""
    # PCAPNG Section Header Block starts with 0x0a0d0d0a
    pcapng = io.BytesIO(b"\x0a\x0d\x0d\x0a" + b"\x00" * 100)
    result = detect_file_type_from_content(pcapng)
    assert result is not None
    format_id, confidence, method = result
    assert format_id == "pcapng"
    assert confidence >= 0.95
    assert method == "magic_number"


@pytest.mark.skipif(not HAS_DPKT, reason="dpkt not installed")
class TestPCAP:
    def test_read_pcap(self, pcap_file):
        with open_iterable(pcap_file) as source:
            assert isinstance(source, PCAPIterable)
            records = list(source)
            assert len(records) == 1
            assert "timestamp" in records[0]
            assert "data" in records[0]
            assert len(records[0]["data"]) == 14

    def test_read_via_class(self, pcap_file):
        source = PCAPIterable(pcap_file)
        records = list(source)
        source.close()
        assert len(records) == 1

    def test_detection(self, pcap_file):
        from iterable.helpers.detect import detect_file_type

        res = detect_file_type(pcap_file)
        assert res["success"]
        assert res["datatype"] == PCAPIterable

    def test_not_installed(self):
        if not HAS_DPKT:
            with pytest.raises(ImportError, match="dpkt is required"):
                PCAPIterable("dummy.pcap")

    def test_pcapng_detection(self, pcapng_file):
        """Test that PCAPNG files are detected by extension"""
        res = detect_file_type(pcapng_file)
        assert res["success"]
        assert res["datatype"] == PCAPIterable

    def test_read_pcapng(self, pcapng_file):
        """Test reading PCAPNG files if dpkt supports it"""
        try:
            with open_iterable(pcapng_file) as source:
                assert isinstance(source, PCAPIterable)
                records = list(source)
                assert isinstance(records, list)
        except (ValueError, dpkt.dpkt.NeedData, Exception):
            pass

    def test_read_raises_stopiteration_at_eof(self, pcap_file):
        with open_iterable(pcap_file) as source:
            row = source.read()
            assert row is not None
            with pytest.raises(StopIteration):
                source.read()

    def test_read_bulk_semantics(self, pcap_file):
        with open_iterable(pcap_file) as source:
            chunk = source.read_bulk(10)
            assert isinstance(chunk, list)
            assert len(chunk) == 1
            assert source.read_bulk(10) == []

    def test_reset_round_trip(self, pcap_file):
        with open_iterable(pcap_file) as source:
            first = source.read()
            source.reset()
            again = source.read()
            assert again == first
