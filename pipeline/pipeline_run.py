"""
ClinicalMind AI — Pipeline Run Tracking

Dataclasses that represent a single pipeline execution and the result of
each stage within it. Used by orchestrator.py and persisted to the
pipeline_runs Supabase table.
"""
from __future__ import annotations



import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"cm-{ts}-{uuid.uuid4().hex[:6]}"


@dataclass
class StageResult:
    """Result of a single pipeline stage."""

    name: str
    status: str = "pending"        # pending | ok | failed | skipped
    records_in: int = 0
    records_out: int = 0
    duration_secs: float = 0.0
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name":          self.name,
            "status":        self.status,
            "records_in":    self.records_in,
            "records_out":   self.records_out,
            "duration_secs": round(self.duration_secs, 3),
            "error":         self.error,
            "metadata":      self.metadata,
        }


@dataclass
class PipelineRun:
    """Tracks the full lifecycle of one pipeline execution."""

    run_id: str = field(default_factory=_run_id)
    started_at: datetime = field(default_factory=_now)
    config: dict = field(default_factory=dict)
    stages: list[StageResult] = field(default_factory=list)
    completed_at: datetime | None = None
    status: str = "running"   # running | success | failed

    def add_stage(self, result: StageResult) -> None:
        self.stages.append(result)

    def finish(self, status: str = "success") -> None:
        self.completed_at = _now()
        self.status = status

    @property
    def duration_secs(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (_now() - self.started_at).total_seconds()

    def stage(self, name: str) -> StageResult | None:
        return next((s for s in self.stages if s.name == name), None)

    def to_dict(self) -> dict:
        return {
            "run_id":        self.run_id,
            "started_at":    self.started_at.isoformat(),
            "completed_at":  self.completed_at.isoformat() if self.completed_at else None,
            "status":        self.status,
            "config":        self.config,
            "stages":        [s.to_dict() for s in self.stages],
        }
