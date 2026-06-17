"""Tests for ai.suggest_transform and apply_spec."""

from unittest.mock import MagicMock, patch

import pytest

from iterable.ai.suggest import suggest_transform
from iterable.ops import transform


class TestSuggestTransform:
    def test_suggest_transform_mocked(self):
        spec_json = '{"operations": [{"op": "rename", "mapping": {"old": "new"}}]}'
        with patch("iterable.ai.suggest.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = spec_json
            mock_get.return_value = mock_provider
            spec = suggest_transform("fixtures/2cols6rows.csv", goal="rename columns")
        assert spec["operations"][0]["op"] == "rename"

    def test_apply_spec_rename(self):
        rows = [{"a": 1, "b": 2}]
        spec = {"operations": [{"op": "rename", "mapping": {"a": "alpha"}}]}
        result = list(transform.apply_spec(rows, spec))
        assert result[0] == {"alpha": 1, "b": 2}

    def test_apply_spec_rejects_unknown_op(self):
        with pytest.raises(ValueError, match="Unknown transform"):
            list(transform.apply_spec([{"a": 1}], {"operations": [{"op": "exec_code"}]}))
