import pytest


def test_jsonl_roundtrip_hypothesis(tmp_path):
    """
    Property-style sanity check: JSONL write -> read returns the same records.

    This is skipped automatically if Hypothesis isn't installed.
    """
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis.strategies")

    from iterable.helpers.detect import open_iterable  # noqa: F401

    # Keep generated data small and strictly JSON-serializable.
    record_strategy = st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-10_000, max_value=10_000),
            st.text(max_size=50),
        ),
        max_size=10,
    )

    @hypothesis.given(st.lists(record_strategy, max_size=50))
    @hypothesis.settings(max_examples=25, suppress_health_check=[hypothesis.HealthCheck.too_slow])
    def _roundtrip(records):
        path = tmp_path / "rt.jsonl"
        with open_iterable(str(path), mode="w") as w:
            w.write_bulk(records)

        with open_iterable(str(path), mode="r") as r:
            out = list(r)

        assert out == records

    _roundtrip()
