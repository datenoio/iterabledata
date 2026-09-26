"""Behavior-pinning tests for parse_line_protocol (complexity refactor).

Pins the observable behavior of ``iterable.datatypes.ilp.parse_line_protocol``
before/after the behavior-preserving decomposition: the character-scan state
machine (quotes, escapes, space separators, timestamp detection), measurement/
tag splitting, field value parsing, and error paths. Includes several quirky
but stable behaviors (escaped commas in tags, ambiguous timestamps, unclosed
quotes) that must be preserved exactly.
"""

import pytest

from iterable.datatypes.ilp import parse_line_protocol


class TestBasicParsing:
    def test_simple_line_with_timestamp(self):
        result = parse_line_protocol("temperature value=23.5 1631022245000000000")
        assert result["measurement"] == "temperature"
        assert result["tags"] == {}
        assert result["fields"] == {"value": 23.5}
        assert result["time"] == "1631022245000000000"

    def test_tags_parsed(self):
        result = parse_line_protocol("temperature,sensor=abc123,location=room1 value=23.5 1631022245000000000")
        assert result["measurement"] == "temperature"
        assert result["tags"] == {"sensor": "abc123", "location": "room1"}
        assert result["fields"] == {"value": 23.5}

    def test_no_timestamp_key_absent(self):
        """Without a timestamp the result has no 'time' key at all."""
        result = parse_line_protocol("weather,location=us-midwest temperature=82,humidity=71")
        assert result["measurement"] == "weather"
        assert result["tags"] == {"location": "us-midwest"}
        assert result["fields"]["temperature"] == 82.0
        assert result["fields"]["humidity"] == 71.0
        assert "time" not in result

    def test_measurement_only(self):
        result = parse_line_protocol("m")
        assert result == {"measurement": "m", "tags": {}, "fields": {}}

    def test_trailing_space_stripped(self):
        result = parse_line_protocol("m ")
        assert result == {"measurement": "m", "tags": {}, "fields": {}}

    def test_leading_trailing_whitespace_stripped(self):
        result = parse_line_protocol("  temperature value=1  ")
        assert result["measurement"] == "temperature"
        assert result["fields"] == {"value": 1.0}

    def test_digit_tail_is_timestamp(self):
        result = parse_line_protocol("m x=1 123")
        assert result["fields"] == {"x": 1.0}
        assert result["time"] == "123"

    def test_tag_order_preserved(self):
        result = parse_line_protocol("m,z=1,a=2 x=1")
        assert list(result["tags"].keys()) == ["z", "a"]


class TestErrors:
    def test_empty_line_raises(self):
        with pytest.raises(ValueError, match="Empty line"):
            parse_line_protocol("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Empty line"):
            parse_line_protocol("   ")


class TestFieldValueTypes:
    def test_integer_suffix(self):
        result = parse_line_protocol("weather,location=us-midwest count=42i")
        assert result["fields"]["count"] == 42
        assert isinstance(result["fields"]["count"], int)

    def test_boolean_variants(self):
        assert parse_line_protocol("w active=t")["fields"]["active"] is True
        assert parse_line_protocol("w active=true")["fields"]["active"] is True
        assert parse_line_protocol("w active=FALSE")["fields"]["active"] is False
        assert parse_line_protocol("w active=f")["fields"]["active"] is False

    def test_negative_float(self):
        assert parse_line_protocol("m temp=-3.5")["fields"]["temp"] == -3.5

    def test_quoted_string(self):
        result = parse_line_protocol('w,location=us-midwest temperature=82,description="hot and humid"')
        assert result["fields"]["temperature"] == 82.0
        assert result["fields"]["description"] == "hot and humid"

    def test_quoted_string_with_comma(self):
        result = parse_line_protocol('m note="a,b",x=1')
        assert result["fields"] == {"note": "a,b", "x": 1.0}

    def test_quoted_escaped_quote(self):
        result = parse_line_protocol('m note="a\\"b"')
        assert result["fields"]["note"] == 'a"b'

    def test_quoted_newline_escape(self):
        result = parse_line_protocol('m note="a\\nb"')
        assert result["fields"]["note"] == "a\nb"

    def test_empty_value_is_none(self):
        assert parse_line_protocol("m x=")["fields"]["x"] is None

    def test_unquoted_passthrough_string(self):
        assert parse_line_protocol("m x=hello")["fields"]["x"] == "hello"

    def test_float_with_i_suffix_stays_string(self):
        """int() fails on '3.5' so the value falls through to the string default."""
        assert parse_line_protocol("m x=3.5i")["fields"]["x"] == "3.5i"


class TestQuirkyBehaviors:
    """Odd but stable outputs that the refactor must preserve."""

    def test_escaped_comma_in_tag_splits_anyway(self):
        """Tag splitting is a plain str.split(','); the escaped comma splits the tag."""
        result = parse_line_protocol("m,tag=a\\,b x=1")
        assert result["tags"] == {"tag": "a\\"}

    def test_escaped_space_in_tag_unescaped(self):
        result = parse_line_protocol("m,tag=a\\ b x=1")
        assert result["tags"] == {"tag": "a b"}

    def test_escaped_equals_in_tag_unescaped(self):
        result = parse_line_protocol("m,tag=a\\=b x=1")
        assert result["tags"] == {"tag": "a=b"}

    def test_space_in_measurement_switches_on_equals_ahead(self):
        """A space in the measurement part switches to fields when '=' lies ahead."""
        result = parse_line_protocol("m m2 x=1")
        assert result["measurement"] == "m"
        assert result["fields"] == {"m2 x": 1.0}

    def test_comma_without_equals_is_measurement_name(self):
        result = parse_line_protocol("meas,part x=1")
        assert result["measurement"] == "meas,part"
        assert result["tags"] == {}

    def test_tag_with_empty_key_skipped(self):
        result = parse_line_protocol("m,=v,k=2 x=1")
        assert result["tags"] == {"k": "2"}

    def test_tag_without_equals_skipped(self):
        result = parse_line_protocol("m,novalue,k=2 x=1")
        assert result["tags"] == {"k": "2"}

    def test_field_without_equals_ignored(self):
        result = parse_line_protocol("m x=1,stray")
        assert result["fields"] == {"x": 1.0}

    def test_unclosed_quote_value_kept_raw(self):
        result = parse_line_protocol('m note="abc')
        assert result["fields"] == {"note": '"abc'}

    def test_short_non_digit_tail_joins_field_value(self):
        """A short non-digit tail is not a timestamp; the space joins the field."""
        result = parse_line_protocol("m x=1 abc")
        assert result["fields"] == {"x": "1 abc"}
        assert "time" not in result

    def test_negative_digit_tail_joins_field_value(self):
        """'-5' is not isdigit() so it is not treated as a timestamp."""
        result = parse_line_protocol("m x=1 -5")
        assert result["fields"] == {"x": "1 -5"}
        assert "time" not in result

    def test_long_non_equals_tail_is_timestamp(self):
        """A long (>10 chars) tail without '=' is treated as a timestamp."""
        result = parse_line_protocol("m x=1 abcdefghijklmnop")
        assert result["fields"] == {"x": 1.0}
        assert result["time"] == "abcdefghijklmnop"

    def test_double_space_between_parts(self):
        result = parse_line_protocol("m  x=1")
        assert result["fields"] == {"x": 1.0}

    def test_trailing_backslash_kept_in_value(self):
        result = parse_line_protocol("m x=1\\")
        assert result["fields"] == {"x": "1\\"}


class TestIterableIntegration:
    def test_read_skips_malformed_lines(self, tmp_path):
        """ILPIterable.read with skip_empty=True skips unparseable lines."""
        from iterable.datatypes import ILPIterable

        path = tmp_path / "data.ilp"
        path.write_text("\n\nm1 x=1\nm2 x=2\n")
        iterable = ILPIterable(str(path))
        try:
            records = list(iterable)
        finally:
            iterable.close()
        assert [r["measurement"] for r in records] == ["m1", "m2"]

    def test_read_skip_empty_false_propagates_error(self, tmp_path):
        from iterable.datatypes import ILPIterable

        path = tmp_path / "data.ilp"
        path.write_text("m1 x=1\n")
        iterable = ILPIterable(str(path))
        try:
            next(iterable)
            with pytest.raises(StopIteration):
                iterable.read(skip_empty=False)
        finally:
            iterable.close()
