import time
from dataclasses import dataclass
from typing import Optional

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.engines import EngineHealth
from smolotchi.core.jobs import JobRow, JobStore
from smolotchi.core.reports import ReportRenderer


@dataclass
class LanConfig:
    enabled: bool = True
    safe_mode: bool = True
    max_jobs_per_tick: int = 1


class LanEngine:
    name = "lan"

    def __init__(
        self,
        bus: SQLiteBus,
        cfg: LanConfig,
        artifacts: ArtifactStore,
        jobs: JobStore,
        report_renderer: Optional[ReportRenderer] = None,
    ):
        self.bus = bus
        self.cfg = cfg
        self.artifacts = artifacts
        self.jobs = jobs
        self.report_renderer = report_renderer
        self._running = False
        self._active: Optional[JobRow] = None

    def start(self) -> None:
        self._running = True
        self.bus.publish("lan.engine.started", {"safe_mode": self.cfg.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("lan.engine.stopped", {})

    def enqueue(self, job_dict: dict) -> None:
        self.jobs.enqueue(job_dict)
        self.bus.publish(
            "lan.job.enqueued",
            {
                "id": job_dict["id"],
                "kind": job_dict["kind"],
                "scope": job_dict["scope"],
                "note": job_dict.get("note", ""),
            },
        )

    def tick(self) -> None:
        if not self._running or not self.cfg.enabled:
            return

        if self._active is None:
            self._active = self.jobs.pop_next()
            if self._active:
                self.bus.publish(
                    "lan.job.started",
                    {
                        "id": self._active.id,
                        "kind": self._active.kind,
                        "scope": self._active.scope,
                    },
                )

        if self._active is not None:
            try:
                result = {
                    "job": {
                        "id": self._active.id,
                        "kind": self._active.kind,
                        "scope": self._active.scope,
                        "note": self._active.note,
                    },
                    "summary": "stub result (persist queue v0.0.6)",
                    "ts": time.time(),
                }

                meta = self.artifacts.put_json(
                    kind="lan_result",
                    title=f"LAN {self._active.kind} • {self._active.scope}",
                    payload=result,
                )
                report_meta = None
                if self.report_renderer is not None:
                    html_bytes = self.report_renderer.render_lan_result(
                        title=f"LAN {self._active.kind} • {self._active.scope}",
                        result=result,
                    )
                    report_meta = self.artifacts.put_file(
                        kind="lan_report",
                        title=f"Report • {self._active.id}",
                        filename="report.html",
                        content=html_bytes,
                        mimetype="text/html; charset=utf-8",
                    )

                self.bus.publish(
                    "lan.job.progress", {"id": self._active.id, "pct": 100}
                )
                self.bus.publish(
                    "lan.job.finished",
                    {
                        "id": self._active.id,
                        "result": {
                            "artifact_id": meta.id,
                            "artifact_path": meta.path,
                            "report_artifact_id": report_meta.id if report_meta else None,
                            "report_path": report_meta.path if report_meta else None,
                        },
                    },
                )
                self.jobs.mark_done(self._active.id)
            except Exception as ex:
                self.bus.publish(
                    "lan.job.failed", {"id": self._active.id, "err": str(ex)}
                )
                self.jobs.mark_failed(self._active.id, note=str(ex))
            finally:
                self._active = None

    def health(self) -> EngineHealth:
        if not self.cfg.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        queued = self.jobs.list(limit=1, status="queued")
        detail = (
            "running queued="
            f"{'yes' if queued else 'no'} active={'yes' if self._active else 'no'}"
            if self._running
            else "stopped"
        )
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
