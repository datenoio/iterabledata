"""Genomic Variant Call Format (VCF/BCF) reader backed by pysam.

This is distinct from the vCard ``vcf`` format (``iterable/datatypes/vcf.py``).
Genomic VCF files declare ``##fileformat=VCF`` in their header and describe
sequence variants; content detection disambiguates the two extensions.

Each record is one variant with the standard columns (CHROM, POS, ID, REF,
ALT, QUAL, FILTER), the parsed INFO dictionary, and per-sample FORMAT fields.
Reading streams variant by variant.
"""

from __future__ import annotations

import typing
from typing import Any

try:
    import pysam

    HAS_PYSAM = True
except ImportError:
    pysam = None  # type: ignore[assignment]
    HAS_PYSAM = False

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


def _to_plain(value: Any) -> Any:
    """Convert pysam tuple/array values into JSON-friendly Python types."""
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value


def _variant_to_dict(record: Any) -> Row:
    """Convert a pysam ``VariantRecord`` into a flat dict."""
    info = {key: _to_plain(record.info[key]) for key in record.info.keys()}

    samples: dict[str, dict[str, Any]] = {}
    for name, sample in record.samples.items():
        samples[name] = {key: _to_plain(sample[key]) for key in sample.keys()}

    return {
        "CHROM": record.chrom,
        # pysam exposes 0-based `start`; `pos` is the 1-based VCF POS.
        "POS": record.pos,
        "ID": record.id,
        "REF": record.ref,
        "ALT": list(record.alts) if record.alts else [],
        "QUAL": record.qual,
        "FILTER": list(record.filter.keys()),
        "INFO": info,
        "SAMPLES": samples,
    }


class GenomicVCFIterable(BaseFileIterable):
    """Genomic VCF/BCF reader: yields one dict per variant.

    Memory behavior: variants are read incrementally from the underlying
    ``pysam.VariantFile``; the file is never fully materialized.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYSAM:
            raise ImportError(
                "Genomic VCF/BCF support requires 'pysam'. Install with: pip install iterabledata[bio]"
            ) from None
        if filename is None:
            raise ValueError("Genomic VCF format requires a filename (stream not supported)")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self._vfile = None
        self._iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reopen the variant file and rewind."""
        super().reset()
        self.pos = 0
        if self.mode == "r" and self.filename is not None:
            # pysam auto-detects VCF (text/bgzf) vs BCF (binary) from content.
            self._vfile = pysam.VariantFile(self.filename)
            self._iterator = iter(self._vfile)
        else:
            self._iterator = iter([])

    @staticmethod
    def id() -> str:
        return "genomic_vcf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Variants are read incrementally from the pysam variant file."""
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single variant record."""
        try:
            record = next(self._iterator)
            self.pos += 1
            return _variant_to_dict(record)
        except (StopIteration, EOFError):
            raise StopIteration from None

    def close(self) -> None:
        """Close the variant file."""
        if self._vfile is not None:
            try:
                self._vfile.close()
            except Exception:
                pass
            self._vfile = None
        super().close()
