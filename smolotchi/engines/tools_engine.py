import subprocess
import time

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.engines import EngineHealth
from smolotchi.core.jobs import JobRow, JobStore


class ToolsEngine:
    name = "tools"

    def __init__(self, bus: SQLiteBus, artifacts: ArtifactStore, jobstore: JobStore):
        self.bus = bus
        self.artifacts = artifacts
        self.jobstore = jobstore
        self._running = True

    def start(self) -> None:
        self._running = True
        self.bus.publish("tools.engine.start", {"ts": time.time()})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("tools.engine.stop", {"ts": time.time()})

    def tick(self) -> None:
        if not self._running:
            return
        job = self.jobstore.pop_next_filtered(include_prefixes=["scan."])
        if not job:
            return
        self.bus.publish("tools.job.started", {"id": job.id, "kind": job.kind})
        ok = False
        err = ""
        try:
            if job.kind == "scan.nmap":
                ok = self._run_nmap(job)
            elif job.kind == "scan.bettercap":
                ok = self._run_bettercap(job)
            else:
                err = f"unknown kind {job.kind}"
                self.jobstore.mark_failed(job.id, err)
        except Exception as exc:
            err = str(exc)
            self.jobstore.mark_failed(job.id, err)
        else:
            if ok:
                self.jobstore.mark_done(job.id)
            elif not err:
                self.jobstore.mark_failed(job.id, "tool failed")
        finally:
            self.bus.publish("tools.job.finished", {"id": job.id, "ok": ok, "err": err})

    def _run_nmap(self, job: JobRow) -> bool:
        cmd = ["nmap", "-A", "-T4", job.scope]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        payload = {
            "job_id": job.id,
            "ts": start,
            "scope": job.scope,
            "cmd": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "rc": result.returncode,
        }
        result_meta = self.artifacts.put_json(
            kind="lan_result",
            title=f"nmap {job.scope}",
            payload=payload,
        )
        self._store_bundle(job, result_meta.id, ok=result.returncode == 0)
        return result.returncode == 0

    def _run_bettercap(self, job: JobRow) -> bool:
        cmd = [
            "bettercap",
            "-eval",
            f"set net.probe.targets {job.scope}; net.probe on; sleep 10; exit",
        ]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        payload = {
            "job_id": job.id,
            "ts": start,
            "scope": job.scope,
            "cmd": " ".join(cmd),
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
            "rc": result.returncode,
        }
        result_meta = self.artifacts.put_json(
            kind="lan_result",
            title=f"bettercap {job.scope}",
            payload=payload,
        )
        self._store_bundle(job, result_meta.id, ok=result.returncode == 0)
        return result.returncode == 0

    def _store_bundle(self, job: JobRow, result_id: str, ok: bool) -> None:
        bundle = {
            "job_id": job.id,
            "kind": job.kind,
            "scope": job.scope,
            "note": job.note,
            "created_ts": time.time(),
            "result_json": {"artifact_id": result_id},
        }
        bundle_meta = self.artifacts.put_json(
            kind="lan_bundle",
            title=f"Bundle • {job.id}",
            payload=bundle,
        )
        self.artifacts.put_json(
            kind="lan_job_result",
            title=f"lan job result {job.id}",
            payload={
                "ts": time.time(),
                "job_id": job.id,
                "bundle_id": bundle_meta.id,
                "report_id": None,
                "ok": ok,
            },
        )

    def health(self) -> EngineHealth:
        return EngineHealth(name="tools", ok=self._running, detail="running")
