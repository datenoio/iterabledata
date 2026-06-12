import glob
import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    if iterableargs is None:
        iterableargs = {}
    if toiterableargs is None:
        toiterableargs = {}

    # Input validation
    if scan_limit is not None and scan_limit < 0:
        raise ValueError(f"scan_limit must be non-negative, got {scan_limit}")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")

    # Initialize metrics tracking
    start_time = time.time()
    rows_read = 0
    rows_written = 0
    errors: list[Exception] = []
    bytes_read: int | None = None
    bytes_written: int | None = None

    # Determine if we should show progress bar
    should_show_progress = show_progress and not silent and TQDM_AVAILABLE

    # Determine actual output file (may be temporary if atomic=True)
    actual_tofile = tofile
    temp_file: str | None = None
    if atomic:
        # Generate temporary filename by appending .tmp
        temp_file = os.path.join(os.path.dirname(tofile) or ".", os.path.basename(tofile) + ".tmp")
        actual_tofile = temp_file
        # Clean up any existing temp file
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                logging.warning(f"Failed to remove existing temporary file '{temp_file}': {e}")

    it_in = None
    it_out = None

    def invoke_progress_callback():
        """Invoke progress callback if provided."""
        if progress is not None:
            elapsed = time.time() - start_time
            estimated_total = None
            if use_totals and it_in is not None and it_in.has_totals():
                estimated_total = it_in.totals()

            # Calculate enhanced stats
            percent_complete = None
            estimated_time_remaining = None
            if estimated_total is not None and estimated_total > 0:
                percent_complete = (rows_read / estimated_total) * 100.0
                if elapsed > 0 and rows_read > 0:
                    rate = rows_read / elapsed
                    remaining_rows = estimated_total - rows_read
                    estimated_time_remaining = remaining_rows / rate if rate > 0 else None

            try:
                progress(
                    {
                        "rows_read": rows_read,
                        "rows_written": rows_written,
                        "elapsed": elapsed,
                        "estimated_total": estimated_total,
                        "bytes_read": bytes_read,
                        "bytes_written": bytes_written,
                        "percent_complete": percent_complete,
                        "estimated_time_remaining": estimated_time_remaining,
                    }
                )
            except Exception as e:
                logging.warning(f"Error in progress callback: {e}")

    try:
        # Extract engine from iterableargs if present (for database sources)
        # Make a copy to avoid modifying the original dict
        source_iterableargs = iterableargs.copy() if iterableargs else {}
        source_engine = source_iterableargs.pop("engine", "internal")

        # Open source iterable (may be file or database)
        it_in = open_iterable(fromfile, mode="r", engine=source_engine, iterableargs=source_iterableargs)
        keys = set()  # Use set for O(1) lookups instead of O(n) with list
        n = 0
        is_flat_output = is_flat(tofile)

        # Schema extraction for flat output formats
        if is_flat_output:
            if not silent:
                logging.debug("Extracting schema")
            it = tqdm(it_in, total=scan_limit, desc="Schema analysis") if not silent else it_in
            for item in it:
                if scan_limit is not None and n >= scan_limit:
                    break
                n += 1
                if not is_flatten:
                    dk = dict_generator(item)
                    for i in dk:
                        k = ".".join(i[:-1])
                        keys.add(k)
                else:
                    item = make_flat(item)
                    keys.update(item.keys())

            # Reset after schema extraction (moved outside the loop - was a critical bug)
            # Note: Database sources don't support reset, so we skip it for them
            try:
                it_in.reset()
            except NotImplementedError:
                # Database sources don't support reset - this is expected
                # For database sources, schema extraction consumes the iterator
                # We'll need to recreate the iterator for the actual conversion
                if not silent:
                    logging.debug("Database source doesn't support reset - recreating iterator")
                # Close and recreate the source iterable
                it_in.close()
                it_in = open_iterable(fromfile, mode="r", engine=source_engine, iterableargs=source_iterableargs)
            keys = sorted(keys)  # Convert to sorted list for consistent ordering

        # Prepare output iterable arguments
        # Merge auto-generated args (like 'keys' for flat formats) with user-provided args
        if is_flat_output:
            args = {"keys": keys}
            # Merge user-provided args (user args can override 'keys' if needed, though not recommended)
            args.update(toiterableargs)
        else:
            args = toiterableargs.copy()
        # When atomic, actual_tofile has .tmp extension; pass format from final path so open_iterable can open it
        if actual_tofile != tofile and "format" not in args:
            out_ext = (tofile.lower().rsplit(".", 1)[-1] if "." in tofile else None) or ""
            if out_ext:
                args = {**args, "format": out_ext}
        it_out = open_iterable(actual_tofile, mode="w", iterableargs=args)

        logging.debug("Converting data")
        n = 0

        # Setup progress tracking
        if use_totals and it_in.has_totals():
            totals = it_in.totals()
            if totals is not None and totals > 0:
                logging.debug(f"Total rows: {totals}")
                try:
                    it_in.reset()
                except NotImplementedError:
                    # Database sources don't support reset - skip it
                    pass
                it = tqdm(it_in, total=totals, desc="Converting") if should_show_progress else it_in
            else:
                # Fallback if totals() returns None or invalid value
                try:
                    it_in.reset()
                except NotImplementedError:
                    # Database sources don't support reset - skip it
                    pass
                it = tqdm(it_in, desc="Converting") if should_show_progress else it_in
        else:
            it = tqdm(it_in, desc="Converting") if should_show_progress else it_in

        # Try to get file size for bytes tracking
        try:
            if hasattr(it_in, "file") and hasattr(it_in.file, "tell"):
                # For file-based iterables, we might be able to track bytes
                pass  # Will implement if needed
        except Exception:
            pass

        # Process data in batches
        batch = []
        for row in it:
            n += 1
            rows_read = n  # Update rows_read for each row processed
            if is_flatten:
                # Ensure all keys are present (fill missing with None)
                for k in keys:
                    if k not in row:
                        row[k] = None
                batch.append(make_flat(row))
            else:
                batch.append(row)

            if n % batch_size == 0:
                try:
                    it_out.write_bulk(batch)
                    rows_written += len(batch)
                except Exception as e:
                    errors.append(e)
                    logging.error(f"Error writing batch: {e}")
                batch = []

            # Invoke progress callback periodically
            if n % progress_interval == 0:
                invoke_progress_callback()

        # Write remaining batch
        if len(batch) > 0:
            try:
                it_out.write_bulk(batch)
                rows_written += len(batch)
            except Exception as e:
                errors.append(e)
                logging.error(f"Error writing final batch: {e}")

        # Update final rows_read count
        rows_read = n

        # Final progress callback
        invoke_progress_callback()

        # Perform atomic rename if atomic writes are enabled
        if atomic and temp_file is not None and os.path.exists(temp_file):
            try:
                _atomic_write(tofile, temp_file)
            except Exception as e:
                errors.append(e)
                logging.error(f"Failed to atomically rename temporary file: {e}")
                raise

    except Exception as e:
        errors.append(e)
        # Clean up temporary file on error
        if atomic and temp_file is not None and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as cleanup_error:
                logging.warning(f"Failed to clean up temporary file '{temp_file}': {cleanup_error}")
        raise
    finally:
        # Ensure resources are always cleaned up, even if an error occurs
        if it_in is not None:
            try:
                it_in.close()
            except Exception as e:
                logging.warning(f"Error closing input file: {e}")
                if e not in errors:
                    errors.append(e)
        if it_out is not None:
            try:
                it_out.close()
            except Exception as e:
                logging.warning(f"Error closing output file: {e}")
                if e not in errors:
                    errors.append(e)

    # Calculate final metrics
    elapsed_seconds = time.time() - start_time

    return ConversionResult(
        rows_in=rows_read,
        rows_out=rows_written,
        elapsed_seconds=elapsed_seconds,
        bytes_read=bytes_read,
        bytes_written=bytes_written,
        errors=errors,
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

    # Discover files to convert
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

    # Ensure output directory exists
    dest_path = Path(dest)
    if not dest_path.exists():
        dest_path.mkdir(parents=True, exist_ok=True)
    elif not dest_path.is_dir():
        raise ValueError(f"Destination path '{dest}' exists but is not a directory")

    # Initialize aggregated metrics
    start_time = time.time()
    total_rows_in = 0
    total_rows_out = 0
    successful_files = 0
    failed_files = 0
    file_results: list[FileConversionResult] = []
    all_errors: list[Exception] = []

    # Determine if we should show progress bar
    should_show_progress = show_progress and not silent and TQDM_AVAILABLE

    # Determine number of workers for parallel processing
    if parallel:
        if workers is None:
            # Default to min(4, CPU count) for I/O-bound operations
            cpu_count = os.cpu_count() or 1
            workers = min(4, cpu_count)
        logging.debug(f"Parallel conversion enabled with {workers} workers")

    # Prepare file conversion tasks
    tasks = []
    for source_file in source_files:
        dest_file = _generate_output_filename(source_file, dest, pattern, to_ext)
        tasks.append(
            (
                source_file,
                dest_file,
                {
                    "iterableargs": iterableargs,
                    "toiterableargs": toiterableargs,
                    "scan_limit": scan_limit,
                    "batch_size": batch_size,
                    "silent": True,  # Don't show per-file progress in parallel mode
                    "is_flatten": is_flatten,
                    "use_totals": use_totals,
                    "progress": None,  # Progress callbacks handled separately in parallel mode
                    "progress_interval": progress_interval,
                    "show_progress": False,
                    "atomic": atomic,
                },
            )
        )

    # Process files in parallel or sequentially
    if parallel:
        # Parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all conversion tasks
            futures = {executor.submit(_convert_file_worker, task): task[0] for task in tasks}

            # Process completed conversions
            file_iterator = (
                tqdm(futures, desc="Converting files", total=len(tasks)) if should_show_progress else futures
            )

            for future in as_completed(file_iterator):
                source_file, result, error = future.result()

                if error:
                    # File conversion failed
                    failed_files += 1
                    all_errors.append(error)
                    logging.error(f"Error converting {source_file}: {error}")

                    file_results.append(
                        FileConversionResult(
                            source_file=source_file,
                            dest_file=_generate_output_filename(source_file, dest, pattern, to_ext),
                            result=None,
                            error=error,
                        )
                    )
                else:
                    # File conversion succeeded
                    if result:
                        total_rows_in += result.rows_in
                        total_rows_out += result.rows_out
                        successful_files += 1
                        if result.errors:
                            all_errors.extend(result.errors)

                    file_results.append(
                        FileConversionResult(
                            source_file=source_file,
                            dest_file=_generate_output_filename(source_file, dest, pattern, to_ext),
                            result=result,
                            error=None,
                        )
                    )

                    # Invoke progress callback if provided
                    if progress is not None and result:
                        try:
                            progress(
                                {
                                    "file_index": successful_files + failed_files,
                                    "total_files": len(source_files),
                                    "current_file": source_file,
                                    "file_rows_read": result.rows_in,
                                    "file_rows_written": result.rows_out,
                                    "rows_read": total_rows_in,
                                    "rows_written": total_rows_out,
                                    "elapsed": time.time() - start_time,
                                }
                            )
                        except Exception as e:
                            logging.warning(f"Error in progress callback: {e}")
    else:
        # Sequential processing (existing code)
        file_iterator = tqdm(source_files, desc="Converting files") if should_show_progress else source_files

        for file_index, source_file in enumerate(file_iterator, 1):
            try:
                # Generate output filename
                dest_file = _generate_output_filename(source_file, dest, pattern, to_ext)

                # Create per-file progress callback wrapper if needed
                file_progress: Callable[[dict[str, Any]], None] | None = None
                if progress is not None:

                    def make_file_progress(file_idx: int, total: int, src: str) -> Callable[[dict[str, Any]], None]:
                        def file_progress_callback(stats: dict[str, Any]) -> None:
                            # Add bulk conversion context to progress stats
                            bulk_stats = {
                                **stats,
                                "file_index": file_idx,
                                "total_files": total,
                                "current_file": src,
                                "file_rows_read": stats.get("rows_read", 0),
                                "file_rows_written": stats.get("rows_written", 0),
                            }
                            progress(bulk_stats)

                        return file_progress_callback

                    file_progress = make_file_progress(file_index, len(source_files), source_file)

                # Convert the file
                result = convert(
                    fromfile=source_file,
                    tofile=dest_file,
                    iterableargs=iterableargs,
                    toiterableargs=toiterableargs,
                    scan_limit=scan_limit,
                    batch_size=batch_size,
                    silent=silent,
                    is_flatten=is_flatten,
                    use_totals=use_totals,
                    progress=file_progress,
                    progress_interval=progress_interval,
                    show_progress=False,  # Don't show per-file progress bars in bulk mode
                    atomic=atomic,
                )

                # Aggregate metrics
                total_rows_in += result.rows_in
                total_rows_out += result.rows_out
                successful_files += 1
                if result.errors:
                    all_errors.extend(result.errors)

                file_results.append(
                    FileConversionResult(
                        source_file=source_file,
                        dest_file=dest_file,
                        result=result,
                        error=None,
                    )
                )

            except Exception as e:
                # File conversion failed, but continue with others
                failed_files += 1
                all_errors.append(e)
                logging.error(f"Error converting {source_file}: {e}")

                file_results.append(
                    FileConversionResult(
                        source_file=source_file,
                        dest_file=_generate_output_filename(source_file, dest, pattern, to_ext),
                        result=None,
                        error=e,
                    )
                )

    # Calculate total elapsed time
    total_elapsed_seconds = time.time() - start_time

    return BulkConversionResult(
        total_files=len(source_files),
        successful_files=successful_files,
        failed_files=failed_files,
        total_rows_in=total_rows_in,
        total_rows_out=total_rows_out,
        total_elapsed_seconds=total_elapsed_seconds,
        file_results=file_results,
        errors=all_errors,
    )
