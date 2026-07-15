"""Regression tests for untrusted-input hardening.

Covers:
- XXE: external entities are never resolved by the hardened XML helpers.
- Schema validation: type names are resolved via an explicit map, never eval.
- Filter expressions: the AST whitelist rejects injection attempts.
"""

import io

import pytest

from iterable.helpers.validation import schema_validator
from iterable.ops.filter import _safe_eval_expr, _validate_expr


class TestXXEHardening:
    """External entities must not be resolved when parsing XML."""

    XXE_DOC = (
        b'<?xml version="1.0"?>\n'
        b"<!DOCTYPE root [\n"
        b'  <!ENTITY xxe SYSTEM "file:///etc/passwd">\n'
        b"]>\n"
        b"<root><item>&xxe;</item></root>\n"
    )

    def test_safe_parse_does_not_resolve_external_entities(self):
        pytest.importorskip("lxml", reason="lxml required for XML support")
        from iterable.helpers.xmlsec import safe_parse

        tree = safe_parse(io.BytesIO(self.XXE_DOC))
        item = tree.getroot().find("item")
        text = item.text or ""
        assert "root:" not in text, "external entity was resolved!"

    def test_safe_iterparse_does_not_resolve_external_entities(self):
        pytest.importorskip("lxml", reason="lxml required for XML support")
        from iterable.helpers.xmlsec import safe_iterparse

        texts = []
        for _event, elem in safe_iterparse(io.BytesIO(self.XXE_DOC), events=("end",)):
            if elem.tag == "item":
                texts.append(elem.text or "")
        assert all("root:" not in t for t in texts), "external entity was resolved!"

    def test_xml_iterable_does_not_resolve_external_entities(self, tmp_path):
        # Rejecting the document outright is also acceptable; what must never
        # happen is the entity silently expanding to file contents.
        pytest.importorskip("lxml", reason="lxml required for XML support")
        from iterable.datatypes.xml import XMLIterable

        path = tmp_path / "xxe.xml"
        path.write_bytes(self.XXE_DOC)
        try:
            with XMLIterable(str(path), options={"tagname": "item"}) as source:
                for row in source:
                    assert "root:" not in str(row), "external entity was resolved!"
        except Exception as e:
            assert "root:" not in str(e), "external entity was resolved!"


class TestValidationTypeResolution:
    """schema_validator resolves type names without eval."""

    @pytest.mark.parametrize(
        "type_name,value",
        [
            ("int", 1),
            ("integer", 1),
            ("float", 1.5),
            ("double", 1.5),
            ("str", "x"),
            ("string", "x"),
            ("bool", True),
            ("boolean", False),
        ],
    )
    def test_supported_type_names_pass(self, type_name, value):
        validator = schema_validator({"fields": {"f": {"type": type_name}}})
        assert validator({"f": value}) == {"f": value}

    def test_type_mismatch_rejected(self):
        validator = schema_validator({"fields": {"f": {"type": "int"}}})
        with pytest.raises(ValueError, match="expected 'int'"):
            validator({"f": [1, 2]})

    def test_malicious_type_name_is_not_executed(self):
        # With eval() this would have executed arbitrary code; now it is just
        # an unknown type name that never matches.
        evil = "__import__('os').system('true')"
        validator = schema_validator({"fields": {"f": {"type": evil}}})
        with pytest.raises(ValueError, match="Schema validation failed"):
            validator({"f": 1})


class TestFilterExpressionWhitelist:
    """Filter expressions are restricted to a safe AST subset."""

    def test_legitimate_expressions_still_work(self):
        row = {"status": "active", "price": 150, "tag": "a"}
        assert _safe_eval_expr("`status` == 'active' and `price` > 100", row)
        assert _safe_eval_expr("`tag` in ['a', 'b']", row)
        assert _safe_eval_expr("not (`price` < 100)", row)
        assert _safe_eval_expr("`price` > 100 + 40", row)
        assert not _safe_eval_expr("`status` != 'active'", row)

    @pytest.mark.parametrize(
        "expr",
        [
            # dunder / attribute escape attempts
            "().__class__.__bases__[0].__subclasses__()",
            "`x`.__class__",
            # function calls other than field access
            "open('/etc/passwd')",
            "__import__('os').system('true')",
            "exec('pass')",
            # subscripts, lambdas, comprehensions, f-strings
            "row['x']",
            "(lambda: 1)()",
            "[x for x in [1]]",
            # walrus / assignment-adjacent tricks
            "(y := 1)",
            # unknown bare names
            "os",
        ],
    )
    def test_injection_attempts_rejected(self, expr):
        with pytest.raises(ValueError):
            _validate_expr(expr)
        with pytest.raises(ValueError):
            _safe_eval_expr(expr, {"x": 1})

    def test_power_operator_rejected(self):
        # ** is excluded from the arithmetic whitelist (DoS via huge numbers).
        with pytest.raises(ValueError):
            _validate_expr("`x` > 2 ** 9999999")
