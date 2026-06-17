"""AI-assisted declarative transform suggestions."""

from __future__ import annotations

import collections.abc
import json
import re
from typing import Any

from ..ops import schema
from ..types import Row
from .context import redact_for_llm, sample_for_llm
from .models import validate_transform_spec
from .prompts import load_prompt
from .providers import get_provider


def suggest_transform(
    iterable: collections.abc.Iterable[Row] | str,
    goal: str,
    *,
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    send_raw_samples: bool = False,
    sample_size: int = 5,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Suggest a declarative transform spec for a dataset and goal.

    Returns JSON with whitelisted operations only; does not apply transforms.
    """
    schema_info: dict[str, Any] = {}
    if isinstance(iterable, str):
        try:
            schema_info = schema.infer(iterable, detect_constraints=False)
        except Exception:
            schema_info = {}

    samples = sample_for_llm(iterable, max_rows=sample_size, strategy="head")
    if not send_raw_samples:
        samples = redact_for_llm(samples)

    prompt = load_prompt(
        "suggest_transform",
        goal=goal,
        schema=json.dumps(schema_info, default=str)[:3000],
        samples=json.dumps(samples, default=str)[:2000],
    )
    llm = get_provider(provider, api_key=api_key, base_url=base_url)
    raw = llm.generate(prompt=prompt, model=model, temperature=0.2, **kwargs)
    spec_dict = _extract_json_object(raw)
    validate_transform_spec(spec_dict)
    return spec_dict


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain valid JSON transform spec")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Transform spec must be a JSON object")
    return parsed
