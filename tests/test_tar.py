"""Tests for the TAR multi-file container."""

import io
import tarfile

import pytest

from iterable.datatypes import TARIterable
from iterable.exceptions import WriteNotSupportedError
from iterable.helpers.detect import detect_file_type, open_iterable

NAMES = ["John", "Mary", "Michael", "Anna", "Orban", "Lucy"]


class TestTAR:
    def test_id(self):
        assert TARIterable.id() == "tar"

    def test_is_streaming(self):
        iterable = TARIterable("fixtures/2cols6rows.tar")
        assert iterable.is_streaming() is True
        iterable.close()

    def test_iterate_all_members(self):
        """Records of each data member are yielded in archive order, tagged."""
        with open_iterable("fixtures/2cols6rows.tar") as source:
            rows = list(source)
        # 6 CSV rows + 6 JSONL rows
        assert len(rows) == 12
        assert rows[0]["_member"] == "2cols6rows.csv"
        assert rows[6]["_member"] == "2cols6rows_flat.jsonl"
        assert rows[0]["name"] == "John"
        assert rows[11]["name"] == "Lucy"

    def test_member_selection_exact(self):
        with open_iterable("fixtures/2cols6rows.tar", iterableargs={"members": "2cols6rows.csv"}) as source:
            rows = list(source)
        assert len(rows) == 6
        assert all(r["_member"] == "2cols6rows.csv" for r in rows)

    def test_member_selection_glob(self):
        with open_iterable("fixtures/2cols6rows.tar", iterableargs={"members": "*.jsonl"}) as source:
            rows = list(source)
        assert len(rows) == 6
        assert all(r["_member"] == "2cols6rows_flat.jsonl" for r in rows)

    def test_member_key_configurable(self):
        with open_iterable("fixtures/2cols6rows.tar", iterableargs={"member_key": "_src"}) as source:
            row = source.read()
        assert "_src" in row and "_member" not in row

    def test_member_tagging_disabled(self):
        with open_iterable("fixtures/2cols6rows.tar", iterableargs={"member_key": None}) as source:
            row = source.read()
        assert "_member" not in row

    def test_compressed_tarball_matches_plain(self):
        with open_iterable("fixtures/2cols6rows.tar") as plain:
            plain_rows = list(plain)
        with open_iterable("fixtures/2cols6rows.tar.gz") as gz:
            gz_rows = list(gz)
        assert gz_rows == plain_rows

    def test_tar_zst_via_codec(self, tmp_path):
        """`.tar.zst` layers the ZStandard codec under the tar container."""
        zstandard = pytest.importorskip("zstandard", reason="zstandard is required for .tar.zst")

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            payload = b"id,name\n1,zstd\n"
            info = tarfile.TarInfo(name="member.csv")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        archive = tmp_path / "data.tar.zst"
        archive.write_bytes(zstandard.ZstdCompressor().compress(buf.getvalue()))

        with open_iterable(str(archive)) as source:
            rows = list(source)
        assert rows == [{"id": "1", "name": "zstd", "_member": "member.csv"}]

    def test_read_bulk(self):
        iterable = TARIterable("fixtures/2cols6rows.tar")
        chunk = iterable.read_bulk(8)
        assert len(chunk) == 8
        rest = iterable.read_bulk(100)
        assert len(rest) == 4
        iterable.close()

    def test_reset(self):
        iterable = TARIterable("fixtures/2cols6rows.tar")
        first = iterable.read()
        _ = list(iterable)
        iterable.reset()
        again = iterable.read()
        assert again == first
        iterable.close()

    def test_list_members(self):
        iterable = TARIterable("fixtures/2cols6rows.tar")
        assert iterable.list_members() == ["2cols6rows.csv", "2cols6rows_flat.jsonl"]
        iterable.close()

    def test_write_not_supported(self):
        iterable = TARIterable("fixtures/2cols6rows.tar")
        with pytest.raises(WriteNotSupportedError):
            iterable.write({"a": 1})
        with pytest.raises(WriteNotSupportedError):
            iterable.write_bulk([{"a": 1}])
        iterable.close()

    def test_open_write_mode_rejected(self):
        with pytest.raises(WriteNotSupportedError):
            TARIterable("fixtures/2cols6rows.tar", mode="w")


class TestTARSafety:
    @staticmethod
    def _tar_with_member(path, member_name, payload=b"id,name\n1,evil\n"):
        with tarfile.open(path, "w") as tar:
            info = tarfile.TarInfo(name=member_name)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))

    def test_traversal_member_skipped(self, tmp_path, caplog):
        """Members with `..` traversal are skipped and never touch the filesystem."""
        archive = tmp_path / "evil.tar"
        self._tar_with_member(str(archive), "../evil.csv")

        with open_iterable(str(archive)) as source:
            rows = list(source)
        assert rows == []
        assert not (tmp_path.parent / "evil.csv").exists()

    def test_absolute_member_skipped(self, tmp_path):
        archive = tmp_path / "evil_abs.tar"
        self._tar_with_member(str(archive), "/tmp/evil.csv")

        with open_iterable(str(archive)) as source:
            rows = list(source)
        assert rows == []

    def test_safe_members_still_read_alongside_unsafe(self, tmp_path):
        archive = tmp_path / "mixed.tar"
        payload = b"id,name\n1,ok\n"
        with tarfile.open(str(archive), "w") as tar:
            bad = tarfile.TarInfo(name="../evil.csv")
            bad.size = len(payload)
            tar.addfile(bad, io.BytesIO(payload))
            good = tarfile.TarInfo(name="good.csv")
            good.size = len(payload)
            tar.addfile(good, io.BytesIO(payload))

        with open_iterable(str(archive)) as source:
            rows = list(source)
        assert len(rows) == 1
        assert rows[0]["_member"] == "good.csv"


class TestTARDetection:
    def test_detect_by_extension(self):
        result = detect_file_type("fixtures/2cols6rows.tar")
        assert result["success"]
        assert result["datatype"] == TARIterable
        assert result["codec"] is None

    def test_detect_tar_gz(self):
        result = detect_file_type("fixtures/2cols6rows.tar.gz")
        assert result["success"]
        assert result["datatype"] == TARIterable

    def test_detect_by_content_magic(self, tmp_path):
        from iterable.helpers.content_detection import detect_file_type_from_content

        path = tmp_path / "noext"
        with tarfile.open(str(path), "w") as tar:
            payload = b"id\n1\n"
            info = tarfile.TarInfo(name="member.csv")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        with open(path, "rb") as f:
            result = detect_file_type_from_content(f)
        assert result is not None
        assert result[0] == "tar"
        assert result[2] == "magic_number"
