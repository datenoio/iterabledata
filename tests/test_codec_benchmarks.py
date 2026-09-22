"""Codec performance profile benchmarks.

Benchmarks the primary codecs (gzip, bzip2, xz, Zstandard, LZ4, Brotli)
across the ``fast``/``balanced``/``max`` profiles on both compressible and
low-compressibility (random) fixtures:

- write/read throughput (MB/s, best of 3 rounds)
- compression ratio (compressed vs uncompressed bytes)
- peak memory (tracemalloc peak per run)
- reset/reopen cost (normalized by a pure-Python calibration workload)

Run with: pytest tests/test_codec_benchmarks.py -m benchmark --no-cov -s

Regression thresholds (deliberately tolerant to absorb platform noise):
- fast-profile write throughput >= 0.9x max-profile write throughput
  (compressible fixture; margins are normally 1.4x-50x, so this only fails
  on a genuine profile-mapping inversion)
- normalized reset cost <= 0.25 of the calibration workload (reset is
  normally ~0.001; a failure means reset/reopen started rebuffering data)
- peak memory <= 64 MiB for a 1 MiB payload (catches accidental
  full-buffer-N regressions in Python-side handling); xz has documented
  per-direction overrides for liblzma's preset-9 encoder state (~700 MiB)
  and 64 MiB decoder dictionary

Absolute numbers vary by platform and backend build, so full results are
advisory: they are recorded per run and written to
``$CODEC_BENCH_OUT`` (or ``<tmpdir>/codec_benchmark_results.json``), and
pytest-benchmark's own ``--benchmark-json`` can be used alongside.
"""

from __future__ import annotations

import json
import os
import platform
import tempfile
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed (pip install pytest-benchmark)")

from codec_perf_fixtures import (  # noqa: E402
    CHUNK_SIZE,
    CODEC_SPECS,
    MEDIUM,
    SMALL,
    fixture_payload,
    read_payload,
    write_payload,
)

from iterable.codecs import PROFILES  # noqa: E402

# Excluded from the default run via addopts; run with: pytest -m benchmark
pytestmark = pytest.mark.benchmark

KINDS = ("compressible", "random")

# Tolerant regression thresholds (see module docstring).
FAST_VS_MAX_WRITE_FLOOR = 0.9
RESET_NORMALIZED_LIMIT = 0.25
PEAK_MEMORY_LIMIT_BYTES = 64 * 1024 * 1024

# Per-codec peak-memory overrides for backends with documented large internal
# allocations: liblzma (xz) preset 9 allocates ~700 MiB of encoder state for
# compression (see xz(1) "Memory usage") and a 64 MiB dictionary plus overhead
# for decompression. The limits below still catch genuine regressions (e.g.
# unbounded Python-side buffering on top of the documented encoder state).
PEAK_MEMORY_LIMIT_OVERRIDES = {
    "xz": {"write": 1024 * 1024 * 1024, "read": 128 * 1024 * 1024},
}


def _peak_limit(codec_name: str, direction: str) -> int:
    return PEAK_MEMORY_LIMIT_OVERRIDES.get(codec_name, {}).get(direction, PEAK_MEMORY_LIMIT_BYTES)


# Advisory result records, flushed to JSON at session end.
_RESULTS: list[dict[str, Any]] = []


def _record(**fields: Any) -> None:
    _RESULTS.append(fields)


@pytest.fixture(scope="session", autouse=True)
def _flush_results():
    """Persist advisory benchmark results as JSON at the end of the session."""
    yield
    if not _RESULTS:
        return
    out = os.environ.get("CODEC_BENCH_OUT") or str(Path(tempfile.gettempdir()) / "codec_benchmark_results.json")
    doc = {
        "_meta": {
            "description": "Advisory codec profile benchmark results (absolute numbers are platform-dependent)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "payload_bytes": MEDIUM,
        },
        "results": _RESULTS,
    }
    with open(out, "w") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"\ncodec benchmark results written to {out}")


def _spec_params():
    params = []
    for spec in CODEC_SPECS:
        marks = [] if spec.available else [pytest.mark.skip(reason=f"{spec.class_name} optional extra not installed")]
        params.append(pytest.param(spec, id=spec.name, marks=marks))
    return params


_PAYLOADS: dict[tuple[str, int], bytes] = {}


def _payload(kind: str, size: int = MEDIUM) -> bytes:
    key = (kind, size)
    if key not in _PAYLOADS:
        _PAYLOADS[key] = fixture_payload(kind, size)
    return _PAYLOADS[key]


def _best_of(func, runs: int = 3, warmup: int = 1) -> float:
    """Best wall time of ``runs`` executions after ``warmup`` runs."""
    for _ in range(warmup):
        func()
    best = float("inf")
    for _ in range(runs):
        start = time.perf_counter()
        func()
        best = min(best, time.perf_counter() - start)
    return best


def _calibration_workload() -> int:
    """Fixed pure-Python workload used to normalize reset timings across machines."""
    total = 0
    for i in range(1_500_000):
        total += i * i
    return total


@pytest.fixture(scope="module")
def calibration_seconds() -> float:
    return _best_of(_calibration_workload, runs=3, warmup=1)


def _peak_memory(callable_) -> int:
    """Run once under tracemalloc and return the peak traced bytes."""
    tracemalloc.start()
    try:
        callable_()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("spec", _spec_params())
class TestCodecThroughput:
    """Write/read throughput and ratio per codec x profile x fixture type."""

    def test_write_throughput(self, benchmark, tmp_path, spec, profile, kind):
        data = _payload(kind)
        path = str(tmp_path / f"out.{spec.extension}")
        benchmark.pedantic(
            lambda: write_payload(spec.codec_class, path, data, {"profile": profile}),
            iterations=1,
            rounds=3,
            warmup_rounds=1,
        )
        seconds = benchmark.stats.stats.min
        compressed = os.path.getsize(path)
        throughput = len(data) / seconds / 1e6
        ratio = compressed / len(data)
        _record(
            test="write_throughput",
            codec=spec.name,
            backend_version=spec.version,
            profile=profile,
            fixture=kind,
            input_bytes=len(data),
            output_bytes=compressed,
            ratio=round(ratio, 4),
            write_seconds=round(seconds, 6),
            write_mb_s=round(throughput, 2),
        )
        print(f"\n{spec.name}/{profile}/{kind}: write {throughput:.1f} MB/s, ratio {ratio:.4f}")
        assert compressed > 0

    def test_read_throughput(self, benchmark, tmp_path, spec, profile, kind):
        data = _payload(kind)
        path = str(tmp_path / f"out.{spec.extension}")
        compressed = write_payload(spec.codec_class, path, data, {"profile": profile})
        benchmark.pedantic(
            lambda: read_payload(spec.codec_class, path),
            iterations=1,
            rounds=3,
            warmup_rounds=1,
        )
        seconds = benchmark.stats.stats.min
        throughput = len(data) / seconds / 1e6
        _record(
            test="read_throughput",
            codec=spec.name,
            backend_version=spec.version,
            profile=profile,
            fixture=kind,
            input_bytes=len(data),
            output_bytes=compressed,
            read_seconds=round(seconds, 6),
            read_mb_s=round(throughput, 2),
        )
        print(f"\n{spec.name}/{profile}/{kind}: read {throughput:.1f} MB/s")
        assert read_payload(spec.codec_class, path) == data


@pytest.mark.parametrize("spec", _spec_params())
class TestCodecPairedThresholds:
    """Paired fast-vs-max comparisons on the compressible fixture.

    Acceptance considers throughput and ratio together: the fast profile
    must not be slower to write than max (elapsed time alone is not
    sufficient), and the max profile must not compress worse than fast.
    """

    def test_fast_write_not_slower_than_max(self, tmp_path, spec):
        data = _payload("compressible")
        path = str(tmp_path / f"out.{spec.extension}")
        fast_seconds = _best_of(lambda: write_payload(spec.codec_class, path, data, {"profile": "fast"}))
        max_seconds = _best_of(lambda: write_payload(spec.codec_class, path, data, {"profile": "max"}))
        fast_tput = len(data) / fast_seconds / 1e6
        max_tput = len(data) / max_seconds / 1e6
        _record(
            test="paired_fast_vs_max_write",
            codec=spec.name,
            backend_version=spec.version,
            fixture="compressible",
            input_bytes=len(data),
            fast_write_mb_s=round(fast_tput, 2),
            max_write_mb_s=round(max_tput, 2),
        )
        print(f"\n{spec.name}: fast {fast_tput:.1f} MB/s vs max {max_tput:.1f} MB/s")
        assert fast_tput >= max_tput * FAST_VS_MAX_WRITE_FLOOR, (
            f"{spec.name}: fast profile write ({fast_tput:.1f} MB/s) slower than "
            f"max profile ({max_tput:.1f} MB/s); profile mapping looks inverted"
        )

    def test_max_ratio_not_worse_than_fast(self, tmp_path, spec):
        data = _payload("compressible")
        fast_path = str(tmp_path / f"fast.{spec.extension}")
        max_path = str(tmp_path / f"max.{spec.extension}")
        fast_size = write_payload(spec.codec_class, fast_path, data, {"profile": "fast"})
        max_size = write_payload(spec.codec_class, max_path, data, {"profile": "max"})
        _record(
            test="paired_fast_vs_max_ratio",
            codec=spec.name,
            backend_version=spec.version,
            fixture="compressible",
            input_bytes=len(data),
            fast_output_bytes=fast_size,
            max_output_bytes=max_size,
        )
        print(f"\n{spec.name}: fast {fast_size} B vs max {max_size} B compressed")
        # 2% slack absorbs header/block-boundary jitter across backends.
        assert max_size <= fast_size * 1.02, (
            f"{spec.name}: max profile output ({max_size} B) larger than fast profile ({fast_size} B); "
            "profile mapping looks inverted"
        )


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("spec", _spec_params())
class TestCodecPeakMemory:
    """Peak traced memory for streaming write/read of a 1 MiB payload."""

    def test_peak_memory_write(self, benchmark, tmp_path, spec, profile, kind):
        data = _payload(kind)
        path = str(tmp_path / f"out.{spec.extension}")
        peak = benchmark.pedantic(
            lambda: _peak_memory(lambda: write_payload(spec.codec_class, path, data, {"profile": profile})),
            rounds=1,
            iterations=1,
        )
        _record(
            test="peak_memory_write",
            codec=spec.name,
            backend_version=spec.version,
            profile=profile,
            fixture=kind,
            input_bytes=len(data),
            peak_memory_bytes=peak,
        )
        print(f"\n{spec.name}/{profile}/{kind}: write peak memory {peak / 1e6:.2f} MB")
        assert 0 < peak <= _peak_limit(spec.name, "write")

    def test_peak_memory_read(self, benchmark, tmp_path, spec, profile, kind):
        data = _payload(kind)
        path = str(tmp_path / f"out.{spec.extension}")
        write_payload(spec.codec_class, path, data, {"profile": profile})
        peak = benchmark.pedantic(
            lambda: _peak_memory(lambda: read_payload(spec.codec_class, path)),
            rounds=1,
            iterations=1,
        )
        _record(
            test="peak_memory_read",
            codec=spec.name,
            backend_version=spec.version,
            profile=profile,
            fixture=kind,
            input_bytes=len(data),
            peak_memory_bytes=peak,
        )
        print(f"\n{spec.name}/{profile}/{kind}: read peak memory {peak / 1e6:.2f} MB")
        assert 0 < peak <= _peak_limit(spec.name, "read")


@pytest.mark.parametrize("spec", _spec_params())
class TestCodecResetCost:
    """Reset/reopen cost, normalized by a pure-Python calibration workload."""

    def test_reset_cost_normalized(self, benchmark, tmp_path, spec, calibration_seconds):
        data = _payload("compressible", SMALL)
        path = str(tmp_path / f"out.{spec.extension}")
        write_payload(spec.codec_class, path, data, {"profile": "balanced"})

        codec = spec.codec_class(path, mode="r")
        codec.open()
        try:
            codec.fileobj().read(CHUNK_SIZE)  # position mid-stream before resetting

            benchmark.pedantic(codec.reset, iterations=1, rounds=5, warmup_rounds=1)
            reset_seconds = benchmark.stats.stats.min
            normalized = reset_seconds / calibration_seconds
            _record(
                test="reset_cost",
                codec=spec.name,
                backend_version=spec.version,
                fixture="compressible",
                input_bytes=len(data),
                reset_seconds=round(reset_seconds, 6),
                reset_normalized=round(normalized, 5),
                calibration_seconds=round(calibration_seconds, 6),
            )
            print(f"\n{spec.name}: reset {reset_seconds * 1e6:.0f} us (normalized {normalized:.5f})")
            assert normalized <= RESET_NORMALIZED_LIMIT, (
                f"{spec.name}: reset cost {normalized:.4f} of calibration workload exceeds "
                f"{RESET_NORMALIZED_LIMIT}; reset/reopen may be rebuffering data"
            )

            # Reset must return the stream to a correct full read.
            codec.reset()
            chunks = []
            while True:
                chunk = codec.fileobj().read(CHUNK_SIZE)
                if not chunk:
                    break
                chunks.append(chunk)
            assert b"".join(chunks) == data
        finally:
            codec.close()
