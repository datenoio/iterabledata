"""Behavior-pinning tests for AnnotatedCSVIterable.read (complexity refactor).

Pins the observable behavior of ``AnnotatedCSVIterable.read`` before/after the
behavior-preserving decomposition: annotation-row skipping, datatype alignment
(non-empty columns, full header, numeric inference), type conversion, default
value application, and position tracking.
"""

from datetime import datetime, timezone

import pytest

from iterable.datatypes import AnnotatedCSVIterable


@pytest.fixture
def csv_path(tmp_path):
    def _write(content: str, name: str = "data.csv") -> str:
        path = tmp_path / name
        path.write_text(content)
        return str(path)

    return _write


def _read_all(path: str, **kwargs):
    iterable = AnnotatedCSVIterable(path, **kwargs)
    try:
        return list(iterable)
    finally:
        iterable.close()


class TestDatatypeConversion:
    def test_basic_types_converted(self, csv_path):
        path = csv_path(
            "#datatype,string,long,double,boolean\n"
            "#group,false,false,false,false\n"
            ",name,count,price,active\n"
            ",Item1,10,19.99,true\n"
            ",Item2,20,29.99,false\n"
        )
        records = _read_all(path)
        assert len(records) == 2
        assert records[0]["name"] == "Item1"
        assert records[0]["count"] == 10
        assert isinstance(records[0]["count"], int)
        assert records[0]["price"] == 19.99
        assert isinstance(records[0]["price"], float)
        assert records[0]["active"] is True
        assert records[1]["active"] is False

    def test_datetime_rfc3339_conversion(self, csv_path):
        path = csv_path("#datatype,string,dateTime:RFC3339\n,name,_time\n,a,2025-12-19T15:12:51Z\n")
        records = _read_all(path)
        assert records[0]["_time"] == datetime(2025, 12, 19, 15, 12, 51, tzinfo=timezone.utc)

    def test_unparseable_values_stay_strings(self, csv_path):
        path = csv_path("#datatype,string,long,double\n,name,count,price\n,a,notanint,notafloat\n")
        records = _read_all(path)
        assert records[0]["count"] == "notanint"
        assert records[0]["price"] == "notafloat"

    def test_empty_values_stay_empty_strings(self, csv_path):
        """The ``if value else value`` guard keeps empty strings unconverted."""
        path = csv_path("#datatype,string,long\n,name,count\n,a,\n")
        records = _read_all(path)
        assert records[0]["count"] == ""
        assert records[0]["name"] == "a"

    def test_boolean_truthy_variants(self, csv_path):
        path = csv_path("#datatype,string,boolean,boolean,boolean,boolean\n,name,b1,b2,b3,b4\n,a,t,1,yes,other\n")
        records = _read_all(path)
        assert records[0]["b1"] is True
        assert records[0]["b2"] is True
        assert records[0]["b3"] is True
        assert records[0]["b4"] is False

    def test_no_annotations_returns_strings(self, csv_path):
        path = csv_path("name,count\na,10\n")
        records = _read_all(path)
        assert records == [{"name": "a", "count": "10"}]


class TestDatatypeAlignment:
    def test_datatypes_align_with_non_empty_columns(self, csv_path):
        """InfluxDB layout: leading empty header column, datatypes skip it."""
        path = csv_path("#datatype,string,long\n#group,false,false\n,name,count\n,a,7\n")
        records = _read_all(path)
        assert records[0]["name"] == "a"
        assert records[0]["count"] == 7

    def test_datatypes_align_with_full_header(self, csv_path):
        """Datatypes covering every column (including empty first) align by index."""
        path = csv_path("#datatype,string,string,long\n,name,count\n,a,7\n")
        records = _read_all(path)
        assert records[0]["count"] == 7
        assert records[0]["name"] == "a"

    def test_misaligned_datatypes_numeric_inference_values(self, csv_path):
        """When datatype count matches neither layout, trailing columns get numeric inference."""
        path = csv_path("#datatype,string\n,name,count,ratio,label\n,a,7,2.5,x\n")
        records = _read_all(path)
        assert records[0]["count"] == 7
        assert isinstance(records[0]["count"], int)
        assert records[0]["ratio"] == 2.5
        assert isinstance(records[0]["ratio"], float)
        assert records[0]["label"] == "x"

    def test_headerless_fallback_alignment(self, csv_path):
        """With datatypes but header_row=None, datatypes apply by iteration order."""
        path = csv_path("a,10\nb,20\n")
        iterable = AnnotatedCSVIterable(path, keys=["name", "count"])
        try:
            # Force the no-header fallback path (first line became the header at init)
            iterable.header_row = None
            iterable.datatypes = ["string", "long"]
            row = iterable.read()
        finally:
            iterable.close()
        # Fieldnames come from the init-time header; values convert by position
        assert row == {"a": "b", "10": 20}


class TestDefaultValues:
    def test_default_applied_to_empty_value(self, csv_path):
        path = csv_path(
            "#datatype,string,long\n#group,false,false\n#default,_result,0\n,name,count\n,Item1,10\n,Item2,\n"
        )
        records = _read_all(path)
        assert records[0]["count"] == 10
        assert records[1]["count"] == 0
        assert isinstance(records[1]["count"], int)

    def test_default_string_not_converted_without_datatype(self, csv_path):
        path = csv_path("#default,,fallback\n,name,note\n,a,\n")
        records = _read_all(path)
        assert records[0]["note"] == "fallback"

    def test_empty_default_marker_ignored(self, csv_path):
        """Empty default values are never applied; the empty string passes through."""
        path = csv_path("#datatype,string,long\n#default,,\n,name,count\n,a,\n")
        records = _read_all(path)
        assert records[0]["count"] == ""


class TestRowSkipping:
    def test_annotation_rows_skipped(self, csv_path):
        path = csv_path("#datatype,string,long\n#group,false,false\n,name,count\n,a,1\n,b,2\n")
        records = _read_all(path)
        assert [r["name"] for r in records] == ["a", "b"]
        assert len(records) == 2

    def test_hash_first_value_row_skipped(self, csv_path):
        """Data rows whose first value starts with '#' are treated as annotations."""
        path = csv_path("name,count\n#comment,1\na,2\n")
        records = _read_all(path)
        assert len(records) == 1
        assert records[0]["name"] == "a"

    def test_hash_in_middle_value_not_skipped(self, csv_path):
        """Only the first key/value triggers the annotation skip; middle '#' values pass through."""
        path = csv_path("name,note,count\na,#tag,5\n")
        records = _read_all(path)
        assert len(records) == 1
        assert records[0]["note"] == "#tag"

    def test_pos_increments_per_read(self, csv_path):
        path = csv_path("name,count\na,1\nb,2\n")
        iterable = AnnotatedCSVIterable(path)
        try:
            iterable.read()
            assert iterable.pos == 1
            iterable.read()
            assert iterable.pos == 2
        finally:
            iterable.close()

    def test_stop_iteration_at_end(self, csv_path):
        path = csv_path("name\na\n")
        iterable = AnnotatedCSVIterable(path)
        try:
            iterable.read()
            with pytest.raises(StopIteration):
                iterable.read()
        finally:
            iterable.close()


class TestAnnotationsParsed:
    def test_annotations_exposed(self, csv_path):
        path = csv_path("#datatype,string,long\n#group,false,true\n#default,_result,0\n,name,count\n,a,1\n")
        iterable = AnnotatedCSVIterable(path)
        try:
            assert iterable.annotations["datatype"] == ["string", "long"]
            assert iterable.annotations["group"] == [False, True]
            assert iterable.annotations["default"] == ["_result", "0"]
            assert iterable.datatypes == ["string", "long"]
            assert iterable.group_flags == [False, True]
            assert iterable.default_values == ["_result", "0"]
        finally:
            iterable.close()
