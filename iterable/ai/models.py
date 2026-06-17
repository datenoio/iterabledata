"""Pydantic models for AI documentation JSON output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UsageInfo(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class DocumentationResult(BaseModel):
    """Validated shape for ``ai.doc.generate(format='json')`` responses."""

    model_config = ConfigDict(extra="allow")

    documentation: str
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    samples: list[dict[str, Any]] | None = None
    usage: UsageInfo | dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    statistics: dict[str, Any] | None = None
    semantic_types: dict[str, Any] | None = None
    pii_fields: list[dict[str, Any]] | None = None
    field_descriptions: dict[str, str] | None = None


def validate_documentation_result(payload: dict[str, Any]) -> DocumentationResult:
    """Validate a documentation JSON payload; raises pydantic.ValidationError on failure."""
    return DocumentationResult.model_validate(payload)


class TransformOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: str
    mapping: dict[str, str] | None = None
    field: str | None = None
    strategy: str | None = None
    value: Any | None = None
    pattern: str | None = None
    replacement: str | None = None
    regex: bool | None = None
    fields: list[str] | dict[str, str] | None = None
    expression: str | None = None


class TransformSpec(BaseModel):
    """Declarative transform spec returned by ``ai.suggest_transform``."""

    model_config = ConfigDict(extra="forbid")

    operations: list[TransformOperation]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


_ALLOWED_TRANSFORM_OPS = frozenset({"rename", "fill", "replace", "select", "filter"})


def validate_transform_spec(payload: dict[str, Any]) -> TransformSpec:
    """Validate transform spec; raises on unknown operations."""
    spec = TransformSpec.model_validate(payload)
    for operation in spec.operations:
        if operation.op not in _ALLOWED_TRANSFORM_OPS:
            raise ValueError(f"Unknown transform operation: {operation.op!r}")
    return spec
