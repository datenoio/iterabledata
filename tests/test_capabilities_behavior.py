"""Behavior-pinning tests for _detect_capabilities (complexity refactor).

Pins the observable behavior of ``iterable.helpers.capabilities._detect_capabilities``
before/after the behavior-preserving decomposition: the introspection fallback path
used for plugin formats without a declarative descriptor. Covers read/write/bulk
detection, the write-support heuristic (base-class default, WriteNotSupportedError
source scan, uninspectable methods), static capability declarations
(totals/tables/flat-only), streaming detection (explicit declaration, known
non-streaming list, conditional hook, default), and descriptor value overlay.
"""

from iterable.base import BaseIterable
from iterable.datatypes import CSVIterable, JSONIterable, XMLIterable
from iterable.exceptions import WriteNotSupportedError
from iterable.helpers.capabilities import _detect_capabilities

ALL_KEYS = {
    "readable",
    "writable",
    "bulk_read",
    "bulk_write",
    "totals",
    "streaming",
    "flat_only",
    "tables",
    "compression",
    "nested",
    "native_bulk_read",
    "native_bulk_write",
    "read_memory",
    "write_memory",
    "selection",
    "codec_support",
    "source_constraints",
    "maturity",
}


class _MinimalReadable(BaseIterable):
    """read only; every other method is the base-class default."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration


class _RealWrite(BaseIterable):
    """write overridden with a real implementation."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def write(self, record):
        self.pos += 1
        self.fobj.write(record)


class _WriteNotSupportedShort(BaseIterable):
    """write overridden but only raises WriteNotSupportedError (<=3 effective lines)."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def write(self, record):
        raise WriteNotSupportedError(format_id="x", reason="nope")


class _LongWriteNotSupported(BaseIterable):
    """write mentions WriteNotSupportedError but has more than 3 effective lines."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def write(self, record):
        """Write a record."""
        if record is None:
            raise WriteNotSupportedError(format_id="x", reason="nope")
        self.fobj.write(record)


class _BuiltinWrite(BaseIterable):
    """write is an uninspectable builtin; getsource raises -> assumed supported."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    write = len


class _NoAttrsAtAll:
    """Not a BaseIterable subclass; exposes nothing."""


class _RaisingId(BaseIterable):
    """id() raises TypeError -> treated as having no format id."""

    @staticmethod
    def id():
        raise TypeError("boom")

    def read(self, skip_empty=True):
        raise StopIteration


class _ReadOnlyRegistered(BaseIterable):
    """id() names a registered read-only format (pcap)."""

    @staticmethod
    def id():
        return "pcap"

    def read(self, skip_empty=True):
        raise StopIteration


class _CsvIdBaseWrite(BaseIterable):
    """Registered writable id (csv) with the base-default write."""

    @staticmethod
    def id():
        return "csv"

    def read(self, skip_empty=True):
        raise StopIteration


class _CsvIdRealWrite(BaseIterable):
    """Registered writable id (csv) with a real write override."""

    @staticmethod
    def id():
        return "csv"

    def read(self, skip_empty=True):
        raise StopIteration

    def write(self, record):
        self.pos += 1
        self.fobj.write(record)


class _RaisingTotals(BaseIterable):
    """has_totals raises TypeError -> totals becomes None."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    @staticmethod
    def has_totals():
        raise TypeError("boom")


class _RaisingTables(BaseIterable):
    """has_tables raises AttributeError -> tables becomes None."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    @staticmethod
    def has_tables():
        raise AttributeError("boom")


class _RaisingFlatonly(BaseIterable):
    """is_flatonly raises TypeError -> flat_only/nested become None."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    @staticmethod
    def is_flatonly():
        raise TypeError("boom")


class _FlatTables(BaseIterable):
    """Declares totals, tables and flat-only."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    @staticmethod
    def has_totals():
        return True

    @staticmethod
    def has_tables():
        return True

    @staticmethod
    def is_flatonly():
        return True


class _ExplicitStreaming(BaseIterable):
    """Declares is_streaming() True below the base classes."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def is_streaming(self):
        return True


class _InstanceDependentStreaming(BaseIterable):
    """is_streaming depends on instance state; calling it with None raises."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def is_streaming(self):
        return self._streaming  # noqa: F821 - AttributeError when called with None


class _ConditionalStreaming(BaseIterable):
    """Exposes the _should_use_streaming hook."""

    @staticmethod
    def id():
        return None

    def read(self, skip_empty=True):
        raise StopIteration

    def _should_use_streaming(self):
        return True


class _KnownNonStreaming(BaseIterable):
    """id() names a known non-streaming format (arff)."""

    @staticmethod
    def id():
        return "arff"

    def read(self, skip_empty=True):
        raise StopIteration


class TestResultShape:
    def test_all_keys_present_for_real_format(self):
        caps = _detect_capabilities(CSVIterable)
        assert set(caps.keys()) == ALL_KEYS

    def test_all_keys_present_for_minimal_class(self):
        caps = _detect_capabilities(_MinimalReadable)
        assert set(caps.keys()) == ALL_KEYS

    def test_defaults_for_unknown_class(self):
        """Introspection defaults: unknown fields stay None/'unknown'/empty."""
        caps = _detect_capabilities(_MinimalReadable)
        assert caps["native_bulk_read"] is None
        assert caps["native_bulk_write"] is None
        assert caps["read_memory"] == "unknown"
        assert caps["write_memory"] == "unknown"
        assert caps["selection"] == []
        assert caps["codec_support"] == []
        assert caps["source_constraints"] == []
        assert caps["maturity"] == "stable"


class TestRealFormats:
    def test_csv(self):
        caps = _detect_capabilities(CSVIterable)
        assert caps["readable"] is True
        assert caps["writable"] is True
        assert caps["bulk_read"] is True
        assert caps["bulk_write"] is True
        assert caps["totals"] is True
        assert caps["tables"] is False
        assert caps["flat_only"] is True
        assert caps["nested"] is False
        assert caps["streaming"] is True
        assert caps["compression"] is True

    def test_json(self):
        caps = _detect_capabilities(JSONIterable)
        assert caps["readable"] is True
        assert caps["writable"] is True
        assert caps["flat_only"] is False
        assert caps["nested"] is True
        assert caps["tables"] is False
        assert caps["streaming"] is True

    def test_xml_tables(self):
        caps = _detect_capabilities(XMLIterable)
        assert caps["readable"] is True
        assert caps["tables"] is True
        assert caps["flat_only"] is False
        assert caps["nested"] is True


class TestReadableBulk:
    def test_minimal_class_readable_via_base_methods(self):
        """read/read_bulk/write_bulk exist via the base class; read is readable."""
        caps = _detect_capabilities(_MinimalReadable)
        assert caps["readable"] is True
        assert caps["bulk_read"] is True
        assert caps["bulk_write"] is True

    def test_bare_object_reports_nothing(self):
        """A class without any methods reports False across the method flags."""
        caps = _detect_capabilities(_NoAttrsAtAll)
        assert caps["readable"] is False
        assert caps["writable"] is False
        assert caps["bulk_read"] is False
        assert caps["bulk_write"] is False
        # streaming/compression fall back to the readable value
        assert caps["streaming"] is False
        assert caps["compression"] is False


class TestWritableDetection:
    def test_base_default_write_not_writable(self):
        caps = _detect_capabilities(_MinimalReadable)
        assert caps["writable"] is False

    def test_real_write_override_writable(self):
        caps = _detect_capabilities(_RealWrite)
        assert caps["writable"] is True

    def test_short_write_not_supported_stub_not_writable(self):
        caps = _detect_capabilities(_WriteNotSupportedShort)
        assert caps["writable"] is False

    def test_long_write_mentioning_error_writable(self):
        """More than 3 effective lines with WriteNotSupportedError counts as implemented."""
        caps = _detect_capabilities(_LongWriteNotSupported)
        assert caps["writable"] is True

    def test_uninspectable_write_assumed_writable(self):
        caps = _detect_capabilities(_BuiltinWrite)
        assert caps["writable"] is True

    def test_registered_read_only_id_not_writable(self):
        """A registered read-only format id short-circuits write introspection."""
        caps = _detect_capabilities(_ReadOnlyRegistered)
        assert caps["writable"] is False

    def test_registered_writable_id_base_default_write(self):
        caps = _detect_capabilities(_CsvIdBaseWrite)
        assert caps["writable"] is False

    def test_registered_writable_id_real_write(self):
        caps = _detect_capabilities(_CsvIdRealWrite)
        assert caps["writable"] is True

    def test_raising_id_treated_as_no_id(self):
        caps = _detect_capabilities(_RaisingId)
        assert caps["readable"] is True
        assert caps["writable"] is False


class TestStaticDeclarations:
    def test_defaults_false_when_methods_missing(self):
        """Bare object without declarations reports False (not None)."""
        caps = _detect_capabilities(_NoAttrsAtAll)
        assert caps["totals"] is False
        assert caps["tables"] is False
        assert caps["flat_only"] is False
        assert caps["nested"] is True

    def test_declared_totals_tables_flat(self):
        caps = _detect_capabilities(_FlatTables)
        assert caps["totals"] is True
        assert caps["tables"] is True
        assert caps["flat_only"] is True
        assert caps["nested"] is False

    def test_raising_totals_becomes_none(self):
        caps = _detect_capabilities(_RaisingTotals)
        assert caps["totals"] is None

    def test_raising_tables_becomes_none(self):
        caps = _detect_capabilities(_RaisingTables)
        assert caps["tables"] is None

    def test_raising_flatonly_becomes_none_pair(self):
        caps = _detect_capabilities(_RaisingFlatonly)
        assert caps["flat_only"] is None
        assert caps["nested"] is None


class TestStreamingDetection:
    def test_explicit_is_streaming_true(self):
        caps = _detect_capabilities(_ExplicitStreaming)
        assert caps["streaming"] is True

    def test_instance_dependent_is_streaming_assumed_true(self):
        """A declaration that needs an instance raises on None -> treated as True."""
        caps = _detect_capabilities(_InstanceDependentStreaming)
        assert caps["streaming"] is True

    def test_conditional_streaming_hook(self):
        caps = _detect_capabilities(_ConditionalStreaming)
        assert caps["streaming"] is True

    def test_known_non_streaming_format_id(self):
        caps = _detect_capabilities(_KnownNonStreaming)
        assert caps["streaming"] is False

    def test_default_streaming_matches_readable(self):
        caps = _detect_capabilities(_MinimalReadable)
        assert caps["streaming"] is True


class TestDescriptorOverlay:
    def test_registered_id_overlays_descriptor_values(self):
        """A class whose id() names a described format inherits descriptor values."""
        caps = _detect_capabilities(_CsvIdBaseWrite)
        assert caps["native_bulk_read"] is False
        assert caps["native_bulk_write"] is True
        assert caps["read_memory"] == "bounded"
        assert caps["write_memory"] == "bounded"
        assert caps["codec_support"] == ["gzip", "bz2", "xz", "zstd"]
        assert caps["maturity"] == "stable"

    def test_unregistered_id_keeps_unknowns(self):
        caps = _detect_capabilities(_MinimalReadable)
        assert caps["native_bulk_read"] is None
        assert caps["read_memory"] == "unknown"


class TestCompression:
    def test_compression_mirrors_readable(self):
        assert _detect_capabilities(_RealWrite)["compression"] is True
        assert _detect_capabilities(_NoAttrsAtAll)["compression"] is False
