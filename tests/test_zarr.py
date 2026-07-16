import pytest

zarr = pytest.importorskip("zarr")

from iterable.datatypes.zarr import ZarrIterable  # noqa: E402


def test_zarr_round_trip_and_bounded_bulk(tmp_path):
    path = tmp_path / "values.zarr"
    with ZarrIterable(str(path), mode="w", chunks=2, array="value") as output:
        output.write_bulk([{"value": 1}, {"value": 2}, {"value": 3}])

    with ZarrIterable(str(path), array="value") as source:
        assert source.read() == {"value": 1}
        assert source.read_bulk(2) == [{"value": 2}, {"value": 3}]
