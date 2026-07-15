"""Content-based format detection (magic bytes and text heuristics)."""

from __future__ import annotations

import json
from typing import IO, BinaryIO

from .format_registry import match_magic_prefix


def _detect_geojsonseq(text: str) -> tuple[str, float, str] | None:
    """Detect GeoJSON Text Sequences: JSON Feature objects, one per line."""
    lines = [line.lstrip("\x1e").strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    if not lines:
        return None
    # The last peeked line may be truncated; require at least one full line.
    candidates = lines[:-1] if len(lines) > 1 else lines
    matched = 0
    for line in candidates[:5]:
        if not line.startswith("{"):
            return None
        try:
            obj = json.loads(line)
        except (ValueError, json.JSONDecodeError):
            return None
        if not (isinstance(obj, dict) and obj.get("type") == "Feature"):
            return None
        matched += 1
    if matched == 0:
        return None
    confidence = min(0.90, 0.75 + matched * 0.03)
    return ("geojsonseq", confidence, "heuristic")


def _detect_vcf(text: str) -> tuple[str, float, str] | None:
    """Disambiguate the shared ``.vcf`` extension by content.

    Genomic Variant Call Format files declare ``##fileformat=VCF`` in the
    header; vCard files start with ``BEGIN:VCARD``.
    """
    stripped = text.lstrip("\ufeff \t\r\n")
    if stripped.startswith("##fileformat=VCF"):
        return ("genomic_vcf", 0.98, "magic_number")
    if stripped.upper().startswith("BEGIN:VCARD"):
        return ("vcf", 0.95, "heuristic")
    return None


def detect_file_type_from_content(
    fileobj: BinaryIO | IO[bytes],
    peek_size: int = 8192,
) -> tuple[str, float, str] | None:
    """Detect file type from content (magic numbers and heuristics).

    Args:
        fileobj: File-like object to read from
        peek_size: Number of bytes to read for detection

    Returns:
        Tuple of (format_id, confidence, method) if detected, None otherwise
        - format_id: Format identifier string
        - confidence: Confidence score (0.0-1.0), higher is more confident
        - method: Detection method ("magic_number" or "heuristic")
    """
    try:
        original_pos = fileobj.tell()
        peek_raw = fileobj.read(peek_size)
        if not isinstance(peek_raw, bytes):
            raise TypeError("detect_file_type_from_content requires a binary file object")
        peek = peek_raw
        fileobj.seek(original_pos)

        if len(peek) == 0:
            return None

        magic_result = match_magic_prefix(peek)
        if magic_result is not None:
            return magic_result

        # TAR (POSIX ustar): magic lives at offset 257, so it cannot be
        # matched by the prefix table above.
        if len(peek) >= 262 and peek[257:262] == b"ustar":
            return ("tar", 0.95, "magic_number")

        try:
            text = peek.decode("utf-8", errors="ignore")
            text_stripped = text.strip()

            # VCF disambiguation (genomic Variant Call Format vs vCard) must
            # run before generic heuristics; both share the .vcf extension.
            vcf_result = _detect_vcf(text)
            if vcf_result is not None:
                return vcf_result

            # GeoJSON Text Sequences (RFC 8142): one Feature object per line,
            # optionally prefixed with the record separator \x1e. Check before
            # generic JSON/JSONL heuristics so sequences are not misdetected.
            geojsonseq = _detect_geojsonseq(text)
            if geojsonseq is not None:
                return geojsonseq

            if text_stripped.startswith("{") or text_stripped.startswith("["):
                try:
                    import json

                    json.loads(text_stripped[:1000])
                    return ("json", 0.90, "heuristic")
                except (ValueError, json.JSONDecodeError):
                    first_line = text_stripped.split("\n")[0].strip()
                    if first_line.startswith("{") or first_line.startswith("["):
                        try:
                            json.loads(first_line)
                            return ("jsonl", 0.80, "heuristic")
                        except (ValueError, json.JSONDecodeError):
                            pass

            if any(d in text[:100] for d in (",", "\t", "|", ";")):
                lines = text.split("\n")[:5]
                if len(lines) >= 2:
                    delimiters = [",", "\t", "|", ";"]
                    for delim in delimiters:
                        if delim in lines[0] and delim in lines[1]:
                            counts_0 = lines[0].count(delim)
                            counts_1 = lines[1].count(delim)
                            if abs(counts_0 - counts_1) <= 2 and counts_0 > 0:
                                format_id = "csv" if delim == "," else "tsv" if delim == "\t" else "psv"
                                confidence = 0.85 if abs(counts_0 - counts_1) == 0 else 0.75
                                return (format_id, confidence, "heuristic")

            lines = text.split("\n")[:10]
            jsonl_count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    import json

                    json.loads(line)
                    jsonl_count += 1
                except (ValueError, json.JSONDecodeError):
                    break
            if jsonl_count >= 3:
                confidence = min(0.90, 0.70 + (jsonl_count * 0.05))
                return ("jsonl", confidence, "heuristic")

        except UnicodeDecodeError:
            pass

        return None
    except Exception:
        return None
