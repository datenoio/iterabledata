"""Write-support tests for the XML format (OpenSpec add-office-format-writes)."""

import pytest

from iterable import open_iterable


class TestXMLWrite:
    def test_roundtrip_honors_tagname(self, tmp_path):
        path = tmp_path / "out.xml"
        records = [{"name": "alpha", "value": 1}, {"name": "beta", "value": 2}]
        with open_iterable(str(path), mode="w", iterableargs={"tagname": "item"}) as target:
            for record in records:
                target.write(record)
        with open_iterable(str(path), iterableargs={"tagname": "item"}) as source:
            rows = list(source)
        # The reader yields raw text scalars.
        assert rows == [{"name": "alpha", "value": "1"}, {"name": "beta", "value": "2"}]

    def test_write_bulk(self, tmp_path):
        path = tmp_path / "bulk.xml"
        with open_iterable(str(path), mode="w") as target:
            target.write_bulk([{"n": 1}, {"n": 2}])
        with open_iterable(str(path), iterableargs={"tagname": "item"}) as source:
            assert len(list(source)) == 2

    def test_attributes_lists_nested_and_empty(self, tmp_path):
        path = tmp_path / "rich.xml"
        record = {
            "@id": "a1",
            "name": "alpha",
            "tags": ["x", "y"],
            "meta": {"k": "v"},
            "empty": None,
            "#text": "body",
        }
        with open_iterable(str(path), mode="w", iterableargs={"tagname": "row"}) as target:
            target.write(record)
        with open_iterable(str(path), iterableargs={"tagname": "row"}) as source:
            (row,) = list(source)
        assert row["@id"] == "a1"
        assert row["tags"] == ["x", "y"]
        assert row["meta"] == {"k": "v"}
        assert row["empty"] is None
        assert row["#text"] == "body"
        assert row["name"] == "alpha"

    def test_escaping(self, tmp_path):
        path = tmp_path / "esc.xml"
        with open_iterable(str(path), mode="w") as target:
            target.write({"text": "a < b & 'c' \"d\""})
        with open_iterable(str(path), iterableargs={"tagname": "item"}) as source:
            (row,) = list(source)
        assert row["text"] == "a < b & 'c' \"d\""

    def test_validation_hook_skip(self, tmp_path):
        path = tmp_path / "validated.xml"

        def reject_negative(row):
            if row.get("n", 0) < 0:
                raise ValueError("negative")
            return row

        with open_iterable(
            str(path), mode="w", iterableargs={"validation_hook": reject_negative, "on_validation_error": "skip"}
        ) as target:
            target.write({"n": 1})
            target.write({"n": -5})
        with open_iterable(str(path), iterableargs={"tagname": "item"}) as source:
            assert list(source) == [{"n": "1"}]

    def test_write_bulk_none_raises(self, tmp_path):
        path = tmp_path / "none.xml"
        with open_iterable(str(path), mode="w") as target:
            with pytest.raises(TypeError):
                target.write_bulk(None)
