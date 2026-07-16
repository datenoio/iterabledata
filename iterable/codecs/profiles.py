"""Portable compression performance profiles."""

from __future__ import annotations

from typing import Any

PROFILES = ("fast", "balanced", "max")

# Values are intentionally conservative, portable library settings rather than
# backend-specific tuning flags.
PROFILE_LEVELS: dict[str, dict[str, int]] = {
    "gzip": {"fast": 1, "balanced": 6, "max": 9},
    "bz2": {"fast": 1, "balanced": 5, "max": 9},
    "zstd": {"fast": 1, "balanced": 3, "max": 19},
    "lz4": {"fast": 0, "balanced": 9, "max": 16},
    "brotli": {"fast": 1, "balanced": 5, "max": 11},
    "xz": {"fast": 0, "balanced": 6, "max": 9},
    "lzo": {"fast": 1, "balanced": 6, "max": 9},
}


def resolve_profile(
    codec_id: str,
    *,
    profile: str | None,
    explicit_level: int | None,
    default_level: int,
) -> tuple[str, int]:
    """Resolve profile and level; an explicit level always wins."""
    effective_profile = profile or "balanced"
    if effective_profile not in PROFILES:
        raise ValueError(f"Unsupported compression profile {effective_profile!r}; choose one of {', '.join(PROFILES)}")
    levels = PROFILE_LEVELS.get(codec_id)
    if explicit_level is not None:
        return effective_profile, explicit_level
    if levels is None:
        return effective_profile, default_level
    return effective_profile, levels[effective_profile]


def profile_options(codec_id: str, profile: str, level: int) -> dict[str, Any]:
    """Return debug-safe effective codec settings."""
    return {"codec": codec_id, "profile": profile, "compression_level": level}
