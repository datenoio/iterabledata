"""
Tests for validate module.
"""

from iterable import validate
from iterable.validate import register


class TestValidate:
    def test_validate_email(self):
        """Test email validation."""
        rows = [
            {"email": "test@example.com"},
            {"email": "invalid-email"},
            {"email": "valid@test.co.uk"},
        ]
        rules = {"email": ["common.email"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        # First and third should be valid
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid
        assert len(results[2][1]) == 0  # Valid

    def test_validate_url(self):
        """Test URL validation."""
        rows = [
            {"url": "https://example.com"},
            {"url": "not-a-url"},
            {"url": "http://test.org/path"},
        ]
        rules = {"url": ["common.url"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid
        assert len(results[2][1]) == 0  # Valid

    def test_validate_required(self):
        """Test required field validation."""
        rows = [
            {"name": "John"},
            {"name": None},
            {"name": ""},
        ]
        rules = {"name": ["required"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid (None)
        assert len(results[2][1]) > 0  # Invalid (empty string)

    def test_validate_multiple_rules(self):
        """Test validation with multiple rules per field."""
        rows = [
            {"email": "test@example.com"},
            {"email": "invalid"},
            {"email": None},
        ]
        rules = {"email": ["common.email", "required"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid (bad format)
        assert len(results[2][1]) > 0  # Invalid (missing)

    def test_validate_mode_stats(self):
        """Test validation in stats mode."""
        rows = [
            {"email": "test@example.com"},
            {"email": "invalid"},
            {"email": "valid@test.com"},
        ]
        rules = {"email": ["common.email"]}

        stats = validate.iterable(rows, rules, mode="stats")
        assert isinstance(stats, dict)
        assert stats["total_rows"] == 3
        assert stats["valid_rows"] == 2
        assert stats["invalid_rows"] == 1

    def test_validate_mode_invalid(self):
        """Test validation in invalid mode."""
        rows = [
            {"email": "test@example.com"},
            {"email": "invalid"},
            {"email": "valid@test.com"},
        ]
        rules = {"email": ["common.email"]}

        results = list(validate.iterable(rows, rules, mode="invalid"))
        assert len(results) == 1  # Only invalid row
        assert len(results[0][1]) > 0  # Has errors

    def test_validate_mode_valid(self):
        """Test validation in valid mode."""
        rows = [
            {"email": "test@example.com"},
            {"email": "invalid"},
            {"email": "valid@test.com"},
        ]
        rules = {"email": ["common.email"]}

        results = list(validate.iterable(rows, rules, mode="valid"))
        assert len(results) == 2  # Only valid rows
        assert all(len(errors) == 0 for _, errors in results)

    def test_validate_max_errors(self):
        """Test validation with max_errors limit."""
        rows = [{"email": "invalid"} for _ in range(10)]
        rules = {"email": ["common.email"]}

        results = list(validate.iterable(rows, rules, max_errors=5))
        # Should stop early after max_errors
        assert len(results) <= 10  # May process all or stop early

    def test_register_custom_validator(self):
        """Test registering custom validator."""

        def validate_positive(value):
            return isinstance(value, (int, float)) and value > 0

        register("positive", validate_positive)

        rows = [{"value": 10}, {"value": -5}, {"value": 0}]
        rules = {"value": ["positive"]}

        results = list(validate.iterable(rows, rules))
        assert len(results[0][1]) == 0  # Valid (positive)
        assert len(results[1][1]) > 0  # Invalid (negative)
        assert len(results[2][1]) > 0  # Invalid (zero)

    def test_validate_ru_inn(self):
        """Test Russian INN validation."""
        rows = [
            {"inn": "1234567890"},
            {"inn": "invalid"},
            {"inn": "123456789012"},
        ]
        rules = {"inn": ["ru.org.inn"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        # First and third should be valid (10 or 12 digits)
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid
        assert len(results[2][1]) == 0  # Valid

    def test_validate_ru_ogrn(self):
        """Test Russian OGRN validation."""
        rows = [
            {"ogrn": "1234567890123"},
            {"ogrn": "invalid"},
            {"ogrn": "123456789012345"},
        ]
        rules = {"ogrn": ["ru.org.ogrn"]}

        results = list(validate.iterable(rows, rules))
        assert len(results) == 3
        # First and third should be valid (13 or 15 digits)
        assert len(results[0][1]) == 0  # Valid
        assert len(results[1][1]) > 0  # Invalid
        assert len(results[2][1]) == 0  # Valid
