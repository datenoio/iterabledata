import logging
import os
import time
from collections.abc import Callable
from typing import Any

from ..base import BaseFileIterable, BaseIterable
from ..helpers.debug import is_debug_enabled, performance_logger
from ..types import PipelineResult, Row

logger = logging.getLogger(__name__)

DEFAULT_PROGRESS_INTERVAL = 1000  # Call progress callback every N rows


def pipeline(
    source: BaseIterable,
    destination: BaseIterable | None,
    process_func: Callable[[Row, dict[str, Any]], Row | None],
    trigger_func: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
    trigger_on: int = 1000,
    final_func: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
    reset_iterables: bool = True,
    skip_nulls: bool = True,
    start_state: dict[str, Any] | None = None,
    debug: bool = False,
    batch_size: int = 1000,
    progress: Callable[[dict[str, Any]], None] | None = None,
    progress_interval: int = DEFAULT_PROGRESS_INTERVAL,
    atomic: bool = False,
) -> PipelineResult:
    """Wrapper over Pipeline class to simplify data processing pipelines execution.

    Args:
        source: Source iterable to read data from
        destination: Destination iterable to write data to (can be None)
        process_func: Function to process each record
        trigger_func: Optional function called periodically during processing
        trigger_on: Number of records between trigger function calls
        final_func: Optional function called after processing completes
        reset_iterables: If True, reset iterables before processing
        skip_nulls: If True, skip None results from process_func
        start_state: Initial state dictionary passed to process_func
        debug: If True, raise exceptions instead of catching them
        batch_size: Number of records to batch before writing
        progress: Optional callback function for progress updates
        progress_interval: Number of rows between progress callback invocations.
                          Default: 1000. Set to smaller value for more frequent updates,
                          or larger value to reduce callback overhead.
        atomic: If True and destination is a file, use atomic writes. Default: False.

    Returns:
        PipelineResult: Object containing pipeline execution metrics.
    """
    if start_state is None:
        start_state = {}
    runner = Pipeline(
        source=source,
        destination=destination,
        process_func=process_func,
        trigger_func=trigger_func,
        trigger_on=trigger_on,
        final_func=final_func,
        reset_iterables=reset_iterables,
        skip_nulls=skip_nulls,
        start_state=start_state,
        batch_size=batch_size,
        progress=progress,
        progress_interval=progress_interval,
        atomic=atomic,
    )
    return runner.run(debug)


class Pipeline:
    """Data processing pipeline that read data and process it"""

    def __init__(
        self,
        source: BaseIterable,
        destination: BaseIterable | None = None,
        process_func: Callable[[Row, dict[str, Any]], Row | None] | None = None,
        trigger_func: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
        trigger_on: int = 1000,
        final_func: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
        reset_iterables: bool = True,
        skip_nulls: bool = True,
        start_state: dict[str, Any] | None = None,
        batch_size: int = 1000,
        progress: Callable[[dict[str, Any]], None] | None = None,
        progress_interval: int = DEFAULT_PROGRESS_INTERVAL,
        atomic: bool = False,
    ) -> None:
        if start_state is None:
            start_state = {}
        self.source = source
        self.destination = destination
        self.process_func = process_func
        self.trigger_func = trigger_func
        self.trigger_on = trigger_on
        self.final_func = final_func
        self.reset_iterables = reset_iterables
        self.skip_nulls = skip_nulls
        self.start_state = start_state
        self.batch_size = batch_size
        self.progress = progress
        self.progress_interval = progress_interval
        self.atomic = atomic
        self._original_destination_filename: str | None = None
        self._temp_file: str | None = None

    def run(self, debug: bool = False) -> PipelineResult:
        """Execute pipeline"""
        time_start = time.time()
        stats: dict[str, Any] = {"rec_count": 0, "nulls": 0, "exceptions": 0, "time_start": time_start}
        state = self.start_state

        perf_debug = debug or is_debug_enabled()
        if perf_debug:
            performance_logger.debug("Starting pipeline execution")
            dest_name = type(self.destination).__name__ if self.destination else None
            performance_logger.debug(f"Source: {type(self.source).__name__}, Destination: {dest_name}")
            performance_logger.debug(f"Batch size: {self.batch_size}, Reset iterables: {self.reset_iterables}")

        # Setup atomic writes if enabled and destination is a file
        if self.atomic and self.destination is not None:
            if isinstance(self.destination, BaseFileIterable) and hasattr(self.destination, "stype"):
                # Check if destination is a file (not a stream or codec)
                if self.destination.stype == 20:  # ITERABLE_TYPE_FILE
                    if hasattr(self.destination, "filename") and self.destination.filename:
                        self._original_destination_filename = self.destination.filename
                        # Generate temporary filename
                        self._temp_file = os.path.join(
                            os.path.dirname(self._original_destination_filename) or ".",
                            os.path.basename(self._original_destination_filename) + ".tmp",
                        )
                        # Clean up any existing temp file
                        if os.path.exists(self._temp_file):
                            try:
                                os.remove(self._temp_file)
                            except Exception as e:
                                logger.warning(f"Failed to remove existing temporary file '{self._temp_file}': {e}")
                        # Update destination filename to temp file
                        self.destination.filename = self._temp_file
                        # Reopen with new filename if already opened
                        if hasattr(self.destination, "fobj") and self.destination.fobj is not None:
                            try:
                                self.destination.close()
                            except Exception:
                                pass
                            self.destination.open()

        if self.reset_iterables:
            # Reset source (database sources don't support reset - handle gracefully)
            try:
                self.source.reset()
            except NotImplementedError:
                # Database sources don't support reset - this is expected
                logger.debug("Source does not support reset (likely a database source)")
            if self.destination is not None:
                try:
                    self.destination.reset()
                except NotImplementedError:
                    # Database destinations don't support reset - this is expected
                    logger.debug("Destination does not support reset (likely a database destination)")

        batch: list[Row] = []
        can_bulk_write = (
            self.destination is not None
            and hasattr(self.destination, "write_bulk")
            and self.batch_size
            and self.batch_size > 1
        )

        def flush_batch():
            nonlocal batch
            if self.destination is None or not batch:
                batch = []
                return
            if can_bulk_write:
                try:
                    self.destination.write_bulk(batch)
                except Exception:
                    # Fallback to per-record writes if destination's bulk path errors.
                    for item in batch:
                        self.destination.write(item)
            else:
                for item in batch:
                    self.destination.write(item)
            batch = []

        def invoke_progress_callback():
            """Invoke progress callback if provided."""
            if self.progress is not None:
                elapsed = time.time() - time_start
                throughput = stats["rec_count"] / elapsed if elapsed > 0 else None
                try:
                    self.progress(
                        {
                            "rows_processed": stats["rec_count"],
                            "elapsed": elapsed,
                            "throughput": throughput,
                            "rec_count": stats["rec_count"],
                            "exceptions": stats["exceptions"],
                            "nulls": stats["nulls"],
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error in progress callback: {e}")

        try:
            for record in self.source:
                try:
                    result = self.process_func(record, state)
                    if result is None:
                        if not self.skip_nulls:
                            stats["nulls"] += 1
                            if self.destination is not None:
                                # Preserve existing behavior (even though many destinations expect dicts).
                                flush_batch()
                                self.destination.write(result)
                    else:
                        if self.destination is not None:
                            if can_bulk_write:
                                batch.append(result)
                                if len(batch) >= self.batch_size:
                                    flush_batch()
                            else:
                                self.destination.write(result)
                except Exception as e:
                    logger.error(f"Error processing record #{stats['rec_count'] + 1}: {e}", exc_info=debug)
                    stats["exceptions"] += 1
                    # In atomic mode the write is all-or-nothing: a processing error
                    # must abort the run so the original file is preserved and the
                    # temporary file is cleaned up. In non-atomic mode errors are
                    # tolerated and counted.
                    if debug or self.atomic:
                        raise
                stats["rec_count"] += 1

                # Invoke progress callback periodically
                if stats["rec_count"] % self.progress_interval == 0:
                    invoke_progress_callback()

                if stats["rec_count"] % self.trigger_on == 0 and self.trigger_func is not None:
                    try:
                        flush_batch()
                        self.trigger_func(stats, state)
                    except Exception as e:
                        logger.error(f"Error in trigger function at record #{stats['rec_count']}: {e}", exc_info=debug)
                        if debug:
                            raise
        except Exception:
            # Clean up temporary file on error if atomic writes are enabled
            if self.atomic and self._temp_file is not None and os.path.exists(self._temp_file):
                try:
                    os.remove(self._temp_file)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file '{self._temp_file}': {cleanup_error}")
            raise
        finally:
            flush_batch()

            # Final progress callback
            invoke_progress_callback()

        time_end = time.time()
        stats["time_end"] = time_end
        stats["duration"] = time_end - time_start

        if perf_debug:
            throughput = stats["rec_count"] / stats["duration"] if stats["duration"] > 0 else 0
            performance_logger.debug(
                f"Pipeline completed: {stats['rec_count']} records in "
                f"{stats['duration']:.2f}s (throughput: {throughput:.2f} rec/s, "
                f"exceptions: {stats['exceptions']}, nulls: {stats['nulls']})"
            )

        # Perform atomic rename if atomic writes are enabled (only on success)
        if self.atomic and self._temp_file is not None and self._original_destination_filename is not None:
            try:
                if os.path.exists(self._temp_file):
                    # Import atomic write helper from convert module
                    from ..convert.core import _atomic_write

                    _atomic_write(self._original_destination_filename, self._temp_file)
            except Exception as e:
                logger.error(f"Failed to atomically rename temporary file: {e}")
                # Clean up temp file on error
                try:
                    if os.path.exists(self._temp_file):
                        os.remove(self._temp_file)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file '{self._temp_file}': {cleanup_error}")
                raise

        if self.final_func is not None:
            self.final_func(stats, state)

        # Return PipelineResult for structured access, but maintain dict compatibility
        return PipelineResult(
            rows_processed=stats["rec_count"],
            elapsed_seconds=stats["duration"],
            exceptions=stats["exceptions"],
            nulls=stats["nulls"],
            rec_count=stats["rec_count"],
            time_start=time_start,
            time_end=time_end,
            duration=stats["duration"],
        )
