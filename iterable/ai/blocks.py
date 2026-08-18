"""Block-based documentation generators.

Each block generator takes a shared :class:`BlockContext` and returns a dict of
``{"markdown": str, "data": dict}``. Blocks are independent and individually
testable. LLM-backed blocks use structured output (JSON Schema) via the provider
abstraction; the ``statistics`` block is computed deterministically without an LLM.

Deferred blocks (``lineage``, ``geo_coverage``) are registered but return a
not-implemented marker so callers can request them without failing.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .providers import LLMProvider

logger = logging.getLogger("iterable.ai.blocks")

# Column batch size for schema token management. The schema block is generated in
# batches of at most this many columns so every field is described even for wide
# datasets (and so the field list is never truncated out of the prompt).
SCHEMA_BATCH_SIZE = 25


# ---------------------------------------------------------------------------
# Localization
# ---------------------------------------------------------------------------
#
# Static markdown labels (section headings, table headers, rating words) are
# localized for the documented supported languages. Unknown languages fall back
# to English. LLM-generated free text is localized by the prompts themselves.

_LANG_ALIASES = {
    "en": "english",
    "eng": "english",
    "english": "english",
    "ru": "russian",
    "rus": "russian",
    "russian": "russian",
    "русский": "russian",
    "fr": "french",
    "fra": "french",
    "french": "french",
    "français": "french",
    "es": "spanish",
    "spa": "spanish",
    "spanish": "spanish",
    "español": "spanish",
}

_LABELS_EN: dict[str, str] = {
    "documentation": "Documentation",
    "contents": "Contents",
    "general": "General",
    "schema": "Schema",
    "quality": "Data Quality",
    "examples": "Usage Examples",
    "statistics": "Statistics",
    "codebook": "Codebook",
    "agent_skill": "Agent Skill",
    "lineage": "Lineage",
    "geo_coverage": "Geographic Coverage",
    "when_to_use": "When to use",
    "dataset_facts": "Dataset facts",
    "workflow": "Workflow",
    "safety": "Safety constraints",
    "example_steps": "Example analysis steps",
    "caveats": "Dataset caveats",
    "property": "Property",
    "value": "Value",
    "format": "Format",
    "file_name": "File name",
    "file_size": "File size (bytes)",
    "sha256": "SHA-256",
    "encoding": "Encoding",
    "records": "Records",
    "tables": "Tables",
    "topic": "Topic",
    "language": "Language",
    "temporal_coverage": "Temporal coverage",
    "territory": "Territory",
    "field": "Field",
    "type": "Type",
    "nullable": "Nullable",
    "description": "Description",
    "example": "Example",
    "yes": "yes",
    "no": "no",
    "overall_quality": "Overall quality",
    "observations": "Observations",
    "rating_high": "High",
    "rating_medium": "Medium",
    "rating_low": "Low",
    "count": "Count",
    "nulls": "Nulls",
    "null_pct": "Null %",
    "unique": "Unique",
    "dictionary": "Dictionary",
    "code": "Code",
    "meaning": "Meaning",
    "reference": "Reference",
    "no_dictionary_fields": "No dictionary fields detected.",
}

_LABELS_RU: dict[str, str] = {
    "documentation": "Документация",
    "contents": "Содержание",
    "general": "Общие сведения",
    "schema": "Схема данных",
    "quality": "Качество данных",
    "examples": "Примеры использования",
    "statistics": "Статистика",
    "codebook": "Справочник кодов",
    "agent_skill": "Навык агента",
    "lineage": "Происхождение",
    "geo_coverage": "Географическое покрытие",
    "when_to_use": "Когда использовать",
    "dataset_facts": "Факты о наборе данных",
    "workflow": "Рабочий процесс",
    "safety": "Ограничения безопасности",
    "example_steps": "Примеры шагов анализа",
    "caveats": "Оговорки по данным",
    "property": "Свойство",
    "value": "Значение",
    "format": "Формат",
    "file_name": "Имя файла",
    "file_size": "Размер файла (байт)",
    "sha256": "SHA-256",
    "encoding": "Кодировка",
    "records": "Число записей",
    "tables": "Таблицы",
    "topic": "Тематика",
    "language": "Язык",
    "temporal_coverage": "Временной охват",
    "territory": "Территория",
    "field": "Поле",
    "type": "Тип",
    "nullable": "Допускает NULL",
    "description": "Описание",
    "example": "Пример",
    "yes": "да",
    "no": "нет",
    "overall_quality": "Общая оценка качества",
    "observations": "Замечания",
    "rating_high": "Высокое",
    "rating_medium": "Среднее",
    "rating_low": "Низкое",
    "count": "Количество",
    "nulls": "Пропуски",
    "null_pct": "Доля пропусков",
    "unique": "Уникальные",
    "dictionary": "Справочник",
    "code": "Код",
    "meaning": "Значение",
    "reference": "Справочник",
    "no_dictionary_fields": "Поля-справочники не обнаружены.",
}

_LABELS_FR: dict[str, str] = {
    "documentation": "Documentation",
    "contents": "Table des matières",
    "general": "Informations générales",
    "schema": "Schéma des données",
    "quality": "Qualité des données",
    "examples": "Exemples d'utilisation",
    "statistics": "Statistiques",
    "codebook": "Dictionnaire de codes",
    "agent_skill": "Compétence d'agent",
    "lineage": "Traçabilité",
    "geo_coverage": "Couverture géographique",
    "when_to_use": "Quand l'utiliser",
    "dataset_facts": "Faits sur le jeu de données",
    "workflow": "Flux de travail",
    "safety": "Contraintes de sécurité",
    "example_steps": "Exemples d'étapes d'analyse",
    "caveats": "Avertissements sur les données",
    "property": "Propriété",
    "value": "Valeur",
    "format": "Format",
    "file_name": "Nom du fichier",
    "file_size": "Taille du fichier (octets)",
    "sha256": "SHA-256",
    "encoding": "Encodage",
    "records": "Enregistrements",
    "tables": "Tables",
    "topic": "Sujet",
    "language": "Langue",
    "temporal_coverage": "Couverture temporelle",
    "territory": "Territoire",
    "field": "Champ",
    "type": "Type",
    "nullable": "Nullable",
    "description": "Description",
    "example": "Exemple",
    "yes": "oui",
    "no": "non",
    "overall_quality": "Qualité globale",
    "observations": "Observations",
    "rating_high": "Élevée",
    "rating_medium": "Moyenne",
    "rating_low": "Faible",
    "count": "Nombre",
    "nulls": "Valeurs nulles",
    "null_pct": "% de valeurs nulles",
    "unique": "Uniques",
    "dictionary": "Dictionnaire",
    "code": "Code",
    "meaning": "Signification",
    "reference": "Référence",
    "no_dictionary_fields": "Aucun champ de type dictionnaire détecté.",
}

_LABELS_ES: dict[str, str] = {
    "documentation": "Documentación",
    "contents": "Contenido",
    "general": "Información general",
    "schema": "Esquema de datos",
    "quality": "Calidad de los datos",
    "examples": "Ejemplos de uso",
    "statistics": "Estadísticas",
    "codebook": "Libro de códigos",
    "agent_skill": "Habilidad de agente",
    "lineage": "Linaje",
    "geo_coverage": "Cobertura geográfica",
    "when_to_use": "Cuándo usar",
    "dataset_facts": "Hechos del conjunto de datos",
    "workflow": "Flujo de trabajo",
    "safety": "Restricciones de seguridad",
    "example_steps": "Pasos de análisis de ejemplo",
    "caveats": "Advertencias sobre los datos",
    "property": "Propiedad",
    "value": "Valor",
    "format": "Formato",
    "file_name": "Nombre del archivo",
    "file_size": "Tamaño del archivo (bytes)",
    "sha256": "SHA-256",
    "encoding": "Codificación",
    "records": "Registros",
    "tables": "Tablas",
    "topic": "Tema",
    "language": "Idioma",
    "temporal_coverage": "Cobertura temporal",
    "territory": "Territorio",
    "field": "Campo",
    "type": "Tipo",
    "nullable": "Anulable",
    "description": "Descripción",
    "example": "Ejemplo",
    "yes": "sí",
    "no": "no",
    "overall_quality": "Calidad general",
    "observations": "Observaciones",
    "rating_high": "Alta",
    "rating_medium": "Media",
    "rating_low": "Baja",
    "count": "Recuento",
    "nulls": "Nulos",
    "null_pct": "% de nulos",
    "unique": "Únicos",
    "dictionary": "Diccionario",
    "code": "Código",
    "meaning": "Significado",
    "reference": "Referencia",
    "no_dictionary_fields": "No se detectaron campos de diccionario.",
}

_LABELS: dict[str, dict[str, str]] = {
    "english": _LABELS_EN,
    "russian": _LABELS_RU,
    "french": _LABELS_FR,
    "spanish": _LABELS_ES,
}


def get_labels(language: str | None) -> dict[str, str]:
    """Return the localized label table for a language (English fallback)."""
    key = _LANG_ALIASES.get((language or "english").strip().lower(), "english")
    table = _LABELS.get(key, _LABELS_EN)
    if table is _LABELS_EN:
        return _LABELS_EN
    # Merge over English so any missing key falls back gracefully.
    return {**_LABELS_EN, **table}


def section_title(block_name: str, language: str | None) -> str:
    """Return the localized section title for a block."""
    return get_labels(language).get(block_name, block_name.replace("_", " ").title())


def localize_rating(value: Any, labels: dict[str, str]) -> str:
    """Localize a canonical quality rating (High/Medium/Low) when recognized."""
    if not isinstance(value, str):
        return str(value)
    mapping = {
        "high": labels["rating_high"],
        "medium": labels["rating_medium"],
        "low": labels["rating_low"],
    }
    return mapping.get(value.strip().lower(), value)


@dataclass
class BlockContext:
    """Shared inputs available to every block generator."""

    source: str | None = None
    format: str | None = None
    language: str = "English"
    user_context: dict[str, Any] = field(default_factory=dict)
    file_meta: dict[str, Any] = field(default_factory=dict)
    schema_info: dict[str, Any] = field(default_factory=dict)
    samples: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, dict[str, Any]] = field(default_factory=dict)
    record_count: int | None = None
    provider: LLMProvider | None = None
    model: str | None = None
    temperature: float = 0.3
    max_tokens: int | None = None

    def field_names(self) -> list[str]:
        fields = self.schema_info.get("fields") if self.schema_info else None
        if isinstance(fields, dict):
            return list(fields.keys())
        if self.samples and isinstance(self.samples[0], dict):
            return list(self.samples[0].keys())
        if self.statistics:
            return list(self.statistics.keys())
        return []


BlockResult = dict[str, Any]
BlockGenerator = Callable[[BlockContext], BlockResult]


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "... (truncated)"


def _context_section(ctx: BlockContext) -> str:
    parts: list[str] = []
    if ctx.user_context:
        parts.append("## User-provided context:")
        parts.append(_truncate(json.dumps(ctx.user_context, default=str, ensure_ascii=False), 1500))
    if ctx.file_meta:
        meta = {k: v for k, v in ctx.file_meta.items() if k in ("file_name", "format", "encoding", "table_count")}
        if meta:
            parts.append("## File metadata:")
            parts.append(json.dumps(meta, default=str, ensure_ascii=False))
    if ctx.record_count is not None:
        parts.append(f"Record count: {ctx.record_count}")
    return "\n".join(parts)


def _schema_section(ctx: BlockContext, limit: int = 2500) -> str:
    if not ctx.schema_info:
        return ""
    return "## Schema:\n" + _truncate(json.dumps(ctx.schema_info, indent=2, default=str), limit)


def _samples_section(ctx: BlockContext, limit: int = 1500) -> str:
    if not ctx.samples:
        return ""
    return "## Sample rows:\n" + _truncate(json.dumps(ctx.samples[:10], indent=2, default=str), limit)


def _stats_section(ctx: BlockContext, limit: int = 2000) -> str:
    if not ctx.statistics:
        return ""
    return "## Statistics:\n" + _truncate(json.dumps(ctx.statistics, indent=2, default=str), limit)


def _structured(ctx: BlockContext, prompt: str, block_name: str) -> dict[str, Any]:
    """Run a structured-output request for a block and validate it."""
    if ctx.provider is None:
        return {}
    try:
        from . import models
    except ImportError as exc:
        raise ImportError(
            "Pydantic is required for AI block structured output. Install it with: pip install iterabledata[pydantic]"
        ) from exc

    schema = models.block_json_schema(block_name)
    if schema is None:
        return {}
    try:
        raw = ctx.provider.generate_structured(
            prompt,
            schema,
            model=ctx.model,
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
            schema_name=f"{block_name}_block",
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Structured generation failed for block %r: %s", block_name, exc)
        return {}
    model_cls = models.block_model_for(block_name)
    if model_cls is not None and raw:
        try:
            return model_cls.model_validate(raw).model_dump(exclude_none=True)
        except Exception as exc:
            logger.warning("Validation failed for block %r: %s", block_name, exc)
    return raw if isinstance(raw, dict) else {}


# ---------------------------------------------------------------------------
# Block generators
# ---------------------------------------------------------------------------


def generate_general(ctx: BlockContext) -> BlockResult:
    """General block: dataset overview combining file metadata and LLM analysis."""
    prompt = "\n\n".join(
        p
        for p in [
            f"Produce a general overview of this dataset in {ctx.language}.",
            "Provide a concise title, a 2-4 sentence description, the main topic, the data "
            "language, temporal coverage if evident, and territory if evident.",
            _context_section(ctx),
            _schema_section(ctx, 1500),
            _samples_section(ctx, 1000),
        ]
        if p
    )
    data = _structured(ctx, prompt, "general")

    # Merge user-provided context (takes precedence) and file metadata.
    for key in ("title", "description", "tags", "territory"):
        if ctx.user_context.get(key) is not None:
            data[key] = ctx.user_context[key]
    if ctx.user_context.get("source_url"):
        data["source_url"] = ctx.user_context["source_url"]

    data["file_name"] = ctx.file_meta.get("file_name")
    data["file_size"] = ctx.file_meta.get("file_size")
    data["file_hash"] = ctx.file_meta.get("file_hash")
    data["format"] = ctx.format or ctx.file_meta.get("format")
    data["encoding"] = ctx.file_meta.get("encoding")
    data["record_count"] = ctx.record_count
    data["table_count"] = ctx.file_meta.get("table_count")
    if ctx.file_meta.get("tables"):
        data["tables"] = ctx.file_meta["tables"]

    return {"markdown": _render_general_md(data, ctx.language), "data": data}


def _render_general_md(data: dict[str, Any], language: str | None = None) -> str:
    lbl = get_labels(language)
    title = data.get("title") or "Dataset"
    lines = [f"## {lbl['general']}\n", f"**{title}**\n"]
    if data.get("description"):
        lines.append(f"{data['description']}\n")
    rows = [
        (lbl["format"], data.get("format")),
        (lbl["file_name"], data.get("file_name")),
        (lbl["file_size"], data.get("file_size")),
        (lbl["sha256"], data.get("file_hash")),
        (lbl["encoding"], data.get("encoding")),
        (lbl["records"], data.get("record_count")),
        (lbl["tables"], data.get("table_count")),
        (lbl["topic"], data.get("topic")),
        (lbl["language"], data.get("language")),
        (lbl["temporal_coverage"], data.get("temporal_coverage")),
        (lbl["territory"], data.get("territory")),
    ]
    present = [(k, v) for k, v in rows if v is not None]
    if present:
        lines.append(f"| {lbl['property']} | {lbl['value']} |")
        lines.append("| :--- | :--- |")
        for key, value in present:
            lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def generate_schema(ctx: BlockContext) -> BlockResult:
    """Schema block: per-field descriptions, batched for wide schemas."""
    field_names = ctx.field_names()
    schema_fields = ctx.schema_info.get("fields", {}) if ctx.schema_info else {}

    all_fields: list[dict[str, Any]] = []
    if ctx.provider is not None and field_names:
        batches = _column_batches(field_names)
        for batch in batches:
            # Keep the per-field schema compact so the full field list always fits in
            # the prompt (avoids truncating columns out of the request).
            sub_schema = {
                name: {
                    "type": (schema_fields.get(name) or {}).get("type"),
                    "nullable": (schema_fields.get(name) or {}).get("nullable"),
                }
                for name in batch
            }
            field_list = ", ".join(batch)
            prompt = "\n\n".join(
                p
                for p in [
                    f"Document the schema of this dataset in {ctx.language}.",
                    f"Return exactly one `fields` entry for EVERY one of these {len(batch)} fields, "
                    f"in this order, and do not omit or merge any: {field_list}.",
                    "For each field provide name, physical type, an optional semantic_type, a "
                    "clear description, an example value, and whether it is nullable.",
                    _context_section(ctx),
                    "## Fields and inferred types:\n" + json.dumps(sub_schema, indent=2, default=str),
                    _samples_section(ctx, 1500),
                ]
                if p
            )
            data = _structured(ctx, prompt, "schema")
            returned = data.get("fields", []) or []
            all_fields.extend(returned)

            # Retry once for any fields the model skipped within this batch.
            described = {f.get("name") for f in returned if isinstance(f, dict)}
            missing = [name for name in batch if name not in described]
            if missing and len(missing) < len(batch):
                retry_schema = {name: sub_schema[name] for name in missing}
                retry_prompt = "\n\n".join(
                    [
                        f"Document the schema of this dataset in {ctx.language}.",
                        f"Return one `fields` entry for EACH of these {len(missing)} fields, omitting none: "
                        f"{', '.join(missing)}.",
                        "For each field provide name, physical type, an optional semantic_type, a "
                        "clear description, an example value, and whether it is nullable.",
                        "## Fields and inferred types:\n" + json.dumps(retry_schema, indent=2, default=str),
                    ]
                )
                retry_data = _structured(ctx, retry_prompt, "schema")
                all_fields.extend(retry_data.get("fields", []) or [])

    # Deduplicate by field name (a field may be returned by both the main pass and a
    # retry); keep the richest entry (the one with a description).
    deduped: dict[str, dict[str, Any]] = {}
    for f in all_fields:
        if not isinstance(f, dict) or not f.get("name"):
            continue
        name = f["name"]
        existing = deduped.get(name)
        if existing is None or (not existing.get("description") and f.get("description")):
            deduped[name] = f

    # Order by the dataset's field order, ensuring every known field appears even if
    # the LLM omitted some (filled from the inferred schema).
    ordered_fields: list[dict[str, Any]] = []
    for name in field_names:
        if name in deduped:
            ordered_fields.append(deduped.pop(name))
        else:
            inferred = schema_fields.get(name, {}) if isinstance(schema_fields, dict) else {}
            ordered_fields.append(
                {
                    "name": name,
                    "type": inferred.get("type"),
                    "nullable": inferred.get("nullable"),
                }
            )
    # Append any extra fields the model returned that are not in the known field set.
    ordered_fields.extend(deduped.values())

    data = {"fields": ordered_fields}
    return {"markdown": _render_schema_md(ordered_fields, ctx.language), "data": data}


def _column_batches(field_names: list[str]) -> list[list[str]]:
    if len(field_names) <= SCHEMA_BATCH_SIZE:
        return [field_names]
    return [field_names[i : i + SCHEMA_BATCH_SIZE] for i in range(0, len(field_names), SCHEMA_BATCH_SIZE)]


def _render_schema_md(fields: list[dict[str, Any]], language: str | None = None) -> str:
    lbl = get_labels(language)
    lines = [
        f"## {lbl['schema']}\n",
        f"| {lbl['field']} | {lbl['type']} | {lbl['nullable']} | {lbl['description']} | {lbl['example']} |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for f in fields:
        if not isinstance(f, dict):
            continue
        name = f.get("name", "")
        ftype = f.get("type") or ""
        nullable = f.get("nullable")
        nullable_str = "" if nullable is None else (lbl["yes"] if nullable else lbl["no"])
        desc = (f.get("description") or "").replace("\n", " ")
        example = f.get("example")
        example_str = "" if example is None else str(example).replace("\n", " ")
        lines.append(f"| {name} | {ftype} | {nullable_str} | {desc} | {example_str} |")
    return "\n".join(lines)


def generate_quality(ctx: BlockContext) -> BlockResult:
    """Quality block: LLM observations grounded in statistics."""
    prompt = "\n\n".join(
        p
        for p in [
            f"Assess the data quality of this dataset. Write ALL text (the rationale and every "
            f"observation) in {ctx.language}.",
            "Identify missing-value issues, anomalies, duplicates, and type inconsistencies. "
            "Set `overall` to exactly one of the canonical English tokens High, Medium, or Low "
            "(it will be localized for display), but write the `rationale` and all `observations` "
            f"text in {ctx.language}.",
            _context_section(ctx),
            _schema_section(ctx, 1200),
            _stats_section(ctx, 2000),
        ]
        if p
    )
    data = _structured(ctx, prompt, "quality")
    return {"markdown": _render_quality_md(data, ctx.language), "data": data}


def _render_quality_md(data: dict[str, Any], language: str | None = None) -> str:
    lbl = get_labels(language)
    lines = [f"## {lbl['quality']}\n"]
    if data.get("overall"):
        lines.append(f"**{lbl['overall_quality']}:** {localize_rating(data['overall'], lbl)}\n")
    if data.get("rationale"):
        lines.append(f"{data['rationale']}\n")
    observations = data.get("observations") or []
    if observations:
        lines.append(f"**{lbl['observations']}:**\n")
        for obs in observations:
            if isinstance(obs, dict):
                severity = obs.get("severity")
                prefix = f"({localize_rating(severity, lbl)}) " if severity else ""
                field_ref = f"`{obs.get('field')}`: " if obs.get("field") else ""
                lines.append(f"- {prefix}{field_ref}{obs.get('observation', '')}")
    return "\n".join(lines)


def generate_examples(ctx: BlockContext) -> BlockResult:
    """Examples block: usage code samples appropriate to the format."""
    filename = ctx.file_meta.get("file_name") or ctx.source or "data"
    field_names = ctx.field_names()
    fields_line = ", ".join(field_names) if field_names else "(none)"
    prompt = "\n\n".join(
        p
        for p in [
            f"Generate practical usage code examples for this dataset in {ctx.language}.",
            "Return 2-4 examples. Include SQL (DuckDB) and Python (pandas); add R when relevant.",
            "Each example must have `tool`, `language`, runnable `code`, and a short `description`.",
            "Set `language` to exactly one of: python, r, sql. Never put a tool name (pandas, DuckDB, "
            "jsonlite, etc.) in the `language` field.",
            "Safety and validity rules — examples that violate these are discarded:",
            f"- Python and R: read only the local file {filename!r}. No remote URLs, no shell/"
            "system calls, no package installation, and no writing or exporting files "
            "(no to_csv/to_excel/to_parquet/to_json/write_* / save).",
            "- SQL: exactly one read-only SELECT or WITH query against the table named `dataset` "
            "(not the filename, and not read_parquet/read_csv/read_json). Quote real column names "
            "when needed. Do not use CREATE, INSERT, UPDATE, DELETE, COPY, ATTACH, INSTALL, LOAD, "
            "PIVOT, DESCRIBE, SHOW, or multiple statements.",
            f"- Use only these field names: {fields_line}.",
            _context_section(ctx),
            _schema_section(ctx, 1200),
        ]
        if p
    )
    data = _structured(ctx, prompt, "examples")
    return {"markdown": _render_examples_md(data, ctx.language), "data": data}


def _render_examples_md(data: dict[str, Any], language: str | None = None) -> str:
    lines = [f"## {get_labels(language)['examples']}\n"]
    for ex in data.get("examples") or []:
        if not isinstance(ex, dict):
            continue
        title = ex.get("tool") or ex.get("language") or "Example"
        lines.append(f"### {title}\n")
        if ex.get("description"):
            lines.append(f"{ex['description']}\n")
        lang = (ex.get("language") or "").lower()
        lines.append(f"```{lang}\n{ex.get('code', '')}\n```\n")
    return "\n".join(lines)


def generate_statistics(ctx: BlockContext) -> BlockResult:
    """Statistics block: computed deterministically (no LLM)."""
    stats = ctx.statistics or {}
    return {"markdown": _render_statistics_md(stats, ctx.language), "data": {"fields": stats}}


def _render_statistics_md(stats: dict[str, dict[str, Any]], language: str | None = None) -> str:
    lbl = get_labels(language)
    lines = [
        f"## {lbl['statistics']}\n",
        f"| {lbl['field']} | {lbl['count']} | {lbl['nulls']} | {lbl['null_pct']} | "
        f"{lbl['unique']} | {lbl['dictionary']} |",
        "| :--- | ---: | ---: | ---: | ---: | :---: |",
    ]
    for name, s in stats.items():
        if not isinstance(s, dict):
            continue
        null_pct = s.get("null_fraction")
        null_pct_str = f"{null_pct * 100:.1f}%" if isinstance(null_pct, (int, float)) else ""
        is_dict = lbl["yes"] if s.get("is_dictionary") else ""
        lines.append(
            f"| {name} | {s.get('count', '')} | {s.get('null_count', '')} | {null_pct_str} | "
            f"{s.get('unique_count', '')} | {is_dict} |"
        )
    return "\n".join(lines)


def generate_agent_skill(ctx: BlockContext) -> BlockResult:
    """Optional agent-skill block: portable YAML-frontmatter + Markdown instructions."""
    filename = ctx.file_meta.get("file_name") or ctx.source or "data"
    field_names = ctx.field_names()
    fmt = ctx.format or ctx.file_meta.get("format") or "unknown"
    prompt = "\n\n".join(
        p
        for p in [
            f"Create a portable AI agent skill for working with this specific dataset file in {ctx.language}.",
            "Return structured fields only (not full markdown). Rules:",
            f"- `name`: a short kebab-case skill id derived from the file ({filename!r}), ASCII preferred.",
            "- `description`: one or two sentences summarizing when an agent should load this skill.",
            f"- Write `when_to_use`, `workflow_steps`, `safety_constraints`, `dataset_caveats`, and "
            f"`example_steps` in {ctx.language}.",
            "- Workflow and example steps MUST use only real field names from the schema.",
            "- Safety constraints MUST include read-only analysis, no network calls, and no "
            "modification of the source file.",
            "- Do not invent columns, formats, or external APIs.",
            f"Known format: {fmt}. Known fields: {', '.join(field_names) if field_names else '(none)'}.",
            _context_section(ctx),
            _schema_section(ctx, 1500),
            _samples_section(ctx, 800),
            _stats_section(ctx, 1200),
        ]
        if p
    )
    data = _structured(ctx, prompt, "agent_skill")
    data = _finalize_agent_skill_data(data, ctx)
    return {"markdown": _render_agent_skill_md(data, ctx.language), "data": data}


def _finalize_agent_skill_data(data: dict[str, Any], ctx: BlockContext) -> dict[str, Any]:
    """Inject deterministic dataset facts and fill safe defaults for missing LLM fields."""
    result = dict(data) if isinstance(data, dict) else {}
    filename = ctx.file_meta.get("file_name") or ctx.source or "dataset"
    stem = str(filename).rsplit("/", 1)[-1]
    stem = stem.rsplit(".", 1)[0] if "." in stem else stem
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in stem).strip("-") or "dataset"
    while "--" in slug:
        slug = slug.replace("--", "-")

    if not result.get("name"):
        result["name"] = f"{slug}-dataset-skill"
    if not result.get("description"):
        result["description"] = f"Use this skill when analyzing the dataset file {filename}."
    result["file_name"] = ctx.file_meta.get("file_name") or filename
    result["format"] = ctx.format or ctx.file_meta.get("format")
    result["fields"] = ctx.field_names()
    result["record_count"] = ctx.record_count
    if not result.get("safety_constraints"):
        result["safety_constraints"] = [
            "Treat the dataset as read-only; do not modify or overwrite the source file.",
            "Do not make network requests while analyzing this dataset unless the user explicitly asks.",
            "Do not invent field names that are not present in the schema.",
        ]
    return result


def _yaml_scalar(value: str) -> str:
    """Quote a YAML scalar when needed for a minimal frontmatter emitter."""
    text = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return '""'
    if any(ch in text for ch in (":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", ">", "!", "%", "@", "`")):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if "\n" in text or text.startswith(("-", "'", '"')):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def _render_agent_skill_md(data: dict[str, Any], language: str | None = None) -> str:
    """Render a neutral agent-skill document (YAML frontmatter + Markdown body)."""
    lbl = get_labels(language)
    name = str(data.get("name") or "dataset-skill")
    description = str(data.get("description") or "")
    lines = [
        "---",
        f"name: {_yaml_scalar(name)}",
        f"description: {_yaml_scalar(description)}",
        "---",
        "",
        f"# {name}",
        "",
    ]
    if data.get("when_to_use"):
        lines.extend([f"## {lbl['when_to_use']}", "", str(data["when_to_use"]), ""])

    lines.extend([f"## {lbl['dataset_facts']}", ""])
    if data.get("file_name"):
        lines.append(f"- **{lbl['file_name']}:** `{data['file_name']}`")
    if data.get("format"):
        lines.append(f"- **{lbl['format']}:** `{data['format']}`")
    if data.get("record_count") is not None:
        lines.append(f"- **{lbl['records']}:** {data['record_count']}")
    fields = data.get("fields") or []
    if fields:
        field_list = ", ".join(f"`{name}`" for name in fields)
        lines.append(f"- **{lbl['field']}s:** {field_list}")
    lines.append("")

    caveats = [item for item in (data.get("dataset_caveats") or []) if isinstance(item, str) and item.strip()]
    if caveats:
        lines.extend([f"## {lbl['caveats']}", ""])
        for item in caveats:
            lines.append(f"- {item}")
        lines.append("")

    steps = [item for item in (data.get("workflow_steps") or []) if isinstance(item, str) and item.strip()]
    if steps:
        lines.extend([f"## {lbl['workflow']}", ""])
        for index, item in enumerate(steps, start=1):
            lines.append(f"{index}. {item}")
        lines.append("")

    safety = [item for item in (data.get("safety_constraints") or []) if isinstance(item, str) and item.strip()]
    if safety:
        lines.extend([f"## {lbl['safety']}", ""])
        for item in safety:
            lines.append(f"- {item}")
        lines.append("")

    examples = [item for item in (data.get("example_steps") or []) if isinstance(item, str) and item.strip()]
    if examples:
        lines.extend([f"## {lbl['example_steps']}", ""])
        for index, item in enumerate(examples, start=1):
            lines.append(f"{index}. {item}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate_codebook(ctx: BlockContext) -> BlockResult:
    """Codebook block: describes dictionary/lookup fields via the LLM."""
    dict_fields = {
        name: s for name, s in (ctx.statistics or {}).items() if isinstance(s, dict) and s.get("is_dictionary")
    }
    lbl = get_labels(ctx.language)
    if not dict_fields:
        data: dict[str, Any] = {"entries": []}
        return {"markdown": f"## {lbl['codebook']}\n\n{lbl['no_dictionary_fields']}", "data": data}

    summary = {
        name: {
            "unique_count": s.get("unique_count"),
            "top_values": s.get("top_values"),
        }
        for name, s in dict_fields.items()
    }
    prompt = "\n\n".join(
        p
        for p in [
            f"Build a codebook for the dictionary (lookup) fields of this dataset in {ctx.language}.",
            "For each field, identify any known reference (e.g. ISO country codes, currency codes, "
            "classifications), describe it, and map codes to meanings where possible.",
            _context_section(ctx),
            "## Dictionary fields:\n" + _truncate(json.dumps(summary, indent=2, default=str), 2500),
        ]
        if p
    )
    data = _structured(ctx, prompt, "codebook")
    if not data.get("entries"):
        data = {"entries": [{"field": name} for name in dict_fields]}
    return {"markdown": _render_codebook_md(data, ctx.language), "data": data}


def _render_codebook_md(data: dict[str, Any], language: str | None = None) -> str:
    lbl = get_labels(language)
    lines = [f"## {lbl['codebook']}\n"]
    for entry in data.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        lines.append(f"### `{entry.get('field', '')}`\n")
        if entry.get("description"):
            lines.append(f"{entry['description']}\n")
        if entry.get("reference"):
            lines.append(f"{lbl['reference']}: {entry['reference']}\n")
        values = entry.get("values")
        if isinstance(values, dict) and values:
            lines.append(f"| {lbl['code']} | {lbl['meaning']} |")
            lines.append("| :--- | :--- |")
            for code, meaning in values.items():
                lines.append(f"| {code} | {meaning} |")
            lines.append("")
    return "\n".join(lines)


def _deferred_block(name: str) -> BlockGenerator:
    def _gen(ctx: BlockContext) -> BlockResult:
        return {
            "markdown": "",
            "data": {"status": "not_implemented", "block": name},
        }

    return _gen


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class BlockSpec:
    name: str
    generator: BlockGenerator
    requires_llm: bool = True
    deferred: bool = False
    title: str = ""


BLOCK_REGISTRY: dict[str, BlockSpec] = {
    "general": BlockSpec("general", generate_general, requires_llm=True, title="General"),
    "schema": BlockSpec("schema", generate_schema, requires_llm=True, title="Schema"),
    "quality": BlockSpec("quality", generate_quality, requires_llm=True, title="Data Quality"),
    "examples": BlockSpec("examples", generate_examples, requires_llm=True, title="Usage Examples"),
    "statistics": BlockSpec("statistics", generate_statistics, requires_llm=False, title="Statistics"),
    "codebook": BlockSpec("codebook", generate_codebook, requires_llm=True, title="Codebook"),
    "agent_skill": BlockSpec("agent_skill", generate_agent_skill, requires_llm=True, title="Agent Skill"),
    "lineage": BlockSpec("lineage", _deferred_block("lineage"), requires_llm=False, deferred=True, title="Lineage"),
    "geo_coverage": BlockSpec(
        "geo_coverage", _deferred_block("geo_coverage"), requires_llm=False, deferred=True, title="Geographic Coverage"
    ),
}

# Default v1 block set.
DEFAULT_BLOCKS = ["general", "schema", "quality", "examples", "statistics", "agent_skill"]


def available_blocks() -> list[str]:
    """Return all registered block names."""
    return list(BLOCK_REGISTRY.keys())


def render_block(name: str, ctx: BlockContext) -> BlockResult:
    """Generate a single block by name."""
    spec = BLOCK_REGISTRY.get(name)
    if spec is None:
        raise ValueError(f"Unknown documentation block: {name!r}. Available: {', '.join(available_blocks())}")
    return spec.generator(ctx)
