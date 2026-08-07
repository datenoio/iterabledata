"""
AI-powered documentation generation.

Generates dataset documentation using LLM providers with comprehensive
metadata extraction, field-level descriptions, and semantic type detection.
"""

from __future__ import annotations

import collections.abc
import datetime
import json
import logging
import os
from typing import Any

from ..helpers.detect import open_iterable
from ..helpers.structured_logging import OperationContext
from ..ops import schema, stats
from ..types import Row
from . import blocks as blocks_module
from . import fileinfo, metadata, sampling, semantic
from .blocks import BlockContext
from .cache import get_cached, make_doc_cache_key, set_cached
from .context import redact_for_llm
from .progress import ProgressCallback, ProgressReporter, Stage, StageTimer
from .providers import get_provider

logger = logging.getLogger(__name__)

_CLOUD_PROVIDERS = frozenset({"openai", "anthropic", "gemini", "google", "azure", "openrouter", "perplexity"})


def generate(
    iterable: collections.abc.Iterable[Row] | str,
    provider: str = "openai",
    model: str | None = None,
    format: str = "markdown",
    api_key: str | None = None,
    base_url: str | None = None,
    include_schema: bool = True,
    include_samples: bool = True,
    sample_size: int = 5,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    # New parameters
    include_field_descriptions: bool = False,
    include_statistics: bool = True,
    include_metadata: bool = True,
    semantic_types: bool = False,
    pii_detect: bool = False,
    pii_mask_samples: bool = False,
    language: str = "English",
    validate_output: bool = False,
    cache: bool = False,
    context: dict[str, Any] | None = None,
    blocks: list[str] | None = None,
    progress: ProgressCallback | None = None,
    tables: list[str] | None = None,
    **kwargs: Any,
) -> str | dict[str, Any]:
    """
    Generate AI-powered documentation for a dataset.

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        provider: LLM provider - "openai", "openrouter", "ollama", "lmstudio", "perplexity" (default: "openai")
        model: Model name (provider-specific, uses default if None)
        format: Output format - "markdown", "json", "html", "yaml", "text" (default: "markdown")
        api_key: API key for the provider (uses environment variable if None)
        base_url: Base URL for local providers (Ollama, LMStudio)
        include_schema: Whether to include schema information (default: True)
        include_samples: Whether to include sample data (default: True)
        sample_size: Number of sample rows to include (default: 5)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate
        include_field_descriptions: Whether to generate field-level descriptions (default: False)
        include_statistics: Whether to include statistics (default: True)
        include_metadata: Whether to extract structured metadata (default: True)
        semantic_types: Whether to detect semantic types using Metacrafter (default: False)
        pii_detect: Whether to detect PII fields using Metacrafter (default: False)
        pii_mask_samples: Whether to mask PII in sample data (default: False)
        language: Language for AI-generated content (default: "English")
        validate_output: When True and format is json, validate response against Pydantic models
        cache: When True, cache results keyed by content hash and parameters (default: False)
        context: Optional user-provided context (title, description, tags, territory,
            source_url, dataset-card metadata) incorporated into prompts
        blocks: Optional list of documentation blocks. When provided, generation delegates to
            the block-based engine (:func:`generate_blocks`) and returns either an assembled
            markdown string (``format="markdown"``) or the structured result dict
            (``format="json"``)
        progress: Optional progress callback (used with ``blocks``)
        tables: Optional table/sheet selection for multi-table inputs (used with ``blocks``)
        **kwargs: Additional provider-specific options

    Returns:
        Generated documentation as string (markdown/html/yaml/text) or dict (json)

    Example:
        >>> from iterable.ai import doc
        >>> documentation = doc.generate(  # doctest: +SKIP
        ...     "data.csv",
        ...     provider="openai",
        ...     model="gpt-4o-mini",
        ...     format="markdown"
        ... )
        >>> print(documentation)  # doctest: +SKIP
    """
    # Block-based path: delegate to the structured block engine.
    if blocks is not None:
        result = generate_blocks(
            iterable,
            blocks=blocks,
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            context=context,
            language=language,
            tables=tables,
            sample_size=sample_size,
            include_statistics=include_statistics,
            temperature=temperature,
            max_tokens=max_tokens,
            progress=progress,
            **kwargs,
        )
        if format == "json":
            return result
        return result["full_document_markdown"]

    # Determine if we have a file path for semantic type detection and usage samples
    filename: str | None = None
    if isinstance(iterable, str) and os.path.exists(iterable):
        filename = iterable

    cache_params = {
        "provider": provider,
        "model": model,
        "format": format,
        "include_schema": include_schema,
        "include_samples": include_samples,
        "sample_size": sample_size,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "include_field_descriptions": include_field_descriptions,
        "include_statistics": include_statistics,
        "include_metadata": include_metadata,
        "semantic_types": semantic_types,
        "pii_detect": pii_detect,
        "pii_mask_samples": pii_mask_samples,
        "language": language,
        "validate_output": validate_output,
    }
    if cache:
        cache_key = make_doc_cache_key(iterable, cache_params, sample_size)
        cached = get_cached(cache_key)
        if cached is not None:
            return cached

    # Preserve user-provided context before the internal prompt context shadows the name.
    user_context = dict(context) if context else {}

    # Collect context information
    context: dict[str, Any] = {}
    if filename is not None:
        context["filename"] = filename
    if user_context:
        context["user_context"] = user_context

    # Get sample data first (needed for field names and metadata)
    samples: list[Row] = []
    field_names: list[str] = []

    if include_samples:
        try:
            # Open iterable if file path
            if isinstance(iterable, str):
                iterable_obj = open_iterable(iterable)
            else:
                iterable_obj = iterable

            for i, row in enumerate(iterable_obj):
                if i >= sample_size:
                    break
                samples.append(row)
            context["samples"] = samples

            # Extract field names from samples
            if samples:
                if isinstance(samples[0], dict):
                    field_names = list(samples[0].keys())
                elif isinstance(samples[0], list):
                    # Can't determine field names from list samples
                    field_names = []
        except Exception as e:
            logger.warning(f"Sample collection failed: {e}")

    # Get schema if requested
    # Use file path if available to avoid issues with exhausted iterables
    if include_schema:
        try:
            if isinstance(iterable, str) and os.path.exists(iterable):
                # Use file path - schema.infer will open it fresh
                schema_info = schema.infer(iterable, detect_constraints=True)
            else:
                # For non-file iterables, create a fresh iterable
                if isinstance(iterable, str):
                    iterable_obj = open_iterable(iterable)
                else:
                    iterable_obj = iterable
                # Try to reset if possible
                if hasattr(iterable_obj, "reset"):
                    iterable_obj.reset()
                schema_info = schema.infer(iterable_obj, detect_constraints=True)
            context["schema"] = schema_info
            # Update field names from schema if available
            schema_field_names = list(schema_info.get("fields", {}).keys())
            if schema_field_names:
                field_names = schema_field_names
        except Exception as e:
            logger.warning(f"Schema inference failed: {e}")
            # Field names already extracted from samples if available

    # Extract metadata if requested
    extracted_metadata: dict[str, Any] = {}
    if include_metadata and samples and field_names:
        try:
            keywords = metadata.extract_keywords(field_names, samples)
            extracted_metadata["keywords"] = keywords

            geographic_coverage = metadata.extract_geographic_coverage(samples, field_names)
            if geographic_coverage.get("countries") or geographic_coverage.get("regions"):
                extracted_metadata["geographic_coverage"] = geographic_coverage

            temporal_coverage = metadata.extract_temporal_coverage(samples, field_names)
            if temporal_coverage:
                extracted_metadata["temporal_coverage"] = temporal_coverage

            languages = metadata.detect_languages(samples, field_names)
            if languages:
                extracted_metadata["languages"] = languages

            data_theme = metadata.classify_data_theme(field_names, keywords)
            if data_theme:
                extracted_metadata["data_theme"] = data_theme

            context["metadata"] = extracted_metadata
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")

    # Detect semantic types if requested
    semantic_type_map: dict[str, list[dict[str, Any]]] = {}
    if semantic_types and filename:
        try:
            semantic_type_map = semantic.detect_semantic_types(filename, field_names)
            context["semantic_types"] = semantic_type_map
        except Exception as e:
            logger.warning(f"Semantic type detection failed: {e}")

    # Detect PII if requested
    pii_fields: list[dict[str, Any]] = []
    if pii_detect and filename:
        try:
            pii_fields = semantic.detect_pii(filename, field_names)
            context["pii_fields"] = pii_fields
        except Exception as e:
            logger.warning(f"PII detection failed: {e}")

    # Mask PII in samples if requested
    if pii_mask_samples and pii_fields and samples:
        try:
            samples = semantic.mask_pii_samples(samples, field_names, pii_fields)
            context["samples"] = samples
        except Exception as e:
            logger.warning(f"PII masking failed: {e}")
    elif include_samples and samples and provider.lower() in _CLOUD_PROVIDERS and not pii_mask_samples:
        # Heuristic redaction for cloud providers when Metacrafter masking is off
        samples = redact_for_llm(samples)
        context["samples"] = samples

    # Get statistics if requested
    # Use file path if available to avoid issues with exhausted iterables
    statistics: dict[str, Any] | None = None
    if include_statistics:
        try:
            if isinstance(iterable, str) and os.path.exists(iterable):
                # Use file path - stats.compute will open it fresh
                stats_info = stats.compute(iterable)
            else:
                # For non-file iterables, create a fresh iterable
                if isinstance(iterable, str):
                    iterable_obj = open_iterable(iterable)
                else:
                    iterable_obj = iterable
                # Try to reset if possible
                if hasattr(iterable_obj, "reset"):
                    iterable_obj.reset()
                stats_info = stats.compute(iterable_obj)
            statistics = stats_info
            context["statistics"] = statistics
        except Exception as e:
            logger.warning(f"Statistics computation failed: {e}")

    # Generate field descriptions if requested
    field_descriptions: dict[str, str] = {}
    if include_field_descriptions and field_names:
        try:
            llm_provider = get_provider(provider, api_key=api_key, base_url=base_url)
            field_descriptions = llm_provider.get_fields_info(field_names, language=language)
            context["field_descriptions"] = field_descriptions
        except Exception as e:
            logger.warning(f"Field description generation failed: {e}")

    # Build enhanced prompt
    prompt = _build_documentation_prompt(context, language)

    # Filter kwargs: only pass provider-safe options to the LLM (exclude doc.generate params)
    _doc_param_names = {
        "iterable",
        "provider",
        "model",
        "format",
        "api_key",
        "base_url",
        "include_schema",
        "include_samples",
        "sample_size",
        "temperature",
        "max_tokens",
        "include_field_descriptions",
        "include_statistics",
        "include_metadata",
        "semantic_types",
        "pii_detect",
        "pii_mask_samples",
        "language",
    }
    provider_kwargs = {k: v for k, v in kwargs.items() if k not in _doc_param_names}

    # Get provider and generate
    try:
        llm_provider = get_provider(provider, api_key=api_key, base_url=base_url)
        generated_text = llm_provider.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **provider_kwargs,
        )
    except ImportError as e:
        raise ImportError(
            f"Provider '{provider}' requires additional dependencies. "
            f"Install with: pip install openai (or provider-specific package)"
        ) from e

    # Format output
    result: str | dict[str, Any]
    if format == "json":
        result = _format_as_json(generated_text, context, llm_provider.get_usage_info(), extracted_metadata)
        if validate_output:
            try:
                from .models import validate_documentation_result

                validate_documentation_result(result)
            except ImportError:
                logger.warning("validate_output requires pydantic: pip install pydantic")
            except Exception as exc:
                logger.warning("Documentation JSON validation failed: %s", exc)
    elif format == "html":
        result = _format_as_html(generated_text)
    elif format == "yaml":
        result = _format_as_yaml(generated_text, context, llm_provider.get_usage_info(), extracted_metadata)
    elif format == "text":
        result = _format_as_text(generated_text)
    else:  # markdown
        result = generated_text

    if cache:
        set_cached(cache_key, result)
    return result


def generate_blocks(
    iterable: collections.abc.Iterable[Row] | str,
    blocks: list[str] | None = None,
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    context: dict[str, Any] | None = None,
    language: str = "English",
    tables: list[str] | None = None,
    sample_size: int | None = None,
    include_statistics: bool = True,
    detect_constraints: bool = True,
    temperature: float = 0.3,
    max_tokens: int | None = None,
    progress: ProgressCallback | None = None,
    job_id: str | None = None,
    redact_samples: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """Generate dataset documentation as independent, structured blocks.

    Returns a structured result of the shape::

        {
          "job_id": str,
          "created_at": ISO-8601 str,
          "source": {...},
          "blocks": {name: {"markdown": str, "data": {...}}},
          "full_document_markdown": str,
        }

    Args:
        iterable: An iterable of row dictionaries, or a file path/stream
        blocks: Block names to generate (default: general, schema, quality, examples, statistics).
            Unknown names raise ValueError; deferred blocks return a not-implemented marker.
        provider: LLM provider name (None resolves from ``LLM_PROVIDER`` env, default "openai")
        model: Model name (provider-specific)
        api_key: API key (falls back to env vars)
        base_url: Base URL for local/compatible providers
        context: User-provided context merged into prompts and the general block
        language: Output language (default: "English")
        tables: Optional table/sheet selection for multi-table inputs
        sample_size: Override the per-tier sample row count
        include_statistics: Compute statistics (needed by statistics/quality/codebook blocks)
        detect_constraints: Detect schema constraints during inference
        temperature: Sampling temperature for LLM blocks
        max_tokens: Maximum tokens per LLM block
        progress: Optional progress callback invoked per stage
        job_id: Optional job identifier (generated when omitted)
        redact_samples: Redact likely PII in samples before sending to cloud providers
        **kwargs: Reserved for future use

    Returns:
        Structured documentation result dict.
    """
    requested = list(blocks) if blocks else list(blocks_module.DEFAULT_BLOCKS)
    for name in requested:
        if name not in blocks_module.BLOCK_REGISTRY:
            raise ValueError(
                f"Unknown documentation block: {name!r}. Available: {', '.join(blocks_module.available_blocks())}"
            )

    user_context = dict(context) if context else {}
    reporter = ProgressReporter(progress, job_id=job_id)

    source = iterable if isinstance(iterable, str) and os.path.exists(iterable) else None

    # Materialize non-file, single-use iterables so multiple passes are possible.
    materialized: list[Row] | None = None
    if source is None and not isinstance(iterable, str):
        if isinstance(iterable, list):
            materialized = iterable
        else:
            materialized = list(iterable)

    needs_llm = any(blocks_module.BLOCK_REGISTRY[n].requires_llm for n in requested)
    llm_provider = None
    if needs_llm:
        try:
            llm_provider = get_provider(provider, api_key=api_key, base_url=base_url)
        except Exception as exc:
            logger.warning("LLM provider unavailable, LLM blocks will be empty: %s", exc)

    with OperationContext("ai_documentation", job_id=reporter.job_id):
        reporter.emit(Stage.QUEUED, 0, "queued")

        # Resolve tables for multi-table inputs.
        resolved_tables = _resolve_tables(source, tables)

        # Stage: parsing (file metadata).
        file_meta: dict[str, Any] = {}
        with StageTimer(reporter, Stage.PARSING, "extract metadata", progress=10):
            if source is not None:
                file_meta = fileinfo.file_metadata(source)
            elif isinstance(iterable, str):
                file_meta = {"file_name": os.path.basename(iterable), "format": fileinfo.detect_format(iterable)}

        fmt = file_meta.get("format")

        # Stage: sampling + schema + stats for the primary (default) table.
        primary_input: collections.abc.Iterable[Row] | str
        primary_input = source if source is not None else (materialized if materialized is not None else iterable)

        with StageTimer(reporter, Stage.SAMPLING, "sample and profile", progress=30):
            primary = _prepare_table_context(
                primary_input,
                size_bytes=file_meta.get("file_size"),
                sample_size=sample_size,
                include_statistics=include_statistics,
                detect_constraints=detect_constraints,
                redact_samples=redact_samples,
                provider_name=provider,
            )

        base_ctx = BlockContext(
            source=source,
            format=fmt,
            language=language,
            user_context=user_context,
            file_meta=file_meta,
            schema_info=primary["schema"],
            samples=primary["samples"],
            statistics=primary["statistics"],
            record_count=primary["record_count"],
            provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Stage: generating blocks.
        result_blocks: dict[str, Any] = {}
        total = len(requested)
        for index, name in enumerate(requested):
            pct = 40 + int(50 * (index / max(1, total)))
            spec = blocks_module.BLOCK_REGISTRY[name]
            with StageTimer(reporter, Stage.GENERATING, f"block: {name}", progress=pct, block=name):
                if name == "schema" and resolved_tables and len(resolved_tables) > 1:
                    _generate_multitable_schema(
                        result_blocks,
                        base_ctx,
                        source,
                        resolved_tables,
                        sample_size=sample_size,
                        include_statistics=include_statistics,
                        detect_constraints=detect_constraints,
                        redact_samples=redact_samples,
                        provider_name=provider,
                    )
                else:
                    result_blocks[name] = blocks_module.render_block(name, base_ctx)
            usage = llm_provider.get_usage_info() if llm_provider is not None and spec.requires_llm else None
            if usage:
                logger.info(
                    "block generated: %s",
                    name,
                    extra={
                        "job_id": reporter.job_id,
                        "stage": Stage.GENERATING.value,
                        "block": name,
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "event_type": "ai_documentation",
                    },
                )

        # Stage: assembling.
        with StageTimer(reporter, Stage.ASSEMBLING, "assemble document", progress=95):
            source_desc = _source_descriptor(source, iterable, file_meta, primary["record_count"], resolved_tables)
            full_md = _assemble_markdown(base_ctx, result_blocks, requested, resolved_tables)

        reporter.emit(Stage.COMPLETED, 100, "completed")

    return {
        "job_id": reporter.job_id,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": source_desc,
        "blocks": result_blocks,
        "full_document_markdown": full_md,
    }


def _resolve_tables(source: str | None, tables: list[str] | None) -> list[str] | None:
    if source is None:
        return None
    detected = fileinfo.list_tables(source)
    if tables:
        if detected:
            return [t for t in tables if t in detected] or tables
        return tables
    if detected and len(detected) > 1:
        return detected
    return None


def _prepare_table_context(
    input_obj: collections.abc.Iterable[Row] | str,
    *,
    size_bytes: int | None,
    sample_size: int | None,
    include_statistics: bool,
    detect_constraints: bool,
    redact_samples: bool,
    provider_name: str | None,
) -> dict[str, Any]:
    """Infer schema, sample rows, compute stats, and count records for one input."""
    schema_info: dict[str, Any] = {}
    samples: list[Row] = []
    statistics: dict[str, dict[str, Any]] = {}
    record_count: int | None = None

    # Schema inference.
    try:
        schema_info = schema.infer(input_obj, detect_constraints=detect_constraints)
    except Exception as exc:
        logger.warning("Schema inference failed: %s", exc)

    # Sampling.
    try:
        plan = sampling.choose_plan(size_bytes, max_rows=sample_size)
        samples = sampling.sample_rows(input_obj, plan)
        if redact_samples and samples and (provider_name or "openai").lower() in _CLOUD_PROVIDERS:
            samples = redact_for_llm(samples)
    except Exception as exc:
        logger.warning("Sampling failed: %s", exc)

    # Statistics.
    if include_statistics:
        try:
            statistics = stats.compute(input_obj, include_top_values=True)
        except Exception as exc:
            logger.warning("Statistics computation failed: %s", exc)

    # Record count.
    try:
        if statistics:
            record_count = max((s.get("count", 0) + s.get("null_count", 0)) for s in statistics.values())
        else:
            record_count = fileinfo.count_records(input_obj)
    except Exception:
        record_count = None

    return {
        "schema": schema_info,
        "samples": samples,
        "statistics": statistics,
        "record_count": record_count,
    }


def _generate_multitable_schema(
    result_blocks: dict[str, Any],
    base_ctx: BlockContext,
    source: str | None,
    table_names: list[str],
    *,
    sample_size: int | None,
    include_statistics: bool,
    detect_constraints: bool,
    redact_samples: bool,
    provider_name: str | None,
) -> None:
    """Generate a separate schema block per selected table."""
    if source is None:
        result_blocks["schema"] = blocks_module.render_block("schema", base_ctx)
        return
    for table in table_names:
        table_iter = fileinfo.open_table(source, table)
        try:
            rows = list(table_iter)
        except Exception as exc:
            logger.warning("Failed to read table %r: %s", table, exc)
            rows = []
        finally:
            if hasattr(table_iter, "close"):
                try:
                    table_iter.close()
                except Exception:
                    pass
        prepared = _prepare_table_context(
            rows,
            size_bytes=None,
            sample_size=sample_size,
            include_statistics=include_statistics,
            detect_constraints=detect_constraints,
            redact_samples=redact_samples,
            provider_name=provider_name,
        )
        table_ctx = BlockContext(
            source=source,
            format=base_ctx.format,
            language=base_ctx.language,
            user_context=base_ctx.user_context,
            file_meta=base_ctx.file_meta,
            schema_info=prepared["schema"],
            samples=prepared["samples"],
            statistics=prepared["statistics"],
            record_count=prepared["record_count"],
            provider=base_ctx.provider,
            model=base_ctx.model,
            temperature=base_ctx.temperature,
            max_tokens=base_ctx.max_tokens,
        )
        block = blocks_module.render_block("schema", table_ctx)
        block["table"] = table
        result_blocks[f"schema:{table}"] = block


def _source_descriptor(
    source: str | None,
    iterable: Any,
    file_meta: dict[str, Any],
    record_count: int | None,
    tables: list[str] | None,
) -> dict[str, Any]:
    desc: dict[str, Any] = {
        "type": "file" if source is not None else "iterable",
        "name": file_meta.get("file_name"),
        "format": file_meta.get("format"),
        "size_bytes": file_meta.get("file_size"),
        "sha256": file_meta.get("file_hash") if file_meta.get("hash_algo") == "sha256" else None,
        "record_count": record_count,
    }
    if tables:
        desc["tables"] = tables
    return desc


def _assemble_markdown(
    ctx: BlockContext,
    result_blocks: dict[str, Any],
    requested: list[str],
    tables: list[str] | None,
) -> str:
    labels = blocks_module.get_labels(ctx.language)
    title = ctx.user_context.get("title")
    if not title:
        general_data = result_blocks.get("general", {}).get("data", {}) if "general" in result_blocks else {}
        title = general_data.get("title") or "Dataset"

    parts: list[str] = [f"# {labels['documentation']}: {title}\n"]

    # Table of contents (localized section titles, anchors matching block headings).
    toc: list[str] = []
    ordered_keys = _ordered_block_keys(result_blocks, requested)
    for key in ordered_keys:
        block = result_blocks.get(key, {})
        if not block.get("markdown"):
            continue
        base_name, _, table = key.partition(":")
        label = blocks_module.section_title(base_name, ctx.language)
        toc_label = f"{label} — {table}" if table else label
        anchor = _slug(label)
        toc.append(f"- [{toc_label}](#{anchor})")
    if toc:
        parts.append(f"## {labels['contents']}\n")
        parts.extend(toc)
        parts.append("")

    for key in ordered_keys:
        block = result_blocks.get(key, {})
        md = block.get("markdown")
        if md:
            parts.append(md)
            parts.append("")
    return "\n".join(parts).strip() + "\n"


def _slug(text: str) -> str:
    """GitHub-style anchor slug: lowercased, spaces to hyphens, punctuation dropped."""
    import re

    slug = text.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def _ordered_block_keys(result_blocks: dict[str, Any], requested: list[str]) -> list[str]:
    ordered: list[str] = []
    for name in requested:
        if name in result_blocks:
            ordered.append(name)
        else:
            # Multi-table schema produces schema:<table> keys.
            ordered.extend(sorted(k for k in result_blocks if k.startswith(f"{name}:")))
    # Append any remaining keys not covered above.
    for key in result_blocks:
        if key not in ordered:
            ordered.append(key)
    return ordered


def _build_documentation_prompt(context: dict[str, Any], language: str = "English") -> str:
    """Build enhanced prompt for documentation generation."""
    prompt_parts = [
        f"Generate comprehensive documentation for a dataset in {language}. Include:",
        "- Dataset overview and purpose",
        "- Field descriptions with types and constraints",
        "- Data quality notes",
        "- Usage examples",
        "",
    ]

    # Tell the model which filename to use in Python/R usage examples (SQL should use table `dataset`)
    if "filename" in context:
        prompt_parts.append(
            f"In Python/R usage examples, read the local file {context['filename']!r}. "
            "In SQL examples, query the table named `dataset` (do not use the filename or "
            "read_parquet/read_csv table functions)."
        )
        prompt_parts.append("")

    # Add user-provided context (title, description, tags, territory, source, card metadata)
    if context.get("user_context"):
        prompt_parts.append("## User-provided context:")
        prompt_parts.append(json.dumps(context["user_context"], indent=2, default=str, ensure_ascii=False))
        prompt_parts.append("")

    # Add metadata if available
    if "metadata" in context:
        metadata_info = context["metadata"]
        prompt_parts.append("## Metadata:")
        if metadata_info.get("keywords"):
            prompt_parts.append(f"Keywords: {', '.join(metadata_info['keywords'][:10])}")
        if metadata_info.get("geographic_coverage"):
            geo = metadata_info["geographic_coverage"]
            if geo.get("countries"):
                prompt_parts.append(f"Countries: {', '.join(geo['countries'][:5])}")
            if geo.get("regions"):
                prompt_parts.append(f"Regions: {', '.join(geo['regions'][:5])}")
        if metadata_info.get("temporal_coverage"):
            temp = metadata_info["temporal_coverage"]
            prompt_parts.append(
                f"Temporal coverage: {temp.get('start')} to {temp.get('end')} ({temp.get('granularity')})"
            )
        if metadata_info.get("data_theme"):
            theme = metadata_info["data_theme"]
            prompt_parts.append(f"Data theme: {theme.get('label')}")
        prompt_parts.append("")

    # Add schema information
    if "schema" in context:
        schema_info = context["schema"]
        prompt_parts.append("## Schema Information:")
        # Truncate schema info to avoid token limits
        schema_str = json.dumps(schema_info, indent=2, default=str)
        if len(schema_str) > 2000:
            schema_str = schema_str[:2000] + "... (truncated)"
        prompt_parts.append(schema_str)
        prompt_parts.append("")

    # Add field descriptions if available
    if "field_descriptions" in context:
        field_descriptions = context["field_descriptions"]
        prompt_parts.append("## Field Descriptions:")
        for field, desc in list(field_descriptions.items())[:20]:  # Limit to 20 fields
            prompt_parts.append(f"- {field}: {desc}")
        prompt_parts.append("")

    # Add statistics if available
    if "statistics" in context:
        stats_info = context["statistics"]
        prompt_parts.append("## Statistics:")
        # Include key statistics for first few fields
        for field_name, field_stats in list(stats_info.items())[:10]:
            if isinstance(field_stats, dict):
                stats_summary = []
                if "unique_count" in field_stats:
                    stats_summary.append(f"unique: {field_stats['unique_count']}")
                if "count" in field_stats:
                    stats_summary.append(f"total: {field_stats['count']}")
                if stats_summary:
                    prompt_parts.append(f"- {field_name}: {', '.join(stats_summary)}")
        prompt_parts.append("")

    # Add semantic types if available
    if "semantic_types" in context:
        semantic_types = context["semantic_types"]
        prompt_parts.append("## Semantic Types:")
        for field_name, types in list(semantic_types.items())[:10]:
            if types:
                type_names = [t.get("type", "") for t in types[:3]]
                prompt_parts.append(f"- {field_name}: {', '.join(type_names)}")
        prompt_parts.append("")

    # Add sample data
    if "samples" in context:
        samples = context["samples"]
        prompt_parts.append("## Sample Data:")
        # Truncate samples to avoid token limits
        samples_str = json.dumps(samples[:5], indent=2, default=str)
        if len(samples_str) > 1500:
            samples_str = samples_str[:1500] + "... (truncated)"
        prompt_parts.append(samples_str)
        prompt_parts.append("")

    prompt_parts.append(
        f"Generate well-formatted markdown documentation in {language} that describes this dataset comprehensively."
    )

    return "\n".join(prompt_parts)


def _format_as_json(
    generated_text: str,
    context: dict[str, Any],
    usage_info: dict[str, Any] | None,
    extracted_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Format documentation as JSON."""
    result: dict[str, Any] = {
        "documentation": generated_text,
        "schema": context.get("schema"),
        "samples": context.get("samples"),
        "usage": usage_info,
    }

    # Add metadata
    if extracted_metadata:
        result["metadata"] = extracted_metadata

    # Add statistics
    if "statistics" in context:
        result["statistics"] = context["statistics"]

    # Add semantic types
    if "semantic_types" in context:
        result["semantic_types"] = context["semantic_types"]

    # Add PII fields
    if "pii_fields" in context:
        result["pii_fields"] = context["pii_fields"]

    # Add field descriptions
    if "field_descriptions" in context:
        result["field_descriptions"] = context["field_descriptions"]

    return result


def _format_as_html(markdown_text: str) -> str:
    """Format markdown documentation as HTML."""
    try:
        import markdown
    except ImportError:
        # Fallback: simple HTML wrapper
        html_content = markdown_text.replace("\n", "<br>\n")
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dataset Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

    html = markdown.markdown(markdown_text, extensions=["fenced_code", "tables"])
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dataset Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""


def _format_as_yaml(
    generated_text: str,
    context: dict[str, Any],
    usage_info: dict[str, Any] | None,
    extracted_metadata: dict[str, Any],
) -> str:
    """Format documentation as YAML."""
    try:
        import yaml
    except ImportError:
        # Fallback: return as JSON string
        result = _format_as_json(generated_text, context, usage_info, extracted_metadata)
        return json.dumps(result, indent=2, default=str)

    result = _format_as_json(generated_text, context, usage_info, extracted_metadata)
    return yaml.dump(result, default_flow_style=False, allow_unicode=True)


def _format_as_text(markdown_text: str) -> str:
    """Format markdown documentation as plain text."""
    # Simple conversion: remove markdown formatting
    text = markdown_text
    # Remove headers
    import re

    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    # Remove code blocks but keep content
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text
