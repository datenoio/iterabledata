"""Generated fixtures and shared helpers for codec performance/profile tests.

Fixtures are generated deterministically at test time (never committed as
binary blobs):

- ``compressible_payload``: repetitive JSON-lines-like text with a small
  vocabulary, highly compressible by every primary codec.
- ``random_payload``: seeded pseudo-random bytes, effectively
  incompressible, used as the low-compressibility counterpart.

Two representative sizes are provided (``SMALL`` and ``MEDIUM``); benchmark
tests use ``MEDIUM`` while correctness/compat tests use ``SMALL`` or smaller
explicit sizes to keep the default suite fast.
"""

from __future__ import annotations

import random
import zlib
from typing import Any

import iterable.codecs as _codecs

SEED = 20240501

# Representative fixture sizes.
SMALL = 256 * 1024
MEDIUM = 1024 * 1024

# Read/write chunk size used by the streaming helpers.
CHUNK_SIZE = 64 * 1024

# Small vocabulary keeps entropy low so the "compressible" fixture compresses
# well (typically >10x) with every primary codec at every profile.
_NAMES = ("alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi")
_CITIES = ("berlin", "paris", "tokyo", "nairobi", "oslo", "quito")
_MESSAGE = "the quick brown fox jumps over the lazy dog; "


def compressible_payload(size: int) -> bytes:
    """Return ``size`` bytes of highly compressible JSON-lines-like text."""
    lines = []
    total = 0
    n = 0
    while total < size:
        line = (
            f'{{"id": {n}, "name": "{_NAMES[n % len(_NAMES)]}", '
            f'"city": "{_CITIES[n % len(_CITIES)]}", "score": {n % 97}, '
            f'"active": true, "message": "{_MESSAGE * 3}"}}'
        )
        lines.append(line)
        total += len(line) + 1
        n += 1
    data = ("\n".join(lines) + "\n").encode("utf-8")
    return data[:size]


def random_payload(size: int) -> bytes:
    """Return ``size`` bytes of seeded low-compressibility (random) data."""
    return random.Random(SEED).randbytes(size)


def fixture_payload(kind: str, size: int) -> bytes:
    """Dispatch helper: ``kind`` is ``"compressible"`` or ``"random"``."""
    if kind == "compressible":
        return compressible_payload(size)
    if kind == "random":
        return random_payload(size)
    raise ValueError(f"unknown fixture kind {kind!r}; expected 'compressible' or 'random'")


class CodecSpec:
    """Metadata for one primary codec under test."""

    def __init__(self, name: str, class_name: str, extension: str, version: str):
        self.name = name
        self.class_name = class_name
        self.extension = extension
        self.version = version
        self.codec_class = getattr(_codecs, class_name, None)

    @property
    def available(self) -> bool:
        return self.codec_class is not None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"CodecSpec({self.name}, available={self.available})"


def _zlib_version() -> str:
    return f"zlib {zlib.ZLIB_RUNTIME_VERSION}"


def _module_version(module_name: str, attr: str = "__version__") -> str:
    try:
        module = __import__(module_name)
        return f"{module_name} {getattr(module, attr, 'unknown')}"
    except Exception:  # pragma: no cover - defensive; backend missing
        return f"{module_name} unavailable"


# Primary codecs covered by the profile benchmarks. LZO/Snappy are
# fixed-performance codecs and py7zr is container-oriented, so they are
# intentionally out of scope here (documented in the profile matrix).
def codec_specs() -> list[CodecSpec]:
    return [
        CodecSpec("gzip", "GZIPCodec", "gz", _zlib_version()),
        CodecSpec("bz2", "BZIP2Codec", "bz2", "stdlib bz2"),
        CodecSpec("xz", "LZMACodec", "xz", "stdlib lzma"),
        CodecSpec("zstd", "ZSTDCodec", "zst", _module_version("zstandard")),
        CodecSpec("lz4", "LZ4Codec", "lz4", _module_version("lz4")),
        CodecSpec("brotli", "BrotliCodec", "br", _module_version("brotli")),
    ]


CODEC_SPECS = codec_specs()


def write_payload(codec_class: Any, path: str, payload: bytes, options: dict | None = None) -> int:
    """Write ``payload`` through ``codec_class`` in ``CHUNK_SIZE`` chunks.

    Returns the compressed file size in bytes.
    """
    import os

    codec = codec_class(path, mode="w", options=options or {})
    fileobj = codec.open()
    try:
        for offset in range(0, len(payload), CHUNK_SIZE):
            fileobj.write(payload[offset : offset + CHUNK_SIZE])
    finally:
        codec.close()
    return os.path.getsize(path)


def read_payload(codec_class: Any, path: str, options: dict | None = None) -> bytes:
    """Read a full payload back through ``codec_class`` in chunks."""
    chunks = []
    codec = codec_class(path, mode="r", options=options or {})
    fileobj = codec.open()
    try:
        while True:
            chunk = fileobj.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        codec.close()
    return b"".join(chunks)
