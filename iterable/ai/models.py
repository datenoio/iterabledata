"""Pydantic models for AI documentation JSON output."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


# ---------------------------------------------------------------------------
# Block-based documentation models (used by ai.doc.generate_blocks)
# ---------------------------------------------------------------------------


class GeneralBlock(BaseModel):
    """Structured data for the ``general`` documentation block."""

    model_config = ConfigDict(extra="allow")

    title: str | None = None
    description: str | None = None
    topic: str | None = None
    language: str | None = None
    temporal_coverage: str | None = None
    territory: str | None = None
    tags: list[str] | None = None


def _stringify_schema_example(value: Any) -> str | None:
    """Coerce nested/scalar provider examples to a display string.

    Structured-output models often return arrays/objects for nested JSON fields
    even though the contract stores ``example`` as text for markdown tables.
    """

    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


class SchemaFieldModel(BaseModel):
    """A single field in the ``schema`` documentation block."""

    model_config = ConfigDict(extra="allow")

    name: str
    type: str | None = None
    semantic_type: str | None = None
    description: str | None = None
    example: str | None = None
    nullable: bool | None = None

    @field_validator("example", mode="before")
    @classmethod
    def _coerce_example(cls, value: Any) -> str | None:
        return _stringify_schema_example(value)


class SchemaBlock(BaseModel):
    """Structured data for the ``schema`` documentation block."""

    model_config = ConfigDict(extra="allow")

    fields: list[SchemaFieldModel] = Field(default_factory=list)


class QualityObservation(BaseModel):
    model_config = ConfigDict(extra="allow")

    observation: str
    severity: str | None = None
    field: str | None = None


class QualityBlock(BaseModel):
    """Structured data for the ``quality`` documentation block."""

    model_config = ConfigDict(extra="allow")

    overall: str | None = None
    rationale: str | None = None
    observations: list[QualityObservation] = Field(default_factory=list)


class UsageExample(BaseModel):
    model_config = ConfigDict(extra="allow")

    tool: str
    language: str | None = None
    code: str
    description: str | None = None


class ExamplesBlock(BaseModel):
    """Structured data for the ``examples`` documentation block."""

    model_config = ConfigDict(extra="allow")

    examples: list[UsageExample] = Field(default_factory=list)


class CodebookEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    field: str
    description: str | None = None
    values: dict[str, str] | None = None
    reference: str | None = None


class CodebookBlock(BaseModel):
    """Structured data for the ``codebook`` documentation block."""

    model_config = ConfigDict(extra="allow")

    entries: list[CodebookEntry] = Field(default_factory=list)


class AgentSkillBlock(BaseModel):
    """Structured data for the optional ``agent_skill`` documentation block."""

    model_config = ConfigDict(extra="allow")

    name: str
    description: str
    when_to_use: str | None = None
    workflow_steps: list[str] = Field(default_factory=list)
    safety_constraints: list[str] = Field(default_factory=list)
    dataset_caveats: list[str] = Field(default_factory=list)
    example_steps: list[str] = Field(default_factory=list)


_BLOCK_MODELS: dict[str, type[BaseModel]] = {
    "general": GeneralBlock,
    "schema": SchemaBlock,
    "quality": QualityBlock,
    "examples": ExamplesBlock,
    "codebook": CodebookBlock,
    "agent_skill": AgentSkillBlock,
}


def block_model_for(block_name: str) -> type[BaseModel] | None:
    """Return the Pydantic model for an LLM-generated block, or None."""
    return _BLOCK_MODELS.get(block_name)


def block_json_schema(block_name: str) -> dict[str, Any] | None:
    """Return the JSON Schema for a block model, or None if not modeled."""
    model = _BLOCK_MODELS.get(block_name)
    if model is None:
        return None
    return model.model_json_schema()


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
