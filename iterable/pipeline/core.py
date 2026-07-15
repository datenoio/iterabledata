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
        self._batch: list[Row] = []
        self._can_bulk_write: bool = False

    # -- run stages -------------------------------------------------------

    def _log_start(self, perf_debug: bool) -> None:
        """Log pipeline configuration when performance debugging is on."""
        if not perf_debug:
            return
        performance_logger.debug("Starting pipeline execution")
        dest_name = type(self.destination).__name__ if self.destination else None
        performance_logger.debug(f"Source: {type(self.source).__name__}, Destination: {dest_name}")
        performance_logger.debug(f"Batch size: {self.batch_size}, Reset iterables: {self.reset_iterables}")

    def _destination_atomic_filename(self) -> str | None:
        """Return the destination filename if it supports atomic file writes."""
        dest = self.destination
        if dest is None or not isinstance(dest, BaseFileIterable):
            return None
        # Only plain files (not streams/codecs) can be atomically replaced.
        if getattr(dest, "stype", None) != 20:  # ITERABLE_TYPE_FILE
            return None
        return getattr(dest, "filename", None) or None

    def _setup_atomic_destination(self) -> None:
        """Redirect the file destination to a temp file for atomic writes."""
        if not self.atomic:
            return
        filename = self._destination_atomic_filename()
        if filename is None:
            return
        self._original_destination_filename = filename
        self._temp_file = os.path.join(
            os.path.dirname(filename) or ".",
            os.path.basename(filename) + ".tmp",
        )
        if os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except Exception as e:
                logger.warning(f"Failed to remove existing temporary file '{self._temp_file}': {e}")
        self.destination.filename = self._temp_file
        # Reopen with the new filename if the destination is already open.
        if getattr(self.destination, "fobj", None) is not None:
            try:
                self.destination.close()
            except Exception:
                pass
            self.destination.open()

    def _reset_iterables(self) -> None:
        """Reset source and destination, tolerating sources that cannot."""
        try:
            self.source.reset()
        except NotImplementedError:
            logger.debug("Source does not support reset (likely a database source)")
        if self.destination is not None:
            try:
                self.destination.reset()
            except NotImplementedError:
                logger.debug("Destination does not support reset (likely a database destination)")

    def _flush_batch(self) -> None:
        """Write any buffered records to the destination."""
        batch = self._batch
        self._batch = []
        if self.destination is None or not batch:
            return
        if self._can_bulk_write:
            try:
                self.destination.write_bulk(batch)
                return
            except Exception:
                # Fallback to per-record writes if destination's bulk path errors.
                pass
        for item in batch:
            self.destination.write(item)

    def _invoke_progress(self, stats: dict[str, Any], time_start: float) -> None:
        """Invoke the user progress callback, if provided."""
        if self.progress is None:
            return
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

    def _write_result(self, result: Row | None, stats: dict[str, Any]) -> None:
        """Route one processed result to the destination (or drop nulls)."""
        if result is None:
            if not self.skip_nulls:
                stats["nulls"] += 1
                if self.destination is not None:
                    # Preserve existing behavior (even though many destinations expect dicts).
                    self._flush_batch()
                    self.destination.write(result)
            return
        if self.destination is None:
            return
        if self._can_bulk_write:
            self._batch.append(result)
            if len(self._batch) >= self.batch_size:
                self._flush_batch()
        else:
            self.destination.write(result)

    def _process_record(self, record: Row, state: dict[str, Any], stats: dict[str, Any], debug: bool) -> None:
        """Process a single record, counting (or re-raising) failures."""
        try:
            result = self.process_func(record, state)
            self._write_result(result, stats)
        except Exception as e:
            logger.error(f"Error processing record #{stats['rec_count'] + 1}: {e}", exc_info=debug)
            stats["exceptions"] += 1
            # In atomic mode the write is all-or-nothing: a processing error
            # must abort the run so the original file is preserved and the
            # temporary file is cleaned up. In non-atomic mode errors are
            # tolerated and counted.
            if debug or self.atomic:
                raise

    def _maybe_trigger(self, stats: dict[str, Any], state: dict[str, Any], debug: bool) -> None:
        """Invoke the trigger function when the record count hits trigger_on."""
        if stats["rec_count"] % self.trigger_on != 0 or self.trigger_func is None:
            return
        try:
            self._flush_batch()
            self.trigger_func(stats, state)
        except Exception as e:
            logger.error(f"Error in trigger function at record #{stats['rec_count']}: {e}", exc_info=debug)
            if debug:
                raise

    def _cleanup_temp_file(self) -> None:
        """Remove the atomic temp file if it exists, tolerating failures."""
        if self._temp_file is None or not os.path.exists(self._temp_file):
            return
        try:
            os.remove(self._temp_file)
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temporary file '{self._temp_file}': {cleanup_error}")

    def _finalize_atomic(self) -> None:
        """Atomically move the temp file to the real destination on success."""
        if not self.atomic or self._temp_file is None or self._original_destination_filename is None:
            return
        try:
            if os.path.exists(self._temp_file):
                from ..convert.core import _atomic_write

                _atomic_write(self._original_destination_filename, self._temp_file)
        except Exception as e:
            logger.error(f"Failed to atomically rename temporary file: {e}")
            self._cleanup_temp_file()
            raise

    def _log_completion(self, stats: dict[str, Any], perf_debug: bool) -> None:
        """Log pipeline throughput when performance debugging is on."""
        if not perf_debug:
            return
        throughput = stats["rec_count"] / stats["duration"] if stats["duration"] > 0 else 0
        performance_logger.debug(
            f"Pipeline completed: {stats['rec_count']} records in "
            f"{stats['duration']:.2f}s (throughput: {throughput:.2f} rec/s, "
            f"exceptions: {stats['exceptions']}, nulls: {stats['nulls']})"
        )

    def _run_records(self, state: dict[str, Any], stats: dict[str, Any], time_start: float, debug: bool) -> None:
        """Drive the main record loop, cleaning up the temp file on failure."""
        try:
            for record in self.source:
                self._process_record(record, state, stats, debug)
                stats["rec_count"] += 1
                if stats["rec_count"] % self.progress_interval == 0:
                    self._invoke_progress(stats, time_start)
                self._maybe_trigger(stats, state, debug)
        except Exception:
            if self.atomic:
                self._cleanup_temp_file()
            raise
        finally:
            self._flush_batch()
            self._invoke_progress(stats, time_start)

    def run(self, debug: bool = False) -> PipelineResult:
        """Execute pipeline"""
        time_start = time.time()
        stats: dict[str, Any] = {"rec_count": 0, "nulls": 0, "exceptions": 0, "time_start": time_start}
        state = self.start_state

        perf_debug = debug or is_debug_enabled()
        self._log_start(perf_debug)
        self._setup_atomic_destination()
        if self.reset_iterables:
            self._reset_iterables()

        self._batch = []
        self._can_bulk_write = bool(
            self.destination is not None
            and hasattr(self.destination, "write_bulk")
            and self.batch_size
            and self.batch_size > 1
        )

        self._run_records(state, stats, time_start, debug)

        time_end = time.time()
        stats["time_end"] = time_end
        stats["duration"] = time_end - time_start

        self._log_completion(stats, perf_debug)
        self._finalize_atomic()

        if self.final_func is not None:
            self.final_func(stats, state)

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
