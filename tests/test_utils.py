import pytest

from iterable.datatypes import CSVIterable
from iterable.helpers.utils import (
    detect_delimiter,
    detect_encoding_raw,
    dict_generator,
    get_dict_keys,
    get_dict_value,
    get_dict_value_deep,
    get_iterable_keys,
    guess_int_size,
    make_flat,
    normalize_extended_json,
    rowincount,
    strip_dict_fields,
)


class TestUtils:
    def test_rowincount_with_filename(self):
        """Test rowincount with filename"""
        count = rowincount(filename="fixtures/2cols6rows.csv")
        # Should have at least header + 6 rows
        assert count >= 6

    def test_rowincount_with_fileobj(self):
        """Test rowincount with file object"""
        with open("fixtures/2cols6rows.csv", "rb") as f:
            count = rowincount(fileobj=f)
            assert count >= 6

    def test_rowincount_error_no_args(self):
        """Test rowincount raises error with no arguments"""
        with pytest.raises(ValueError, match="Filename or fileobj should not be None"):
            rowincount()

    def test_detect_encoding_raw_with_filename(self):
        """Test detect_encoding_raw with filename"""
        result = detect_encoding_raw(filename="fixtures/ru_utf8_comma.csv")
        assert "encoding" in result
        assert result["encoding"] in ["utf-8", "ascii"]  # UTF-8 files may be detected as ASCII

    def test_detect_encoding_raw_with_stream(self):
        """Test detect_encoding_raw with stream"""
        with open("fixtures/ru_utf8_comma.csv", "rb") as f:
            result = detect_encoding_raw(stream=f)
            assert "encoding" in result

    def test_detect_delimiter_comma(self):
        """Test detect_delimiter with comma"""
        delimiter = detect_delimiter(filename="fixtures/ru_utf8_comma.csv")
        assert delimiter == ","

    def test_detect_delimiter_semicolon(self):
        """Test detect_delimiter with semicolon"""
        delimiter = detect_delimiter(filename="fixtures/ru_utf8_semicolon.csv")
        assert delimiter == ";"

    def test_detect_delimiter_tab(self):
        """Test detect_delimiter with tab"""
        delimiter = detect_delimiter(filename="fixtures/ru_utf8_tab.csv")
        assert delimiter == "\t"

    def test_detect_delimiter_with_stream(self):
        """Test detect_delimiter with stream"""
        with open("fixtures/ru_utf8_comma.csv", encoding="utf-8") as f:
            delimiter = detect_delimiter(stream=f, encoding="utf-8")
            assert delimiter == ","

    def test_get_dict_value_simple(self):
        """Test get_dict_value with simple key"""
        d = {"name": "test", "value": 42}
        result = get_dict_value(d, ["name"])
        assert result == ["test"]

    def test_get_dict_value_nested(self):
        """Test get_dict_value with nested keys"""
        d = {"user": {"name": "test", "age": 30}}
        result = get_dict_value(d, ["user", "name"])
        assert result == ["test"]

    def test_get_dict_value_list(self):
        """Test get_dict_value with list of dicts"""
        d = [{"name": "test1"}, {"name": "test2"}]
        result = get_dict_value(d, ["name"])
        assert result == ["test1", "test2"]

    def test_get_dict_value_none(self):
        """Test get_dict_value with None"""
        result = get_dict_value(None, ["key"])
        assert result == []

    def test_get_dict_value_missing_key(self):
        """Test get_dict_value with missing key"""
        d = {"other": "value"}
        result = get_dict_value(d, ["missing"])
        assert result == []

    def test_strip_dict_fields(self):
        """Test strip_dict_fields"""
        record = {"keep": "value1", "remove": "value2", "also_keep": "value3"}
        fields = [["keep"], ["also_keep"]]
        result = strip_dict_fields(record, fields)
        assert "keep" in result
        assert "also_keep" in result
        assert "remove" not in result

    def test_strip_dict_fields_nested(self):
        """Test strip_dict_fields with nested dict"""
        record = {"user": {"name": "test", "email": "test@example.com"}, "other": "value"}
        fields = [["user", "name"]]
        result = strip_dict_fields(record, fields)
        assert "user" in result
        assert "name" in result["user"]
        assert "email" not in result["user"]

    def test_dict_generator_simple(self):
        """Test dict_generator with simple dict"""
        d = {"name": "test", "value": 42}
        results = list(dict_generator(d))
        assert len(results) == 2
        assert ["name", "test"] in results
        assert ["value", 42] in results

    def test_dict_generator_nested(self):
        """Test dict_generator with nested dict"""
        d = {"user": {"name": "test", "age": 30}}
        results = list(dict_generator(d))
        assert ["user", "name", "test"] in results
        assert ["user", "age", 30] in results

    def test_dict_generator_with_list(self):
        """Test dict_generator with list values"""
        d = {"items": [{"name": "item1"}, {"name": "item2"}]}
        results = list(dict_generator(d))
        assert any("item1" in r for r in results)
        assert any("item2" in r for r in results)

    def test_dict_generator_skips_id(self):
        """Test dict_generator skips _id field"""
        d = {"_id": "skip", "name": "keep"}
        results = list(dict_generator(d))
        assert ["_id", "skip"] not in results
        assert ["name", "keep"] in results

    def test_dict_generator_non_dict(self):
        """Test dict_generator with non-dict input"""
        result = list(dict_generator("not a dict"))
        assert result == ["not a dict"]

    def test_guess_int_size_small(self):
        """Test guess_int_size with small value"""
        assert guess_int_size(100) == "uint8"
        assert guess_int_size(254) == "uint8"

    def test_guess_int_size_medium(self):
        """Test guess_int_size with medium value"""
        assert guess_int_size(1000) == "uint16"
        assert guess_int_size(65534) == "uint16"

    def test_guess_int_size_large(self):
        """Test guess_int_size with large value"""
        assert guess_int_size(100000) == "uint32"
        assert guess_int_size(1000000) == "uint32"

    def test_get_dict_keys(self):
        """Test get_dict_keys"""
        data = [{"name": "test1", "value": 1}, {"name": "test2", "value": 2, "extra": "field"}]
        keys = get_dict_keys(data)
        assert "name" in keys
        assert "value" in keys
        assert "extra" in keys

    def test_get_dict_keys_with_limit(self):
        """Test get_dict_keys with limit"""
        data = [{"key" + str(i): i} for i in range(10)]
        keys = get_dict_keys(data, limit=3)
        # Should only process first 3 items
        assert len(keys) <= 3

    def test_get_dict_keys_nested(self):
        """Test get_dict_keys with nested dicts"""
        data = [{"user": {"name": "test", "age": 30}}]
        keys = get_dict_keys(data)
        assert "user.name" in keys or "user" in keys

    def test_get_iterable_keys(self):
        """Test get_iterable_keys"""
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        keys = get_iterable_keys(iterable)
        assert len(keys) > 0
        # Should have keys from CSV
        assert any("id" in k.lower() or "name" in k.lower() for k in keys)
        iterable.close()

    def test_get_iterable_keys_with_limit(self):
        """Test get_iterable_keys with limit"""
        iterable = CSVIterable("fixtures/2cols6rows.csv")
        keys = get_iterable_keys(iterable, limit=2)
        iterable.close()
        # Should have some keys
        assert isinstance(keys, list)

    def test_get_dict_value_deep_simple(self):
        """Test get_dict_value_deep with simple key"""
        d = {"name": "test"}
        result = get_dict_value_deep(d, "name")
        assert result == "test"

    def test_get_dict_value_deep_nested(self):
        """Test get_dict_value_deep with nested key"""
        d = {"user": {"profile": {"name": "test"}}}
        result = get_dict_value_deep(d, "user.profile.name")
        assert result == "test"

    def test_get_dict_value_deep_missing(self):
        """Test get_dict_value_deep with missing key"""
        d = {"other": "value"}
        result = get_dict_value_deep(d, "missing")
        assert result is None

    def test_get_dict_value_deep_as_array(self):
        """Test get_dict_value_deep with as_array=True"""
        d = {"items": [{"name": "item1"}, {"name": "item2"}]}
        result = get_dict_value_deep(d, "items.name", as_array=True)
        assert isinstance(result, list)
        assert "item1" in result
        assert "item2" in result

    def test_get_dict_value_deep_list(self):
        """Test get_dict_value_deep with list of dicts"""
        d = [{"name": "test1"}, {"name": "test2"}]
        result = get_dict_value_deep(d, "name", as_array=True)
        assert isinstance(result, list)
        assert "test1" in result
        assert "test2" in result

    def test_get_dict_value_deep_custom_splitter(self):
        """Test get_dict_value_deep with custom splitter"""
        d = {"user": {"name": "test"}}
        result = get_dict_value_deep(d, "user/name", splitter="/")
        assert result == "test"

    def test_make_flat_simple(self):
        """Test make_flat with simple dict"""
        item = {"name": "test", "value": 42}
        result = make_flat(item)
        assert result == item

    def test_make_flat_with_list(self):
        """Test make_flat with list value"""
        item = {"name": "test", "items": [1, 2, 3]}
        result = make_flat(item)
        assert result["name"] == "test"
        assert isinstance(result["items"], str)  # List should be converted to string

    def test_make_flat_with_dict(self):
        """Test make_flat with nested dict"""
        item = {"name": "test", "user": {"age": 30}}
        result = make_flat(item)
        assert result["name"] == "test"
        assert isinstance(result["user"], str)  # Dict should be converted to string

    def test_make_flat_with_tuple(self):
        """Test make_flat with tuple value"""
        item = {"name": "test", "coords": (1, 2)}
        result = make_flat(item)
        assert result["name"] == "test"
        assert isinstance(result["coords"], str)  # Tuple should be converted to string

    def test_get_dict_value_path_simple(self):
        """Test get_dict_value_path with simple key"""
        from iterable.helpers.utils import get_dict_value_path

        d = {"name": "test"}
        result = get_dict_value_path(d, "name")
        assert result == "test"

    def test_get_dict_value_path_nested(self):
        """Test get_dict_value_path with nested key"""
        from iterable.helpers.utils import get_dict_value_path

        d = {"user": {"profile": {"name": "test"}}}
        result = get_dict_value_path(d, "user.profile.name")
        assert result == "test"

    def test_get_dict_value_path_with_prefix(self):
        """Test get_dict_value_path with explicit prefix"""
        from iterable.helpers.utils import get_dict_value_path

        d = {"user": {"name": "test"}}
        result = get_dict_value_path(d, "user.name", prefix=["user", "name"])
        assert result == "test"

    def test_guess_datatype_none(self):
        """Test guess_datatype with None"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype(None, qd)
        assert result["base"] == "empty"

    def test_guess_datatype_int(self):
        """Test guess_datatype with int"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype(42, qd)
        assert result["base"] == "int"

    def test_guess_datatype_float(self):
        """Test guess_datatype with float"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype(3.14, qd)
        assert result["base"] == "float"

    def test_guess_datatype_str_int(self):
        """Test guess_datatype with string that is digit"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("123", qd)
        assert result["base"] == "int"
        assert "subtype" in result

    def test_guess_datatype_str_float(self):
        """Test guess_datatype with string that is float"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("3.14", qd)
        assert result["base"] == "float"

    def test_guess_datatype_str_date(self):
        """Test guess_datatype with string that matches date pattern (now fixed)"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("2023-12-25", qd)
        assert result["base"] == "date"
        assert "pat" in result

    def test_guess_datatype_str_empty(self):
        """Test guess_datatype with empty string"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("   ", qd)
        assert result["base"] == "empty"

    def test_guess_datatype_str_regular(self):
        """Test guess_datatype with regular string"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("hello world", qd)
        assert result["base"] == "str"

    def test_guess_datatype_other_type(self):
        """Test guess_datatype with non-str/int/float type"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype([1, 2, 3], qd)
        assert result["base"] == "typed"

    def test_is_flat_object_simple(self):
        """Test is_flat_object with simple dict"""
        from iterable.helpers.utils import is_flat_object

        obj = {"name": "test", "age": 30}
        assert is_flat_object(obj) is True

    def test_is_flat_object_with_list(self):
        """Test is_flat_object with list value"""
        from iterable.helpers.utils import is_flat_object

        obj = {"name": "test", "items": [1, 2, 3]}
        assert is_flat_object(obj) is False

    def test_is_flat_object_with_tuple(self):
        """Test is_flat_object with tuple value"""
        from iterable.helpers.utils import is_flat_object

        obj = {"name": "test", "coords": (1, 2)}
        assert is_flat_object(obj) is False

    def test_is_flat_object_with_nested_dict(self):
        """Test is_flat_object with nested dict (now fixed)"""
        from iterable.helpers.utils import is_flat_object

        obj = {"name": "test", "user": {"age": 30}}
        assert is_flat_object(obj) is False

    def test_detect_delimiter_empty_file(self, tmp_path):
        """Test detect_delimiter with empty file returns default"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        delimiter = detect_delimiter(filename=str(empty_file))
        assert delimiter == ","

    def test_detect_delimiter_no_delimiter_found(self, tmp_path):
        """Test detect_delimiter when no delimiter found"""
        from iterable.helpers.utils import DEFAULT_DELIMITERS

        test_file = tmp_path / "test.csv"
        test_file.write_text("nodelimiterhere\nanotherline\n")
        delimiter = detect_delimiter(filename=str(test_file))
        # Should return one of the default delimiters
        assert delimiter in DEFAULT_DELIMITERS

    def test_rowincount_with_empty_file(self, tmp_path):
        """Test rowincount with empty file"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        count = rowincount(filename=str(empty_file))
        assert count == 0

    def test_get_dict_value_deep_list_empty(self):
        """Test get_dict_value_deep with empty list"""
        d = []
        result = get_dict_value_deep(d, "name", as_array=True)
        assert result == []

    def test_get_dict_value_deep_list_not_dict(self):
        """Test get_dict_value_deep with list of non-dicts"""
        # get_dict_value_deep should handle list of non-dicts gracefully
        d = ["item1", "item2"]
        result = get_dict_value_deep(d, "name")
        # Should return None for non-dict items
        assert result is None

    def test_is_flat_object_deeply_nested(self):
        """Test is_flat_object with deeply nested dict"""
        from iterable.helpers.utils import is_flat_object

        obj = {"level1": {"level2": {"level3": "value"}}}
        assert is_flat_object(obj) is False

    def test_count_file_newlines_with_filename(self, tmp_path):
        """Test count_file_newlines with filename"""
        from iterable.helpers.utils import count_file_newlines

        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline3\n")
        count = count_file_newlines(filename=str(test_file))
        assert count == 3

    def test_count_file_newlines_with_stream(self, tmp_path):
        """Test count_file_newlines with stream"""
        from iterable.helpers.utils import count_file_newlines

        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\n")
        with open(test_file, "rb") as f:
            count = count_file_newlines(stream=f)
        assert count == 2

    def test_count_file_newlines_empty_file(self, tmp_path):
        """Test count_file_newlines with empty file"""
        from iterable.helpers.utils import count_file_newlines

        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        count = count_file_newlines(filename=str(empty_file))
        assert count == 0

    def test_guess_datatype_str_date_fixed(self):
        """Test guess_datatype with string that matches date pattern (now fixed)"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("2023-12-25", qd)
        assert result["base"] == "date"
        assert "pat" in result

    def test_guess_datatype_str_leading_zero(self):
        """Test guess_datatype with string starting with 0"""
        import re

        from iterable.helpers.utils import guess_datatype

        qd = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        result = guess_datatype("0123", qd)
        assert result["base"] == "numstr"

    def test_detect_encoding_raw_empty_file(self, tmp_path):
        """Test detect_encoding_raw with empty file"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        result = detect_encoding_raw(filename=str(empty_file))
        assert "encoding" in result

    def test_detect_encoding_raw_with_limit(self, tmp_path):
        """Test detect_encoding_raw with custom limit"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content" * 1000)
        result = detect_encoding_raw(filename=str(test_file), limit=100)
        assert "encoding" in result

    def test_detect_delimiter_pipe(self, tmp_path):
        """Test detect_delimiter with pipe delimiter"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1|col2|col3\nval1|val2|val3\n")
        delimiter = detect_delimiter(filename=str(test_file))
        assert delimiter == "|"

    def test_detect_delimiter_with_threshold(self, tmp_path):
        """Test detect_delimiter with custom threshold"""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2,col3\nval1,val2,val3\nval4,val5,val6\n")
        delimiter = detect_delimiter(filename=str(test_file), threshold=0.5)
        assert delimiter == ","

    def test_get_dict_value_with_ordered_dict(self):
        """Test get_dict_value with OrderedDict"""
        from collections import OrderedDict

        d = OrderedDict([("name", "test"), ("value", 42)])
        result = get_dict_value(d, ["name"])
        assert result == ["test"]

    def test_get_dict_value_deep_nested_list(self):
        """Test get_dict_value_deep with nested list in dict"""
        d = {"items": [{"name": "item1"}, {"name": "item2"}]}
        result = get_dict_value_deep(d, "items.name", as_array=True)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_get_dict_value_deep_nested_missing(self):
        """Test get_dict_value_deep with missing nested key"""
        d = {"user": {"profile": {"name": "test"}}}
        result = get_dict_value_deep(d, "user.profile.missing")
        assert result is None

    def test_get_dict_value_path_missing_key(self):
        """Test get_dict_value_path with missing key raises error"""
        from iterable.helpers.utils import get_dict_value_path

        d = {"name": "test"}
        with pytest.raises(KeyError):
            get_dict_value_path(d, "missing")

    def test_strip_dict_fields_empty_fields(self):
        """Test strip_dict_fields with empty fields list"""
        record = {"keep": "value1", "remove": "value2"}
        fields = []
        result = strip_dict_fields(record, fields)
        # Should remove all fields
        assert len(result) == 0

    def test_dict_generator_with_tuple(self):
        """Test dict_generator with tuple values"""
        d = {"items": ({"name": "item1"}, {"name": "item2"})}
        results = list(dict_generator(d))
        assert any("item1" in str(r) for r in results)

    def test_get_dict_keys_empty_list(self):
        """Test get_dict_keys with empty list"""
        keys = get_dict_keys([])
        assert keys == []

    def test_get_dict_keys_no_limit(self):
        """Test get_dict_keys with limit=None"""
        data = [{"key" + str(i): i} for i in range(10)]
        keys = get_dict_keys(data, limit=None)
        assert len(keys) == 10

    def test_get_iterable_keys_empty(self):
        """Test get_iterable_keys with empty iterable"""
        import os
        import tempfile

        from iterable.datatypes import JSONLinesIterable

        # Create empty JSONL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            iterable = JSONLinesIterable(temp_file)
            keys = get_iterable_keys(iterable)
            iterable.close()
            assert keys == []
        finally:
            os.unlink(temp_file)


def test_normalize_extended_json_number_long():
    assert normalize_extended_json({"$numberLong": "654"}) == 654


def test_normalize_extended_json_oid():
    assert normalize_extended_json({"$oid": "4bdaa13d9d55821a51000000"}) == "4bdaa13d9d55821a51000000"


def test_normalize_extended_json_nested_record():
    record = {
        "text": "Эльмира",
        "count": {"$numberLong": "654"},
        "_id": {"$oid": "abc"},
        "ethnic": ["tur"],
    }
    assert normalize_extended_json(record) == {
        "text": "Эльмира",
        "count": 654,
        "_id": "abc",
        "ethnic": ["tur"],
    }
