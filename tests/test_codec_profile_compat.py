"""Codec profile precedence, ratio thresholds, and cross-profile round trips.

Deterministic (size-based) regression thresholds live here so they run in
the default suite; timing-based thresholds live in
``tests/test_codec_benchmarks.py`` (benchmark marker).

Covers:
- generated fixture sanity (deterministic, compressible vs low-compressibility)
- explicit compression level overriding the profile (precedence spec)
- profile -> level mapping matching ``PROFILE_LEVELS``
- ratio ordering and floors on compressible data, near-1 ratio on random data
- cross-profile/explicit-level round-trip matrix for every primary codec
"""

from __future__ import annotations

import zlib

import pytest
from codec_perf_fixtures import (
    CODEC_SPECS,
    SMALL,
    compressible_payload,
    fixture_payload,
    random_payload,
    read_payload,
    write_payload,
)

from iterable.codecs import PROFILE_LEVELS, PROFILES
from iterable.helpers.detect import open_iterable

# Explicit levels chosen to differ from every profile mapping for the codec,
# so precedence is observable in the effective settings.
EXPLICIT_LEVELS = {"gzip": 7, "bz2": 7, "xz": 7, "zstd": 12, "lz4": 12, "brotli": 9}

# zstd level 3 can produce slightly larger output than level 1 on highly
# repetitive data (observed with zstandard 0.25), so the balanced<=fast half
# of the ordering is not asserted for zstd; the max-profile bounds still are.
_BALANCED_BEATS_FAST = {"gzip", "bz2", "xz", "lz4", "brotli"}

# Deterministic ratio thresholds (compressible fixture).
MIN_COMPRESSIBLE_RATIO = 3.0
ORDERING_SLACK = 1.02

# Random data must stay near 1:1 (no incompressible-data blowup).
RANDOM_RATIO_LOW = 0.95
RANDOM_RATIO_HIGH = 1.05


def _spec_params():
    params = []
    for spec in CODEC_SPECS:
        marks = [] if spec.available else [pytest.mark.skip(reason=f"{spec.class_name} optional extra not installed")]
        params.append(pytest.param(spec, id=spec.name, marks=marks))
    return params


class TestGeneratedFixtures:
    """The generated fixtures must stay deterministic and fit for purpose."""

    def test_deterministic(self):
        assert compressible_payload(SMALL) == compressible_payload(SMALL)
        assert random_payload(SMALL) == random_payload(SMALL)

    def test_sizes(self):
        assert len(compressible_payload(SMALL)) == SMALL
        assert len(random_payload(SMALL)) == SMALL

    def test_compressible_fixture_compresses_well(self):
        data = compressible_payload(SMALL)
        assert len(data) / len(zlib.compress(data, 6)) >= 8

    def test_random_fixture_is_low_compressibility(self):
        data = random_payload(SMALL)
        ratio = len(zlib.compress(data, 6)) / len(data)
        assert 0.98 <= ratio <= 1.02

    def test_unknown_kind_is_actionable(self):
        with pytest.raises(ValueError, match="compressible"):
            fixture_payload("bogus", SMALL)


@pytest.mark.parametrize("spec", _spec_params())
class TestProfileResolution:
    """Profile -> level mapping and explicit-level precedence."""

    def test_profile_maps_to_documented_level(self, tmp_path, spec):
        for profile in PROFILES:
            codec = spec.codec_class(str(tmp_path / f"p.{spec.extension}"), mode="w", options={"profile": profile})
            assert codec.profile == profile
            assert codec.compression_level == PROFILE_LEVELS[spec.name][profile]
            assert codec.effective_settings == {
                "codec": spec.name,
                "profile": profile,
                "compression_level": PROFILE_LEVELS[spec.name][profile],
            }

    def test_explicit_level_overrides_profile(self, tmp_path, spec):
        level = EXPLICIT_LEVELS[spec.name]
        codec = spec.codec_class(
            str(tmp_path / f"e.{spec.extension}"),
            mode="w",
            options={"profile": "fast", "compression_level": level},
        )
        assert codec.profile == "fast"
        assert codec.compression_level == level
        assert codec.effective_settings["compression_level"] == level

    def test_explicit_level_without_profile_wins_over_balanced_default(self, tmp_path, spec):
        level = EXPLICIT_LEVELS[spec.name]
        codec = spec.codec_class(str(tmp_path / f"d.{spec.extension}"), mode="w", options={"compression_level": level})
        assert codec.profile == "balanced"
        assert codec.compression_level == level

    def test_invalid_profile_is_actionable(self, tmp_path, spec):
        with pytest.raises(ValueError, match="fast.*balanced.*max"):
            spec.codec_class(str(tmp_path / f"bad.{spec.extension}"), mode="w", options={"profile": "turbo"})


@pytest.mark.parametrize("spec", _spec_params())
class TestRatioThresholds:
    """Deterministic compression-ratio ordering and floors (compressible data)."""

    def test_compressible_ratio_floor(self, tmp_path, spec):
        data = compressible_payload(SMALL)
        for profile in PROFILES:
            path = str(tmp_path / f"r.{spec.extension}")
            compressed = write_payload(spec.codec_class, path, data, {"profile": profile})
            ratio = len(data) / compressed
            assert ratio >= MIN_COMPRESSIBLE_RATIO, (
                f"{spec.name}/{profile}: ratio {ratio:.2f}x below floor {MIN_COMPRESSIBLE_RATIO}x"
            )

    def test_profile_ratio_ordering(self, tmp_path, spec):
        data = compressible_payload(SMALL)
        sizes = {
            profile: write_payload(spec.codec_class, str(tmp_path / f"o.{spec.extension}"), data, {"profile": profile})
            for profile in PROFILES
        }
        assert sizes["max"] <= sizes["fast"] * ORDERING_SLACK, f"{spec.name}: max worse than fast: {sizes}"
        assert sizes["max"] <= sizes["balanced"] * ORDERING_SLACK, f"{spec.name}: max worse than balanced: {sizes}"
        if spec.name in _BALANCED_BEATS_FAST:
            assert sizes["balanced"] <= sizes["fast"] * ORDERING_SLACK, (
                f"{spec.name}: balanced worse than fast: {sizes}"
            )

    def test_random_data_stays_near_identity(self, tmp_path, spec):
        data = random_payload(SMALL)
        compressed = write_payload(
            spec.codec_class, str(tmp_path / f"n.{spec.extension}"), data, {"profile": "balanced"}
        )
        ratio = compressed / len(data)
        assert RANDOM_RATIO_LOW <= ratio <= RANDOM_RATIO_HIGH, (
            f"{spec.name}: random data ratio {ratio:.4f} outside "
            f"[{RANDOM_RATIO_LOW}, {RANDOM_RATIO_HIGH}] (incompressible-data blowup)"
        )


@pytest.mark.parametrize("spec", _spec_params())
class TestCrossProfileRoundTrip:
    """Data written with one profile/level must read back under any other."""

    @pytest.mark.parametrize("write_profile", PROFILES)
    @pytest.mark.parametrize("read_profile", PROFILES)
    def test_cross_profile_round_trip(self, tmp_path, spec, write_profile, read_profile):
        data = compressible_payload(SMALL // 4)
        path = str(tmp_path / f"x.{spec.extension}")
        write_payload(spec.codec_class, path, data, {"profile": write_profile})
        assert read_payload(spec.codec_class, path, {"profile": read_profile}) == data

    def test_explicit_level_write_profile_read(self, tmp_path, spec):
        data = compressible_payload(SMALL // 4)
        path = str(tmp_path / f"ew.{spec.extension}")
        options = {"profile": "fast", "compression_level": EXPLICIT_LEVELS[spec.name]}
        write_payload(spec.codec_class, path, data, options)
        for read_profile in PROFILES:
            assert read_payload(spec.codec_class, path, {"profile": read_profile}) == data

    def test_profile_write_explicit_level_read(self, tmp_path, spec):
        data = compressible_payload(SMALL // 4)
        path = str(tmp_path / f"pw.{spec.extension}")
        for write_profile in PROFILES:
            write_payload(spec.codec_class, path, data, {"profile": write_profile})
            assert read_payload(spec.codec_class, path, {"compression_level": EXPLICIT_LEVELS[spec.name]}) == data

    def test_random_round_trip_all_profiles(self, tmp_path, spec):
        data = random_payload(SMALL // 4)
        path = str(tmp_path / f"rr.{spec.extension}")
        for profile in PROFILES:
            write_payload(spec.codec_class, path, data, {"profile": profile})
            assert read_payload(spec.codec_class, path) == data


class TestFactoryProfileWiring:
    """The high-level factory passes profile codecargs through end to end."""

    def test_open_iterable_round_trip_with_profile(self, tmp_path):
        rows = [{"id": i, "name": f"person{i % 100}"} for i in range(100)]
        path = str(tmp_path / "rows.jsonl.gz")
        with open_iterable(path, mode="w", codecargs={"profile": "fast"}) as dest:
            dest.write_bulk(rows)
        with open_iterable(path, mode="r") as source:
            assert list(source) == rows

    def test_open_iterable_explicit_level_overrides_profile(self, tmp_path):
        path = str(tmp_path / "rows.jsonl.gz")
        dest = open_iterable(path, mode="w", codecargs={"profile": "fast", "compression_level": 9})
        try:
            assert dest.codec.profile == "fast"
            assert dest.codec.compression_level == 9
            dest.write_bulk([{"id": 1}])
        finally:
            dest.close()
        with open_iterable(path, mode="r") as source:
            assert list(source) == [{"id": 1}]
