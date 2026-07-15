import glob
import logging
import os
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

from ..helpers.detect import is_flat, open_iterable
from ..helpers.utils import dict_generator, make_flat
from ..types import BulkConversionResult, ConversionResult, FileConversionResult, IterableArgs

DEFAULT_BATCH_SIZE = 50000
DEFAULT_HEADERS_DETECT_LIMIT = 1000
DEFAULT_PROGRESS_INTERVAL = 1000  # Call progress callback every N rows


def _atomic_write(target_file: str, temp_file: str) -> None:
    """
    Atomically rename temporary file to target file using os.replace().

    Args:
        target_file: Path to the final destination file
        temp_file: Path to the temporary file to rename

    Raises:
        OSError: If rename fails (e.g., cross-filesystem rename, permission error)
    """
    try:
        os.replace(temp_file, target_file)
    except OSError as e:
        # Clean up temp file on failure
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass  # Ignore cleanup errors
        raise OSError(
            f"Failed to atomically rename temporary file to '{target_file}': {e}. "
            "Atomic writes only work on the same filesystem. "
            "If source and destination are on different filesystems, use atomic=False."
        ) from e


def _prepare_atomic_target(tofile: str, atomic: bool) -> tuple[str, str | None]:
    """Return the actual write target and temp file path (when atomic)."""
    if not atomic:
        return tofile, None
    temp_file = os.path.join(os.path.dirname(tofile) or ".", os.path.basename(tofile) + ".tmp")
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
        except Exception as e:
            logging.warning(f"Failed to remove existing temporary file '{temp_file}': {e}")
    return temp_file, temp_file


def _close_quietly(it: Any, err_msg: str, errors: list[Exception]) -> None:
    """Close an iterable, logging and recording (not raising) any failure."""
    if it is None:
        return
    try:
        it.close()
    except Exception as e:
        logging.warning(f"{err_msg}: {e}")
        if e not in errors:
            errors.append(e)


@dataclass
class _ConvertMetrics:
    """Mutable metrics shared across the conversion stages."""

    start_time: float
    rows_read: int = 0
    rows_written: int = 0
    bytes_read: int | None = None
    bytes_written: int | None = None
    errors: list[Exception] = field(default_factory=list)


def _progress_estimates(
    metrics: _ConvertMetrics, estimated_total: int | None, elapsed: float
) -> tuple[float | None, float | None]:
    """Compute percent complete and ETA from current metrics, when possible."""
    percent_complete = None
    estimated_time_remaining = None
    if estimated_total is not None and estimated_total > 0:
        percent_complete = (metrics.rows_read / estimated_total) * 100.0
        if elapsed > 0 and metrics.rows_read > 0:
            rate = metrics.rows_read / elapsed
            remaining_rows = estimated_total - metrics.rows_read
            estimated_time_remaining = remaining_rows / rate if rate > 0 else None
    return percent_complete, estimated_time_remaining


def _report_progress(
    progress: Callable[[dict[str, Any]], None] | None,
    metrics: _ConvertMetrics,
    it_in: Any,
    use_totals: bool,
) -> None:
    """Invoke the user progress callback with current metrics, if provided."""
    if progress is None:
        return
    elapsed = time.time() - metrics.start_time
    estimated_total = None
    if use_totals and it_in is not None and it_in.has_totals():
        estimated_total = it_in.totals()

    percent_complete, estimated_time_remaining = _progress_estimates(metrics, estimated_total, elapsed)

    try:
        progress(
            {
                "rows_read": metrics.rows_read,
                "rows_written": metrics.rows_written,
                "elapsed": elapsed,
                "estimated_total": estimated_total,
                "bytes_read": metrics.bytes_read,
                "bytes_written": metrics.bytes_written,
                "percent_complete": percent_complete,
                "estimated_time_remaining": estimated_time_remaining,
            }
        )
    except Exception as e:
        logging.warning(f"Error in progress callback: {e}")


def _safe_reset(it_in: Any) -> None:
    """Reset an iterable, tolerating sources (e.g. databases) that cannot."""
    try:
        it_in.reset()
    except NotImplementedError:
        pass


def _scan_schema_keys(it_in: Any, scan_limit: int | None, is_flatten: bool, silent: bool) -> set[str]:
    """Scan up to ``scan_limit`` rows to collect the flat output key set."""
    keys: set[str] = set()
    n = 0
    it = tqdm(it_in, total=scan_limit, desc="Schema analysis") if not silent else it_in
    for item in it:
        if scan_limit is not None and n >= scan_limit:
            break
        n += 1
        if not is_flatten:
            for i in dict_generator(item):
                keys.add(".".join(i[:-1]))
        else:
            keys.update(make_flat(item).keys())
    return keys


def _build_output_args(
    tofile: str, actual_tofile: str, is_flat_output: bool, keys: list[str], toiterableargs: IterableArgs
) -> dict[str, Any]:
    """Merge auto-detected schema keys and explicit format into output args."""
    if is_flat_output:
        args: dict[str, Any] = {"keys": keys}
        args.update(toiterableargs)
    else:
        args = dict(toiterableargs)
    # When atomic, actual_tofile has a .tmp extension; carry the real format.
    if actual_tofile != tofile and "format" not in args:
        out_ext = (tofile.lower().rsplit(".", 1)[-1] if "." in tofile else None) or ""
        if out_ext:
            args = {**args, "format": out_ext}
    return args


def _wrap_progress_iter(it_in: Any, use_totals: bool, should_show_progress: bool) -> Iterable[Any]:
    """Wrap the source iterable with a tqdm bar when totals/progress apply."""
    if use_totals and it_in.has_totals():
        totals = it_in.totals()
        if totals is not None and totals > 0:
            logging.debug(f"Total rows: {totals}")
            _safe_reset(it_in)
            return tqdm(it_in, total=totals, desc="Converting") if should_show_progress else it_in
        _safe_reset(it_in)
    return tqdm(it_in, desc="Converting") if should_show_progress else it_in


def _flush_batch(it_out: Any, batch: list[Any], metrics: _ConvertMetrics, err_msg: str) -> None:
    """Write one batch, recording any write error without aborting."""
    try:
        it_out.write_bulk(batch)
        metrics.rows_written += len(batch)
    except Exception as e:
        metrics.errors.append(e)
        logging.error(f"{err_msg}: {e}")


def _run_write_loop(
    it: Iterable[Any],
    it_out: Any,
    keys: list[str],
    *,
    is_flatten: bool,
    batch_size: int,
    progress_interval: int,
    metrics: _ConvertMetrics,
    it_in: Any,
    use_totals: bool,
    progress: Callable[[dict[str, Any]], None] | None,
) -> None:
    """Read rows in batches and write them to the destination iterable."""
    batch: list[Any] = []
    n = 0
    for row in it:
        n += 1
        metrics.rows_read = n
        if is_flatten:
            for k in keys:
                if k not in row:
                    row[k] = None
            batch.append(make_flat(row))
        else:
            batch.append(row)

        if n % batch_size == 0:
            _flush_batch(it_out, batch, metrics, "Error writing batch")
            batch = []

        if n % progress_interval == 0:
            _report_progress(progress, metrics, it_in, use_totals)

    if batch:
        _flush_batch(it_out, batch, metrics, "Error writing final batch")

    metrics.rows_read = n


def _validate_convert_args(scan_limit: int | None, batch_size: int) -> None:
    """Validate user-facing convert() numeric arguments."""
    if scan_limit is not None and scan_limit < 0:
        raise ValueError(f"scan_limit must be non-negative, got {scan_limit}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")


def _resolve_schema_keys(
    it_in: Any,
    reopen_source: Callable[[], Any],
    scan_limit: int | None,
    is_flatten: bool,
    silent: bool,
) -> tuple[Any, list[str]]:
    """Scan the source for flat output keys, resetting or reopening it after.

    Returns the (possibly reopened) source iterable and the sorted key list.
    """
    if not silent:
        logging.debug("Extracting schema")
    key_set = _scan_schema_keys(it_in, scan_limit, is_flatten, silent)
    try:
        it_in.reset()
    except NotImplementedError:
        # Database sources cannot reset; the schema scan consumed the
        # iterator, so recreate it for the real conversion pass.
        if not silent:
            logging.debug("Database source doesn't support reset - recreating iterator")
        it_in.close()
        it_in = reopen_source()
    return it_in, sorted(key_set)


def _finalize_atomic_write(tofile: str, temp_file: str | None, metrics: _ConvertMetrics) -> None:
    """Atomically move the temp file into place (no-op when not atomic)."""
    if temp_file is None or not os.path.exists(temp_file):
        return
    try:
        _atomic_write(tofile, temp_file)
    except Exception as e:
        metrics.errors.append(e)
        logging.error(f"Failed to atomically rename temporary file: {e}")
        raise


def _cleanup_temp_file(temp_file: str | None) -> None:
    """Remove a leftover atomic temp file, tolerating failures."""
    if temp_file is None or not os.path.exists(temp_file):
        return
    try:
        os.remove(temp_file)
    except Exception as cleanup_error:
        logging.warning(f"Failed to clean up temporary file '{temp_file}': {cleanup_error}")


def convert(
    fromfile: str,
    tofile: str,
    iterableargs: IterableArgs | None = None,
    toiterableargs: IterableArgs | None = None,
    scan_limit: int = DEFAULT_HEADERS_DETECT_LIMIT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    silent: bool = True,
    is_flatten: bool = False,
    use_totals: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
    progress_interval: int = DEFAULT_PROGRESS_INTERVAL,
    show_progress: bool = False,
    atomic: bool = False,
) -> ConversionResult:
    """
    Convert data between different file formats or from database sources to files.

    Args:
        fromfile: Path to the source file, or database connection string/URL
        tofile: Path to the destination file
        iterableargs: Format-specific arguments for reading the source file
                     (e.g., {'delimiter': ';', 'encoding': 'utf-8'}).
                     For database sources, include 'engine' (e.g., 'postgres', 'mongo')
                     and database-specific parameters (e.g., 'query', 'database', 'collection').
        toiterableargs: Format-specific arguments for writing the destination file
                       (e.g., {'delimiter': '|', 'quotechar': "'", 'page': 0})
        scan_limit: Number of records to scan for schema detection (for flat formats)
        batch_size: Number of records to process in each batch
        silent: If False, shows progress bars during conversion
        is_flatten: If True, flattens nested structures when converting to flat formats
        use_totals: If True, uses total count for progress tracking (if available)
        progress: Optional callback function that receives progress stats dictionary
                 with keys: rows_read, rows_written, elapsed, estimated_total,
                 bytes_read, bytes_written, percent_complete, estimated_time_remaining
        progress_interval: Number of rows between progress callback invocations.
                          Default: 1000. Set to smaller value for more frequent updates,
                          or larger value to reduce callback overhead.
        show_progress: If True, displays a progress bar using tqdm (if available).
                      Ignored if silent=True.
        atomic: If True, write to a temporary file and atomically rename to destination
                upon successful completion. This ensures output files are never left in
                a partially written state. Default: False.

    Returns:
        ConversionResult: Object containing conversion metrics (rows_in, rows_out,
                         elapsed_seconds, bytes_read, bytes_written, errors)

    Raises:
        FileNotFoundError: If source file doesn't exist
        ValueError: If scan_limit or batch_size are invalid
        OSError: If atomic write fails (e.g., cross-filesystem rename)
        Exception: Various exceptions from file I/O operations

    Examples:
        # Convert CSV with custom output delimiter
        convert('input.csv', 'output.csv',
                toiterableargs={'delimiter': '|', 'quotechar': "'"})

        # Convert with progress callback
        def cb(stats):
            print(f"Progress: {stats['rows_read']} rows read")

        result = convert('input.jsonl', 'output.parquet', progress=cb)

        # Convert with progress bar
        result = convert('input.csv', 'output.parquet', show_progress=True)
        print(f"Converted {result.rows_out} rows in {result.elapsed_seconds:.2f}s")

        # Convert with atomic writes for production safety
        result = convert('input.csv', 'output.parquet', atomic=True)

        # Convert from PostgreSQL database to Parquet
        result = convert(
            'postgresql://user:pass@host:5432/dbname',
            'output.parquet',
            iterableargs={'engine': 'postgres', 'query': 'SELECT * FROM users'}
        )
    """
    iterableargs = iterableargs or {}
    toiterableargs = toiterableargs or {}
    _validate_convert_args(scan_limit, batch_size)

    metrics = _ConvertMetrics(start_time=time.time())
    should_show_progress = show_progress and not silent and TQDM_AVAILABLE

    actual_tofile, temp_file = _prepare_atomic_target(tofile, atomic)

    it_in = None
    it_out = None

    source_iterableargs = dict(iterableargs)
    source_engine = source_iterableargs.pop("engine", "internal")

    def reopen_source() -> Any:
        return open_iterable(fromfile, mode="r", engine=source_engine, iterableargs=source_iterableargs)

    try:
        it_in = reopen_source()
        is_flat_output = is_flat(tofile)

        keys: list[str] = []
        if is_flat_output:
            it_in, keys = _resolve_schema_keys(it_in, reopen_source, scan_limit, is_flatten, silent)

        args = _build_output_args(tofile, actual_tofile, is_flat_output, keys, toiterableargs)
        it_out = open_iterable(actual_tofile, mode="w", iterableargs=args)

        logging.debug("Converting data")
        it = _wrap_progress_iter(it_in, use_totals, should_show_progress)

        _run_write_loop(
            it,
            it_out,
            keys,
            is_flatten=is_flatten,
            batch_size=batch_size,
            progress_interval=progress_interval,
            metrics=metrics,
            it_in=it_in,
            use_totals=use_totals,
            progress=progress,
        )

        _report_progress(progress, metrics, it_in, use_totals)
        _finalize_atomic_write(tofile, temp_file, metrics)

    except Exception as e:
        metrics.errors.append(e)
        _cleanup_temp_file(temp_file)
        raise
    finally:
        _close_quietly(it_in, "Error closing input file", metrics.errors)
        _close_quietly(it_out, "Error closing output file", metrics.errors)

    return ConversionResult(
        rows_in=metrics.rows_read,
        rows_out=metrics.rows_written,
        elapsed_seconds=time.time() - metrics.start_time,
        bytes_read=metrics.bytes_read,
        bytes_written=metrics.bytes_written,
        errors=metrics.errors,
    )


def _discover_files(source: str) -> list[str]:
    """
    Discover files from source path (glob pattern, directory, or single file).

    Args:
        source: Glob pattern, directory path, or single file path

    Returns:
        List of file paths to process
    """
    source_path = Path(source)

    # Check if it's a single file
    if source_path.is_file():
        return [str(source_path)]

    # Check if it's a directory
    if source_path.is_dir():
        # Find all files in directory (non-recursive)
        files = []
        for item in source_path.iterdir():
            if item.is_file():
                files.append(str(item))
        return sorted(files)

    # Try glob pattern
    matches = glob.glob(source, recursive=False)
    if matches:
        # Filter to only files (not directories)
        files = [f for f in matches if Path(f).is_file()]
        return sorted(files)

    # If nothing found, return empty list
    return []


def _generate_output_filename(
    source_file: str, dest_dir: str, pattern: str | None = None, to_ext: str | None = None
) -> str:
    """
    Generate output filename from source file using pattern or extension.

    Args:
        source_file: Path to source file
        dest_dir: Output directory path
        pattern: Filename pattern (e.g., '{name}.parquet') or None
        to_ext: Target extension (e.g., 'parquet') or None

    Returns:
        Full path to output file
    """
    source_path = Path(source_file)
    dest_path = Path(dest_dir)

    if pattern:
        # Use pattern to generate filename
        # Extract components from source file
        name = source_path.name  # Full filename with extension

        # Calculate base name (without any extensions)
        base_name = source_path.name
        for suffix in source_path.suffixes:
            base_name = base_name.removesuffix(suffix)
        stem = base_name

        # Get all extensions as one string (e.g., ".csv.gz" -> "csv.gz")
        ext = "".join(source_path.suffixes).lstrip(".")

        # Replace placeholders in pattern
        output_name = pattern.format(name=name, stem=stem, ext=ext)
        return str(dest_path / output_name)
    elif to_ext:
        # Use to_ext to replace extension
        # Remove all extensions and add new one
        base_name = source_path.name
        for suffix in source_path.suffixes:
            base_name = base_name.removesuffix(suffix)

        # Add new extension (with dot)
        new_ext = to_ext if to_ext.startswith(".") else f".{to_ext}"
        output_name = f"{base_name}{new_ext}"
        return str(dest_path / output_name)
    else:
        # No pattern or extension specified, keep original name
        return str(dest_path / source_path.name)


def _convert_file_worker(
    file_info: tuple[str, str, dict[str, Any]],
) -> tuple[str, ConversionResult | None, Exception | None]:
    """Convert single file (for parallel execution).

    This is a worker function designed to be called by ThreadPoolExecutor.
    It wraps the convert() function call with proper error handling.

    Args:
        file_info: Tuple of (source_file, dest_file, kwargs)

    Returns:
        Tuple of (source_file, result, error)
    """
    source_file, dest_file, kwargs = file_info
    try:
        result = convert(fromfile=source_file, tofile=dest_file, **kwargs)
        return (source_file, result, None)
    except Exception as e:
        return (source_file, None, e)


@dataclass
class _BulkMetrics:
    """Aggregated metrics across a bulk conversion run."""

    start_time: float
    total_files: int = 0
    total_rows_in: int = 0
    total_rows_out: int = 0
    successful_files: int = 0
    failed_files: int = 0
    file_results: list[FileConversionResult] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)


def _record_file_result(
    metrics: _BulkMetrics,
    source_file: str,
    dest_file: str,
    result: ConversionResult | None,
    error: Exception | None,
) -> None:
    """Record a single per-file outcome into aggregated metrics."""
    if error is not None:
        metrics.failed_files += 1
        metrics.errors.append(error)
        logging.error(f"Error converting {source_file}: {error}")
    elif result is not None:
        metrics.total_rows_in += result.rows_in
        metrics.total_rows_out += result.rows_out
        metrics.successful_files += 1
        if result.errors:
            metrics.errors.extend(result.errors)
    metrics.file_results.append(
        FileConversionResult(source_file=source_file, dest_file=dest_file, result=result, error=error)
    )


def _build_convert_kwargs(
    iterableargs: IterableArgs | None,
    toiterableargs: IterableArgs | None,
    scan_limit: int,
    batch_size: int,
    is_flatten: bool,
    use_totals: bool,
    progress_interval: int,
    atomic: bool,
) -> dict[str, Any]:
    """Build the per-file kwargs shared by all bulk conversion tasks."""
    return {
        "iterableargs": iterableargs,
        "toiterableargs": toiterableargs,
        "scan_limit": scan_limit,
        "batch_size": batch_size,
        "silent": True,  # Per-file progress is handled at the bulk level
        "is_flatten": is_flatten,
        "use_totals": use_totals,
        "progress": None,
        "progress_interval": progress_interval,
        "show_progress": False,
        "atomic": atomic,
    }


def _invoke_bulk_progress(
    progress: Callable[[dict[str, Any]], None] | None,
    metrics: _BulkMetrics,
    source_file: str,
    result: ConversionResult | None,
) -> None:
    """Invoke the bulk-level progress callback after a file completes."""
    if progress is None or result is None:
        return
    try:
        progress(
            {
                "file_index": metrics.successful_files + metrics.failed_files,
                "total_files": metrics.total_files,
                "current_file": source_file,
                "file_rows_read": result.rows_in,
                "file_rows_written": result.rows_out,
                "rows_read": metrics.total_rows_in,
                "rows_written": metrics.total_rows_out,
                "elapsed": time.time() - metrics.start_time,
            }
        )
    except Exception as e:
        logging.warning(f"Error in progress callback: {e}")


def _run_parallel_bulk(
    tasks: list[tuple[str, str, dict[str, Any]]],
    dest_files: dict[str, str],
    workers: int,
    should_show_progress: bool,
    metrics: _BulkMetrics,
    progress: Callable[[dict[str, Any]], None] | None,
) -> None:
    """Convert files concurrently with a thread pool, aggregating results."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_convert_file_worker, task): task[0] for task in tasks}
        file_iterator = tqdm(futures, desc="Converting files", total=len(tasks)) if should_show_progress else futures
        for future in as_completed(file_iterator):
            source_file, result, error = future.result()
            _record_file_result(metrics, source_file, dest_files[source_file], result, error)
            if error is None:
                _invoke_bulk_progress(progress, metrics, source_file, result)


def _make_file_progress(
    progress: Callable[[dict[str, Any]], None], file_idx: int, total: int, src: str
) -> Callable[[dict[str, Any]], None]:
    """Wrap a bulk progress callback with per-file conversion context."""

    def file_progress_callback(stats: dict[str, Any]) -> None:
        progress(
            {
                **stats,
                "file_index": file_idx,
                "total_files": total,
                "current_file": src,
                "file_rows_read": stats.get("rows_read", 0),
                "file_rows_written": stats.get("rows_written", 0),
            }
        )

    return file_progress_callback


def _run_sequential_bulk(
    tasks: list[tuple[str, str, dict[str, Any]]],
    should_show_progress: bool,
    metrics: _BulkMetrics,
    progress: Callable[[dict[str, Any]], None] | None,
    silent: bool,
) -> None:
    """Convert files one by one, aggregating results."""
    file_iterator = tqdm(tasks, desc="Converting files") if should_show_progress else tasks
    for file_index, (source_file, dest_file, kwargs) in enumerate(file_iterator, 1):
        file_progress: Callable[[dict[str, Any]], None] | None = None
        if progress is not None:
            file_progress = _make_file_progress(progress, file_index, metrics.total_files, source_file)
        try:
            result = convert(
                fromfile=source_file,
                tofile=dest_file,
                **{**kwargs, "silent": silent, "progress": file_progress},
            )
            _record_file_result(metrics, source_file, dest_file, result, None)
        except Exception as e:
            _record_file_result(metrics, source_file, dest_file, None, e)


def _ensure_dest_dir(dest: str) -> None:
    """Create the destination directory, failing if it exists as a file."""
    dest_path = Path(dest)
    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
    elif not dest_path.is_dir():
        raise ValueError(f"Destination path '{dest}' exists but is not a directory")


def _resolve_workers(workers: int | None) -> int:
    """Pick a worker count; I/O-bound work needs only a small pool."""
    if workers is None:
        return min(4, os.cpu_count() or 1)
    return workers


def bulk_convert(
    source: str,
    dest: str,
    pattern: str | None = None,
    to_ext: str | None = None,
    iterableargs: IterableArgs | None = None,
    toiterableargs: IterableArgs | None = None,
    scan_limit: int = DEFAULT_HEADERS_DETECT_LIMIT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    silent: bool = True,
    is_flatten: bool = False,
    use_totals: bool = False,
    progress: Callable[[dict[str, Any]], None] | None = None,
    progress_interval: int = DEFAULT_PROGRESS_INTERVAL,
    show_progress: bool = False,
    atomic: bool = False,
    parallel: bool = False,
    workers: int | None = None,
) -> BulkConversionResult:
    """
    Convert multiple files using glob patterns, directory paths, or file lists.

    This function discovers files from the source path (glob pattern, directory, or single file),
    converts each file using the existing `convert()` function, and aggregates results.

    Args:
        source: Glob pattern (e.g., 'data/raw/*.csv.gz'), directory path, or single file path
        dest: Output directory path where converted files will be written
        pattern: Filename pattern for output files (e.g., '{name}.parquet').
                Supports placeholders: {name} (full filename), {stem} (name without extension),
                {ext} (extension). If None, uses to_ext or keeps original name.
        to_ext: Target file extension (e.g., 'parquet'). Used if pattern is None.
                Extension replacement removes all existing extensions and adds the new one.
        iterableargs: Format-specific arguments for reading source files
        toiterableargs: Format-specific arguments for writing destination files
        scan_limit: Number of records to scan for schema detection (for flat formats)
        batch_size: Number of records to process in each batch
        silent: If False, shows progress bars during conversion
        is_flatten: If True, flattens nested structures when converting to flat formats
        use_totals: If True, uses total count for progress tracking (if available)
        progress: Optional callback function that receives progress stats dictionary.
                 For bulk conversion, callback receives additional keys: 'file_index',
                 'total_files', 'current_file', 'file_rows_read', 'file_rows_written'
        progress_interval: Number of rows between progress callback invocations.
                          Default: 1000. Passed to convert() for each file conversion.
        show_progress: If True, displays a progress bar using tqdm (if available).
                      Ignored if silent=True.
        atomic: If True, each file conversion uses atomic writes. Default: False.
        parallel: If True, enable parallel file conversion using threading.
                 Recommended for I/O-bound operations. Default: False.
        workers: Number of worker threads for parallel conversion.
                If None, uses min(4, CPU count). Default: None.

    Returns:
        BulkConversionResult: Object containing aggregated metrics and per-file results

    Raises:
        ValueError: If both pattern and to_ext are None, or if dest is not a directory
        OSError: If output directory cannot be created

    Examples:
        # Convert all CSV files matching glob pattern
        result = bulk_convert('data/raw/*.csv.gz', 'data/processed/', to_ext='parquet')

        # Convert with custom filename pattern
        result = bulk_convert('data/*.csv', 'output/', pattern='{name}.parquet')

        # Convert entire directory
        result = bulk_convert('data/raw/', 'data/processed/', to_ext='parquet')

        # Convert with all convert() parameters
        result = bulk_convert(
            'data/*.jsonl',
            'output/',
            to_ext='parquet',
            batch_size=10000,
            is_flatten=True
        )

        # Convert with atomic writes for production safety
        result = bulk_convert('data/*.csv', 'output/', to_ext='parquet', atomic=True)
    """
    if pattern is None and to_ext is None:
        raise ValueError("Either 'pattern' or 'to_ext' must be specified")

    source_files = _discover_files(source)
    if not source_files:
        logging.warning(f"No files found matching source: {source}")
        return BulkConversionResult(
            total_files=0,
            successful_files=0,
            failed_files=0,
            total_rows_in=0,
            total_rows_out=0,
            total_elapsed_seconds=0.0,
            file_results=[],
            errors=[],
        )

    _ensure_dest_dir(dest)

    metrics = _BulkMetrics(start_time=time.time(), total_files=len(source_files))
    should_show_progress = show_progress and not silent and TQDM_AVAILABLE

    convert_kwargs = _build_convert_kwargs(
        iterableargs, toiterableargs, scan_limit, batch_size, is_flatten, use_totals, progress_interval, atomic
    )
    dest_files = {f: _generate_output_filename(f, dest, pattern, to_ext) for f in source_files}
    tasks = [(f, dest_files[f], convert_kwargs) for f in source_files]

    if parallel:
        workers = _resolve_workers(workers)
        logging.debug(f"Parallel conversion enabled with {workers} workers")
        _run_parallel_bulk(tasks, dest_files, workers, should_show_progress, metrics, progress)
    else:
        _run_sequential_bulk(tasks, should_show_progress, metrics, progress, silent)

    return BulkConversionResult(
        total_files=len(source_files),
        successful_files=metrics.successful_files,
        failed_files=metrics.failed_files,
        total_rows_in=metrics.total_rows_in,
        total_rows_out=metrics.total_rows_out,
        total_elapsed_seconds=time.time() - metrics.start_time,
        file_results=metrics.file_results,
        errors=metrics.errors,
    )
