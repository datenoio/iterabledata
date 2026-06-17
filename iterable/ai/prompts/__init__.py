"""Versioned prompt templates for AI operations."""

from __future__ import annotations

from importlib import resources


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template from package resources and format placeholders."""
    path = resources.files(__package__).joinpath(f"{name}.txt")
    template = path.read_text(encoding="utf-8")
    if kwargs:
        return template.format(**kwargs)
    return template
