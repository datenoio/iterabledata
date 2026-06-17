"""Content-based format detection (magic bytes and text heuristics)."""

from __future__ import annotations

from typing import IO, BinaryIO

from .format_registry import match_magic_prefix


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

        try:
            text = peek.decode("utf-8", errors="ignore")
            text_stripped = text.strip()

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
