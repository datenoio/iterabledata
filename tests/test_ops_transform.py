"""
Tests for ops.transform module.
"""

from iterable.ops import transform


class TestTransform:
    def test_head_csv_file(self):
        """Test getting first N rows from CSV."""
        rows = list(transform.head("fixtures/2cols6rows.csv", n=3))
        assert len(rows) == 3

    def test_head_iterable(self):
        """Test getting first N rows from iterable."""
        rows = [{"a": i} for i in range(10)]
        head_rows = list(transform.head(rows, n=5))
        assert len(head_rows) == 5
        assert head_rows[0]["a"] == 0

    def test_tail_csv_file(self):
        """Test getting last N rows from CSV."""
        rows = transform.tail("fixtures/2cols6rows.csv", n=3)
        assert len(rows) == 3

    def test_tail_iterable(self):
        """Test getting last N rows from iterable."""
        rows = [{"a": i} for i in range(10)]
        tail_rows = transform.tail(rows, n=3)
        assert len(tail_rows) == 3
        assert tail_rows[-1]["a"] == 9

    def test_sample_rows(self):
        """Test random sampling of rows."""
        rows = [{"a": i} for i in range(100)]
        sampled = list(transform.sample_rows(rows, n=10, seed=42))
        assert len(sampled) == 10
        # With seed, should be reproducible
        sampled2 = list(transform.sample_rows(rows, n=10, seed=42))
        assert len(sampled2) == 10

    def test_sample_rows_smaller_than_n(self):
        """Test sampling when dataset is smaller than n."""
        rows = [{"a": i} for i in range(5)]
        sampled = list(transform.sample_rows(rows, n=10))
        assert len(sampled) == 5

    def test_deduplicate_by_key(self):
        """Test deduplication by key fields."""
        rows = [
            {"email": "a@test.com", "name": "A"},
            {"email": "b@test.com", "name": "B"},
            {"email": "a@test.com", "name": "C"},  # Duplicate email
        ]
        unique = list(transform.deduplicate(rows, keys=["email"]))
        assert len(unique) == 2

    def test_deduplicate_keep_first(self):
        """Test deduplication keeping first occurrence."""
        rows = [
            {"id": 1, "value": "first"},
            {"id": 1, "value": "second"},
        ]
        unique = list(transform.deduplicate(rows, keys=["id"], keep="first"))
        assert len(unique) == 1
        assert unique[0]["value"] == "first"

    def test_deduplicate_keep_last(self):
        """Test deduplication keeping last occurrence."""
        rows = [
            {"id": 1, "value": "first"},
            {"id": 1, "value": "second"},
        ]
        unique = list(transform.deduplicate(rows, keys=["id"], keep="last"))
        assert len(unique) == 1
        assert unique[0]["value"] == "second"

    def test_select_fields(self):
        """Test selecting specific fields."""
        rows = [
            {"a": 1, "b": 2, "c": 3},
            {"a": 4, "b": 5, "c": 6},
        ]
        selected = list(transform.select(rows, fields=["a", "b"]))
        assert len(selected) == 2
        assert "a" in selected[0]
        assert "b" in selected[0]
        assert "c" not in selected[0]

    def test_select_rename(self):
        """Test selecting and renaming fields."""
        rows = [
            {"old_name": "value1"},
            {"old_name": "value2"},
        ]
        selected = list(transform.select(rows, fields={"old_name": "new_name"}))
        assert len(selected) == 2
        assert "new_name" in selected[0]
        assert "old_name" not in selected[0]
        assert selected[0]["new_name"] == "value1"

    def test_slice_rows(self):
        """Test slicing rows by range."""
        rows = [{"a": i} for i in range(10)]
        sliced = list(transform.slice_rows(rows, start=2, end=5))
        assert len(sliced) == 3
        assert sliced[0]["a"] == 2
        assert sliced[-1]["a"] == 4

    def test_slice_rows_no_end(self):
        """Test slicing rows without end."""
        rows = [{"a": i} for i in range(10)]
        sliced = list(transform.slice_rows(rows, start=5))
        assert len(sliced) == 5
        assert sliced[0]["a"] == 5

    def test_slice_rows_csv_file(self):
        """Test slicing rows from CSV file."""
        sliced = list(transform.slice_rows("fixtures/2cols6rows.csv", start=1, end=4))
        assert len(sliced) <= 3

    def test_enum_field_int(self):
        """Test adding integer sequence field."""
        rows = [{"name": "A"}, {"name": "B"}]
        result = list(transform.enum_field(rows, field="id", type="int", start=1))
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

    def test_enum_field_uuid(self):
        """Test adding UUID field."""
        rows = [{"name": "A"}]
        result = list(transform.enum_field(rows, field="id", type="uuid"))
        assert len(result) == 1
        assert "id" in result[0]
        assert isinstance(result[0]["id"], str)
        assert len(result[0]["id"]) == 36  # UUID length

    def test_reverse(self):
        """Test reversing row order."""
        rows = [{"a": 1}, {"a": 2}, {"a": 3}]
        result = list(transform.reverse(rows))
        assert len(result) == 3
        assert result[0]["a"] == 3
        assert result[-1]["a"] == 1

    def test_fill_missing_forward(self):
        """Test forward fill strategy."""
        rows = [{"status": "active"}, {"status": None}, {"status": "pending"}]
        result = list(transform.fill_missing(rows, field="status", strategy="forward"))
        assert result[1]["status"] == "active"  # Filled from previous

    def test_fill_missing_constant(self):
        """Test constant fill strategy."""
        rows = [{"category": None}, {"category": "A"}]
        result = list(transform.fill_missing(rows, field="category", strategy="constant", value="unknown"))
        assert result[0]["category"] == "unknown"

    def test_rename_fields(self):
        """Test renaming fields."""
        rows = [{"old_name": "value1"}, {"old_name": "value2"}]
        result = list(transform.rename_fields(rows, {"old_name": "new_name"}))
        assert "new_name" in result[0]
        assert "old_name" not in result[0]
        assert result[0]["new_name"] == "value1"

    def test_explode_array(self):
        """Test exploding array field."""
        rows = [{"id": 1, "tags": ["a", "b", "c"]}]
        result = list(transform.explode(rows, field="tags"))
        assert len(result) == 3
        assert result[0]["tags"] == "a"

    def test_explode_string(self):
        """Test exploding delimited string field."""
        rows = [{"id": 1, "categories": "a,b,c"}]
        result = list(transform.explode(rows, field="categories", separator=","))
        assert len(result) == 3
        assert result[0]["categories"] == "a"

    def test_replace_values(self):
        """Test value replacement."""
        rows = [{"status": "old_status"}, {"status": "new_status"}]
        result = list(transform.replace_values(rows, field="status", pattern="old", replacement="updated"))
        assert result[0]["status"] == "updated_status"

    def test_replace_values_regex(self):
        """Test regex value replacement."""
        rows = [{"text": "Price: 100 dollars"}]
        result = list(transform.replace_values(rows, field="text", pattern=r"\d+", replacement="XXX", regex=True))
        assert "XXX" in result[0]["text"]

    def test_sort_rows(self):
        """Test sorting rows."""
        rows = [{"value": 3}, {"value": 1}, {"value": 2}]
        result = list(transform.sort_rows(rows, by=["value"]))
        assert result[0]["value"] == 1
        assert result[-1]["value"] == 3

    def test_sort_rows_multiple_fields(self):
        """Test sorting by multiple fields."""
        rows = [
            {"status": "active", "id": 2},
            {"status": "inactive", "id": 1},
            {"status": "active", "id": 1},
        ]
        result = list(transform.sort_rows(rows, by=["status", "id"], desc=[True, False]))
        assert result[0]["status"] == "inactive"

    def test_transpose(self):
        """Test transposing rows and columns."""
        rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = list(transform.transpose(rows))
        assert len(result) == 2  # Two fields become two rows

    def test_split(self):
        """Test splitting field into multiple fields."""
        rows = [{"full_name": "John Doe"}]
        result = list(transform.split(rows, field="full_name", separator=" ", into=["first", "last"]))
        assert result[0]["first"] == "John"
        assert result[0]["last"] == "Doe"
        assert "full_name" not in result[0]

    def test_fixlengths(self):
        """Test fixing field lengths."""
        rows = [{"code": "A"}, {"code": "Very Long Code"}]
        result = list(transform.fixlengths(rows, lengths={"code": 5}))
        assert len(result[0]["code"]) == 5
        assert len(result[1]["code"]) == 5

    def test_cat(self):
        """Test concatenating iterables."""
        rows1 = [{"a": 1}]
        rows2 = [{"a": 2}]
        result = list(transform.cat(rows1, rows2))
        assert len(result) == 2

    def test_join_inner(self):
        """Test inner join."""
        left = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        right = [{"id": 1, "value": 10}, {"id": 3, "value": 30}]
        result = list(transform.join(left, right, on="id", join_type="inner"))
        assert len(result) == 1
        assert result[0]["name"] == "A"
        assert result[0]["right_value"] == 10

    def test_join_left(self):
        """Test left join."""
        left = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        right = [{"id": 1, "value": 10}]
        result = list(transform.join(left, right, on="id", join_type="left"))
        assert len(result) >= 1

    def test_diff(self):
        """Test set difference."""
        left = [{"id": 1}, {"id": 2}, {"id": 3}]
        right = [{"id": 2}]
        result = list(transform.diff(left, right, keys=["id"]))
        assert len(result) == 2
        assert result[0]["id"] == 1

    def test_exclude(self):
        """Test excluding rows."""
        all_rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        exclude_rows = [{"id": 2}]
        result = list(transform.exclude(all_rows, exclude_rows, keys=["id"]))
        assert len(result) == 2
        assert all(r["id"] != 2 for r in result)
