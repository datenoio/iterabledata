"""AI-assisted conversion planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..catalog import describe_format
from ..helpers.detect import detect_file_type
from ..helpers.format_registry import get_descriptor
from .prompts import load_prompt
from .providers import get_provider


def _format_id_from_detection(path: str) -> str | None:
    p = Path(path)
    if p.exists():
        try:
            result = detect_file_type(path)
        except ImportError:
            result = {}
        datatype = result.get("datatype")
        if datatype is not None:
            id_fn = getattr(datatype, "id", None)
            if callable(id_fn):
                try:
                    return str(id_fn())
                except Exception:
                    pass
    ext = p.suffix.lstrip(".").lower()
    if ext and get_descriptor(ext) is not None:
        return ext
    return None


def _codec_note(path: str) -> str | None:
    if not Path(path).exists():
        return None
    try:
        result = detect_file_type(path)
    except ImportError:
        return None
    codec = result.get("codec")
    if codec is None:
        return None
    id_fn = getattr(codec, "id", None)
    codec_id = id_fn() if callable(id_fn) else codec.__name__
    return f"Detected compression codec: {codec_id}"


def plan_conversion(
    source: str,
    target: str,
    *,
    use_llm: bool = False,
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Produce a declarative conversion plan between source and target paths.

    Uses catalog metadata by default; optional LLM reasoning when ``use_llm=True``.
    Does not perform the conversion.
    """
    source_id = _format_id_from_detection(source)
    target_id = _format_id_from_detection(target)

    source_meta: dict[str, Any] = {}
    target_meta: dict[str, Any] = {}
    if source_id:
        source_meta = describe_format(source_id, include_capabilities=True)
    if target_id:
        target_meta = describe_format(target_id, include_capabilities=True)

    warnings: list[str] = []
    if target_id and not target_meta.get("writable", True):
        warnings.append(f"Target format '{target_id}' is read-only; writing to {target!r} may fail.")

    if source_id and source_meta.get("extra"):
        warnings.append(f"Source format may require optional extra: pip install iterabledata[{source_meta['extra']}]")
    if target_id and target_meta.get("extra"):
        warnings.append(f"Target format may require optional extra: pip install iterabledata[{target_meta['extra']}]")

    codec_note = _codec_note(source)
    steps = [
        {"action": "detect", "detail": f"Source format: {source_id or 'unknown'}"},
        {"action": "detect", "detail": f"Target format: {target_id or 'unknown'}"},
        {
            "action": "open",
            "detail": "open_iterable(source, iterableargs=...)",
            "recommended_kwargs": source_meta.get("example_args") or {},
        },
        {"action": "convert", "detail": f"convert({source!r}, {target!r})"},
    ]

    plan: dict[str, Any] = {
        "source": {"path": source, "format": source_id, "metadata": source_meta},
        "target": {"path": target, "format": target_id, "metadata": target_meta},
        "steps": steps,
        "warnings": warnings,
        "recommended_open_iterable_kwargs": source_meta.get("example_args") or {},
        "codec_notes": [codec_note] if codec_note else [],
        "considerations": list(source_meta.get("limitations") or []) + list(target_meta.get("limitations") or []),
    }

    if use_llm:
        prompt = load_prompt(
            "plan_conversion",
            source_path=source,
            target_path=target,
            source_format=source_id or "unknown",
            target_format=target_id or "unknown",
            source_metadata=json.dumps(source_meta, default=str)[:4000],
            target_metadata=json.dumps(target_meta, default=str)[:4000],
            warnings=json.dumps(warnings),
        )
        llm = get_provider(provider, api_key=api_key, base_url=base_url)
        raw = llm.generate(prompt=prompt, model=model, temperature=0.2, **kwargs)
        try:
            llm_plan = json.loads(raw)
        except json.JSONDecodeError:
            import re

            match = re.search(r"\{.*\}", raw, re.DOTALL)
            llm_plan = json.loads(match.group(0)) if match else {}
        if isinstance(llm_plan, dict):
            if llm_plan.get("steps"):
                plan["steps"] = llm_plan["steps"]
            if llm_plan.get("considerations"):
                plan["considerations"] = llm_plan["considerations"]
            if llm_plan.get("recommended_kwargs"):
                plan["recommended_open_iterable_kwargs"] = llm_plan["recommended_kwargs"]
            plan["llm_notes"] = llm_plan

    return plan
