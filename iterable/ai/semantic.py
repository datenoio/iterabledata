"""
Semantic type detection and PII identification using Metacrafter.

Provides integration with Metacrafter CLI tool for detecting semantic types
and personally identifiable information (PII) in datasets.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from ..types import Row


def _run_metacrafter_scan(filename: str) -> list[dict[str, Any]] | None:
    """
    Run Metacrafter scan on a file.

    Args:
        filename: Path to file to scan

    Returns:
        List of field entries with semantic types, or None if Metacrafter unavailable
    """
    if shutil.which("metacrafter") is None:
        return None

    commands = [
        ["metacrafter", "scan-file", "--format", "json", filename],
        ["metacrafter", "scan-file", filename, "--format", "json"],
    ]

    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
            if result.returncode != 0:
                continue
            output = result.stdout.strip()
            if not output:
                continue
            data = json.loads(output)
            if isinstance(data, dict):
                if "fields" in data:
                    return data["fields"]
                if "data" in data:
                    return data["data"]
            if isinstance(data, list):
                return data
        except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired):
            continue

    return None


def _parse_metacrafter_matches(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Parse semantic type matches from Metacrafter entry.

    Args:
        entry: Metacrafter entry dictionary

    Returns:
        List of semantic type dictionaries with type, url, and confidence
    """
    matches = entry.get("matches") or entry.get("datatypes") or entry.get("types")
    if matches is None:
        matches = []
    if isinstance(matches, str):
        matches = [m.strip() for m in matches.split(",") if m.strip()]

    results = []
    for match in matches:
        if isinstance(match, dict):
            match_type = match.get("type") or match.get("name") or match.get("label")
            confidence = match.get("confidence")
        else:
            match_type = str(match).split()[0]
            confidence = None
            match_parts = str(match).split()
            if len(match_parts) > 1:
                try:
                    confidence = float(match_parts[-1])
                except ValueError:
                    confidence = None

        if match_type:
            results.append(
                {
                    "type": match_type,
                    "url": entry.get("datatype_url"),
                    "confidence": confidence,
                }
            )

    return results


def detect_semantic_types(filename: str, field_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    """
    Detect semantic types for fields using Metacrafter.

    Args:
        filename: Path to file to analyze
        field_names: List of field names

    Returns:
        Dictionary mapping field names to lists of semantic type dictionaries
    """
    entries = _run_metacrafter_scan(filename)
    if not entries:
        return {name: [] for name in field_names}

    entry_map = {}
    for entry in entries:
        key = entry.get("key") or entry.get("name")
        if key:
            entry_map[key] = entry

    result = {}
    for name in field_names:
        entry = entry_map.get(name)
        if entry:
            result[name] = _parse_metacrafter_matches(entry)
        else:
            result[name] = []

    return result


def detect_pii(filename: str, field_names: list[str]) -> list[dict[str, Any]]:
    """
    Detect PII fields using Metacrafter.

    Args:
        filename: Path to file to analyze
        field_names: List of field names

    Returns:
        List of PII field dictionaries with field, type, and confidence
    """
    entries = _run_metacrafter_scan(filename)
    if not entries:
        return []

    entry_map = {}
    for entry in entries:
        key = entry.get("key") or entry.get("name")
        if key:
            entry_map[key] = entry

    pii_fields = []
    for name in field_names:
        entry = entry_map.get(name)
        if not entry:
            continue

        # Check tags for PII
        tags = entry.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        is_pii = any("pii" in str(tag).lower() for tag in tags)

        # Check semantic types for PII
        matches = _parse_metacrafter_matches(entry)
        is_pii = is_pii or any("pii" in str(m.get("type", "")).lower() for m in matches)

        if is_pii:
            top_match = matches[0] if matches else {}
            pii_fields.append(
                {
                    "field": name,
                    "type": top_match.get("type"),
                    "confidence": top_match.get("confidence"),
                }
            )

    return pii_fields


def mask_pii_samples(samples: list[Row], field_names: list[str], pii_fields: list[dict[str, Any]]) -> list[Row]:
    """
    Mask PII values in sample data.

    Args:
        samples: Sample data rows
        field_names: List of field names
        pii_fields: List of PII field dictionaries

    Returns:
        Samples with PII values masked (replaced with "***")
    """
    if not pii_fields:
        return samples

    pii_set = {item.get("field") for item in pii_fields if item.get("field")}
    masked = []

    for sample in samples:
        if isinstance(sample, dict):
            new_sample = dict(sample)
            for key in pii_set:
                if key in new_sample:
                    new_sample[key] = "***"
            masked.append(new_sample)
        elif isinstance(sample, list):
            new_sample = list(sample)
            for idx, name in enumerate(field_names):
                if name in pii_set and idx < len(new_sample):
                    new_sample[idx] = "***"
            masked.append(new_sample)
        else:
            masked.append(sample)

    return masked
