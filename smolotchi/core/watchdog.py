from __future__ import annotations

import os
import socket
import threading
import time
from typing import Dict, Optional

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.jobs import JobStore


class SystemdWatchdog:
    def __init__(self) -> None:
        self.interval = self._calc_interval()
        self._last_ping = time.time()
        self._running = False

    def _calc_interval(self) -> float:
        usec = os.getenv("WATCHDOG_USEC")
        if not usec:
            return 0.0
        try:
            return int(usec) / 1_000_000 / 2
        except ValueError:
            return 0.0

    def start(self) -> None:
        if self.interval <= 0:
            return
        self._running = True
        self._notify("READY=1")
        threading.Thread(target=self._loop, daemon=True).start()

    def ping(self) -> None:
        self._last_ping = time.time()

    def _loop(self) -> None:
        while self._running:
            if time.time() - self._last_ping <= self.interval * 2:
                self._notify("WATCHDOG=1")
            time.sleep(self.interval)

    def _notify(self, payload: str) -> None:
        addr = "/run/systemd/notify"
        if not os.path.exists(addr):
            return
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.connect(addr)
            sock.sendall(f"{payload}\n".encode("utf-8"))
        except Exception:
            return
        finally:
            try:
                sock.close()
            except Exception:
                return


class JobWatchdog:
    def __init__(
        self,
        bus: SQLiteBus,
        jobs: JobStore,
        config: ConfigStore,
    ):
        self.bus = bus
        self.jobs = jobs
        self.config = config
        self._reset_counts: Dict[str, int] = {}

    def tick(self) -> None:
        cfg = self.config.get()
        wd = getattr(cfg, "watchdog", None)
        if not wd or not getattr(wd, "enabled", False):
            return

        now = time.time()
        running = self.jobs.list(status="running", limit=100)

        for job in running:
            job_id = job.id
            started = getattr(job, "updated_ts", None) or getattr(job, "created_ts", 0.0)
            runtime = now - started

            if runtime < wd.min_runtime_sec:
                continue

            last_evt = self._last_job_event(job_id)
            last_ts = last_evt.get("ts") if last_evt else None
            idle = (now - last_ts) if last_ts else runtime

            if idle < wd.stuck_after_sec:
                continue

            resets = self._reset_counts.get(job_id, 0)
            self.bus.publish(
                "core.watchdog.job.stuck",
                {
                    "job_id": job_id,
                    "idle_sec": int(idle),
                    "runtime_sec": int(runtime),
                    "resets": resets,
                },
            )

            if wd.action == "none":
                continue

            if resets >= wd.max_resets:
                self.bus.publish(
                    "core.watchdog.job.giveup",
                    {"job_id": job_id, "resets": resets},
                )
                continue

            if wd.action == "reset":
                ok = self.jobs.reset_running(job_id)
                if ok:
                    self._reset_counts[job_id] = resets + 1
                    self.bus.publish(
                        "core.watchdog.job.reset",
                        {"job_id": job_id, "resets": self._reset_counts[job_id]},
                    )

            elif wd.action == "fail":
                ok = self.jobs.fail(job_id, note="watchdog: stuck")
                if ok:
                    self.bus.publish(
                        "core.watchdog.job.failed",
                        {"job_id": job_id},
                    )

    def _last_job_event(self, job_id: str) -> Optional[dict]:
        evts = self.bus.tail(limit=50)
        for e in evts:
            payload = e.payload or {}
            if payload.get("id") == job_id or payload.get("job", {}).get("id") == job_id:
                return {"ts": e.ts, "topic": e.topic}
        return None
