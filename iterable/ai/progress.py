"""In-process progress reporting for block-based documentation generation.

Provides a lightweight, dependency-free progress mechanism mirroring the
documentation job lifecycle. This is intentionally synchronous and in-process:
external orchestration (task queues, webhooks, persistence) lives in the
consuming service, not in this library.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("iterable.ai.progress")


class Stage(str, Enum):
    """Processing stages for documentation generation."""

    QUEUED = "queued"
    FETCHING = "fetching"
    PARSING = "parsing"
    CONVERTING = "converting"
    SAMPLING = "sampling"
    GENERATING = "generating"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressEvent:
    """A single progress update emitted during generation."""

    job_id: str
    stage: Stage
    progress: int
    detail: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "detail": self.detail,
            "data": self.data,
        }


# A progress callback receives a single ProgressEvent and returns nothing.
ProgressCallback = Callable[[ProgressEvent], None]


class ProgressReporter:
    """Emits :class:`ProgressEvent` updates to an optional callback.

    The reporter never raises if the callback fails; callback errors are logged
    and swallowed so progress reporting cannot break generation.
    """

    def __init__(self, callback: ProgressCallback | None = None, job_id: str | None = None):
        self.callback = callback
        self.job_id = job_id or str(uuid.uuid4())

    def emit(
        self,
        stage: Stage,
        progress: int,
        detail: str | None = None,
        **data: Any,
    ) -> ProgressEvent:
        """Emit a progress event and invoke the callback if present."""
        event = ProgressEvent(
            job_id=self.job_id,
            stage=stage,
            progress=max(0, min(100, int(progress))),
            detail=detail,
            data=dict(data),
        )
        if self.callback is not None:
            try:
                self.callback(event)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Progress callback raised an exception: %s", exc)
        return event


class StageTimer:
    """Context manager that times a stage and logs a structured completion event.

    Usage:
        >>> reporter = ProgressReporter()
        >>> with StageTimer(reporter, Stage.PARSING, "parse data"):  # doctest: +SKIP
        ...     ...
    """

    def __init__(
        self,
        reporter: ProgressReporter,
        stage: Stage,
        detail: str | None = None,
        progress: int = 0,
        **data: Any,
    ):
        self.reporter = reporter
        self.stage = stage
        self.detail = detail
        self.progress = progress
        self.data = data
        self._start = 0.0

    def __enter__(self) -> StageTimer:
        self._start = time.perf_counter()
        self.reporter.emit(self.stage, self.progress, self.detail, **self.data)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = (time.perf_counter() - self._start) * 1000.0
        if exc_type is not None:
            logger.error(
                "stage failed: %s",
                self.stage.value,
                extra={
                    "job_id": self.reporter.job_id,
                    "stage": self.stage.value,
                    "duration_ms": round(duration_ms, 2),
                    "event_type": "ai_documentation",
                },
            )
            self.reporter.emit(Stage.FAILED, self.progress, f"failed during {self.stage.value}")
            return
        logger.info(
            "stage completed: %s",
            self.stage.value,
            extra={
                "job_id": self.reporter.job_id,
                "stage": self.stage.value,
                "duration_ms": round(duration_ms, 2),
                "event_type": "ai_documentation",
                **{k: v for k, v in self.data.items() if _json_safe(v)},
            },
        )


def _json_safe(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool, type(None)))
