"""
Metadata extraction utilities for dataset documentation.

Provides functions for extracting structured metadata including keywords,
geographic coverage, temporal coverage, languages, and data themes.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..types import Row

# Geographic field hints for detection
GEO_FIELD_HINTS = {
    "country": {"country", "country_code", "countrycode", "nation"},
    "region": {"region", "state", "province", "county", "district", "city", "municipality"},
    "coordinates": {"lat", "latitude", "lon", "lng", "longitude", "x", "y"},
}

# Date/time field hints for detection
DATE_FIELD_HINTS = {"date", "time", "timestamp", "datetime", "year", "month", "day"}

# EU Data Theme keywords (simplified version - can be extended)
DATA_THEME_KEYWORDS = {
    "AGRI": {"agri", "agriculture", "farm", "crop", "soil", "livestock"},
    "ECON": {"economy", "economic", "finance", "trade", "gdp", "inflation"},
    "EDUC": {"education", "school", "student", "university", "training"},
    "ENVI": {"environment", "climate", "pollution", "emission", "biodiversity"},
    "ENER": {"energy", "power", "electric", "fuel", "gas", "oil"},
    "GOVE": {"government", "public", "administration", "policy", "budget"},
    "HEAL": {"health", "medical", "hospital", "disease", "patient"},
    "INTR": {"international", "foreign", "trade", "diplomacy"},
    "JUST": {"justice", "crime", "law", "court", "police"},
    "REGI": {"region", "regional", "urban", "rural", "territory"},
    "SOCI": {"social", "population", "demography", "welfare", "community"},
    "TECH": {"technology", "innovation", "digital", "software", "it"},
    "TRAN": {"transport", "traffic", "mobility", "road", "rail", "aviation"},
}

# EU Data Theme URIs (simplified - can be extended with full list)
DATA_THEME_URI_BY_LABEL = {
    "AGRI": "http://publications.europa.eu/resource/authority/data-theme/AGRI",
    "ECON": "http://publications.europa.eu/resource/authority/data-theme/ECON",
    "EDUC": "http://publications.europa.eu/resource/authority/data-theme/EDUC",
    "ENVI": "http://publications.europa.eu/resource/authority/data-theme/ENVI",
    "ENER": "http://publications.europa.eu/resource/authority/data-theme/ENER",
    "GOVE": "http://publications.europa.eu/resource/authority/data-theme/GOVE",
    "HEAL": "http://publications.europa.eu/resource/authority/data-theme/HEAL",
    "INTR": "http://publications.europa.eu/resource/authority/data-theme/INTR",
    "JUST": "http://publications.europa.eu/resource/authority/data-theme/JUST",
    "REGI": "http://publications.europa.eu/resource/authority/data-theme/REGI",
    "SOCI": "http://publications.europa.eu/resource/authority/data-theme/SOCI",
    "TECH": "http://publications.europa.eu/resource/authority/data-theme/TECH",
    "TRAN": "http://publications.europa.eu/resource/authority/data-theme/TRAN",
}


def _iter_sample_values(samples: list[Row], field_names: list[str]) -> Any:
    """Iterate over sample values for given field names."""
    for sample in samples:
        if isinstance(sample, dict):
            for name in field_names:
                yield name, sample.get(name)
        elif isinstance(sample, list):
            for idx, name in enumerate(field_names):
                if idx < len(sample):
                    yield name, sample[idx]
        else:
            for name in field_names:
                yield name, None


def extract_keywords(
    field_names: list[str],
    samples: list[Row] | None = None,
    max_keywords: int = 15,
) -> list[str]:
    """
    Extract keywords from field names and optionally sample data.

    Args:
        field_names: List of field names to extract keywords from
        samples: Optional sample data rows
        max_keywords: Maximum number of keywords to return

    Returns:
        List of keywords sorted by frequency
    """
    tokens = []
    for name in field_names:
        parts = re.split(r"[^A-Za-z0-9]+", name)
        tokens.extend([part.lower() for part in parts if len(part) > 2])

    # Extract from sample data if provided
    if samples:
        for _name, value in _iter_sample_values(samples, field_names):
            if isinstance(value, str) and len(value.strip()) > 2:
                parts = re.split(r"[^A-Za-z0-9]+", value)
                tokens.extend([part.lower() for part in parts if len(part) > 2])

    stopwords = {"and", "or", "the", "for", "with", "from", "data", "info", "id"}
    keywords = [token for token in tokens if token not in stopwords]

    if not keywords:
        return []

    counts = Counter(keywords)
    return [word for word, _ in counts.most_common(max_keywords)]


def extract_geographic_coverage(
    samples: list[Row],
    field_names: list[str],
) -> dict[str, Any]:
    """
    Extract geographic coverage information from samples.

    Args:
        samples: Sample data rows
        field_names: List of field names

    Returns:
        Dictionary with countries, regions, and coordinates_present flag
    """
    field_map = {name: name.lower() for name in field_names}
    coverage: dict[str, Any] = {
        "countries": [],
        "regions": [],
        "coordinates_present": False,
    }

    # Detect coordinate fields
    coord_fields = {
        name for name, lname in field_map.items() if any(hint in lname for hint in GEO_FIELD_HINTS["coordinates"])
    }
    if coord_fields:
        coverage["coordinates_present"] = True

    # Detect country and region fields
    country_fields = {
        name for name, lname in field_map.items() if any(hint in lname for hint in GEO_FIELD_HINTS["country"])
    }
    region_fields = {
        name for name, lname in field_map.items() if any(hint in lname for hint in GEO_FIELD_HINTS["region"])
    }

    countries = []
    regions = []
    for name, value in _iter_sample_values(samples, field_names):
        if value is None:
            continue
        if name in country_fields and isinstance(value, str):
            val = value.strip()
            if 2 <= len(val) <= 64:
                countries.append(val)
        if name in region_fields and isinstance(value, str):
            val = value.strip()
            if 2 <= len(val) <= 64:
                regions.append(val)

    if countries:
        coverage["countries"] = sorted(set(countries))[:10]
    if regions:
        coverage["regions"] = sorted(set(regions))[:10]

    return coverage


def extract_temporal_coverage(
    samples: list[Row],
    field_names: list[str],
) -> dict[str, Any] | None:
    """
    Extract temporal coverage information from samples.

    Args:
        samples: Sample data rows
        field_names: List of field names

    Returns:
        Dictionary with start, end, and granularity, or None if no temporal data found
    """
    candidate_fields = [name for name in field_names if any(hint in name.lower() for hint in DATE_FIELD_HINTS)]
    if not candidate_fields:
        return None

    values = []
    for name, value in _iter_sample_values(samples, field_names):
        if name not in candidate_fields:
            continue
        if value is None:
            continue
        values.append(value)

    if not values:
        return None

    try:
        import pandas as pd

        series = pd.to_datetime(values, errors="coerce")
        series = series.dropna()
        if series.empty:
            return None

        start = series.min()
        end = series.max()
        has_time = any(getattr(dt, "hour", 0) or getattr(dt, "minute", 0) or getattr(dt, "second", 0) for dt in series)
        granularity = "datetime" if has_time else "date"

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "granularity": granularity,
        }
    except ImportError:
        # pandas not available, skip temporal coverage
        return None
    except Exception:
        # Date parsing failed
        return None


def detect_languages(
    samples: list[Row],
    field_names: list[str],
) -> list[dict[str, Any]]:
    """
    Detect languages in text fields from samples.

    Args:
        samples: Sample data rows
        field_names: List of field names

    Returns:
        List of dictionaries with code and confidence for detected languages
    """
    try:
        from langdetect import detect
    except ImportError:
        # langdetect not available
        return []

    texts = []
    for _name, value in _iter_sample_values(samples, field_names):
        if isinstance(value, str) and len(value.strip()) >= 20:
            texts.append(value.strip())
        if len(texts) >= 50:
            break

    if not texts:
        return []

    counts = Counter()
    total = 0
    for text in texts:
        try:
            lang = detect(text)
            counts[lang] += 1
            total += 1
        except Exception:
            continue

    if not total:
        return []

    return [{"code": code, "confidence": round(count / total, 2)} for code, count in counts.most_common(3)]


def classify_data_theme(
    field_names: list[str],
    keywords: list[str],
) -> dict[str, str] | None:
    """
    Classify data theme based on field names and keywords.

    Args:
        field_names: List of field names
        keywords: List of extracted keywords

    Returns:
        Dictionary with label and uri, or None if no theme matches
    """
    tokens = set(keywords)
    for name in field_names:
        parts = re.split(r"[^A-Za-z0-9]+", name)
        tokens.update([part.lower() for part in parts if part])

    best_label = None
    best_score = 0
    for label, theme_keywords in DATA_THEME_KEYWORDS.items():
        score = len(tokens.intersection(theme_keywords))
        if score > best_score:
            best_score = score
            best_label = label

    if not best_label or best_score == 0:
        return None

    return {
        "label": best_label,
        "uri": DATA_THEME_URI_BY_LABEL.get(best_label),
    }
