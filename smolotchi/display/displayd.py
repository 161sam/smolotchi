from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from PIL import Image, ImageDraw, ImageFont

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.paths import resolve_artifact_root, resolve_db_path
from smolotchi.device.buttons import ButtonConfig, ButtonWatcher
from smolotchi.device.power import PowerMonitor
from smolotchi.device.profile import get_device_profile

from .waveshare_driver import EPDDriver

SCREENS = ["STATUS", "JOBS", "STAGES", "POWER"]


@dataclass
class UIState:
    screen_index: int = 0
    mode: str = "observe"
    last_interaction_ts: float = 0.0
    last_render_ts: float = 0.0
    last_btn_ts: float = 0.0
    last_btn_event_ts: float = 0.0
    last_btn_topic: str = ""
    last_ui_state_write_ts: float = 0.0


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_font(size: int = 12) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=size
        )
    except Exception:
        return ImageFont.load_default()


def _render_text_screen(width: int, height: int, lines: List[str]) -> Image.Image:
    image = Image.new("1", (width, height), 255)
    drawer = ImageDraw.Draw(image)
    font = _safe_font(12)

    y = 2
    for line in lines[:14]:
        drawer.text((2, y), line, font=font, fill=0)
        y += 12
        if y > height - 12:
            break
    return image


def _dryrun_enabled() -> bool:
    return os.environ.get("SMOLOTCHI_DISPLAY_DRYRUN", "").strip() == "1"


def main() -> None:
    profile = get_device_profile(os.environ.get("SMOLOTCHI_DEVICE", "pi_zero"))

    db = resolve_db_path()
    root = resolve_artifact_root()

    bus = SQLiteBus(db_path=db)
    artifacts = ArtifactStore(root=root)
    jobs = JobStore(db_path=db)
    power = PowerMonitor()

    ui = UIState()

    def on_btn(evt: str) -> None:
        bus.publish(evt, {"ts": time.time()})

    buttons = ButtonWatcher(
        ButtonConfig(
            next_pin=profile.btn_next_pin,
            mode_pin=profile.btn_mode_pin,
            ok_pin=profile.btn_ok_pin,
        ),
        on_event=on_btn,
    )
    buttons.start()

    driver = EPDDriver()
    hw_ok = False
    if not _dryrun_enabled():
        hw_ok = driver.init()
        if hw_ok:
            driver.clear()

    last_prune = 0.0

    while True:
        _poll_buttons(bus, ui, artifacts, jobs)
        _tick_render(driver, hw_ok, artifacts, jobs, power, ui, profile)

        now = time.time()
        if now - last_prune > 300.0:
            last_prune = now
            try:
                artifacts.prune(
                    keep_last=profile.artifacts_keep_max,
                    older_than_days=profile.artifacts_keep_days,
                )
            except Exception:
                pass
            try:
                bus.prune(keep_last=5000, older_than_days=30, vacuum=False)
            except Exception:
                pass

        time.sleep(0.2)


def _poll_buttons(
    bus: SQLiteBus, ui: UIState, artifacts: ArtifactStore, jobs: JobStore
) -> None:
    events = bus.tail(limit=20, topic_prefix="ui.btn.")
    for evt in reversed(events):
        if evt.ts <= ui.last_btn_ts:
            continue
        ui.last_btn_ts = max(ui.last_btn_ts, float(evt.ts) + 1e-6)
        ui.last_interaction_ts = time.time()
        now = time.time()
        if evt.topic == ui.last_btn_topic and (now - ui.last_btn_event_ts) < 0.25:
            continue
        ui.last_btn_topic = evt.topic
        ui.last_btn_event_ts = now
        before_screen = ui.screen_index
        before_mode = ui.mode

        if evt.topic == "ui.btn.next":
            ui.screen_index = (ui.screen_index + 1) % len(SCREENS)
        elif evt.topic == "ui.btn.mode":
            ui.mode = "ops" if ui.mode != "ops" else "observe"
        elif evt.topic == "ui.btn.ok":
            req = None
            if hasattr(artifacts, "find_latest_pending_stage_request"):
                req = artifacts.find_latest_pending_stage_request()
            if not req:
                req = artifacts.find_latest_stage_request()
            if req and artifacts.is_stage_request_pending(req):
                rid = str(req.get("id") or req.get("request_id") or "")
                job_id = req.get("job_id")
                step_index = req.get("step_index")
                artifacts.put_json(
                    kind="ai_stage_approval",
                    title="Stage approved (device)",
                    payload={
                        "request_id": rid,
                        "approved_by": "device:button",
                        "ts": _utc_iso(),
                    },
                )
                if job_id:
                    note = (
                        f"resume_from:{step_index}"
                        if step_index is not None
                        else "resume_from:0"
                    )
                    try:
                        jobs.mark_queued(str(job_id), note=note)
                    except Exception:
                        pass
                bus.publish(
                    "ai.stage.approved",
                    {
                        "request_id": rid,
                        "job_id": job_id,
                        "step_index": step_index,
                        "ts": time.time(),
                    },
                )
                artifacts.put_json(
                    kind="ui_notice",
                    title="UI Notice",
                    payload={"ts": _utc_iso(), "msg": "Approved!", "request_id": rid},
                )
            else:
                bus.publish(
                    "ui.intent.ok", {"ts": time.time(), "screen": SCREENS[ui.screen_index]}
                )
                artifacts.put_json(
                    kind="ui_notice",
                    title="UI Notice",
                    payload={"ts": _utc_iso(), "msg": "No pending stage"},
                )

        changed = (ui.screen_index != before_screen) or (ui.mode != before_mode)
        if changed or (time.time() - ui.last_ui_state_write_ts) > 2.0:
            ui.last_ui_state_write_ts = time.time()
            artifacts.put_json(
                kind="ui_display_state",
                title="UI display state",
                payload={
                    "screen": SCREENS[ui.screen_index],
                    "screen_index": ui.screen_index,
                    "mode": ui.mode,
                    "ts": _utc_iso(),
                },
            )


def _tick_render(
    driver: EPDDriver,
    hw_ok: bool,
    artifacts: ArtifactStore,
    jobs: JobStore,
    power: PowerMonitor,
    ui: UIState,
    profile,
) -> None:
    now = time.time()
    if now - ui.last_render_ts < profile.display_refresh_min_s:
        return
    ui.last_render_ts = now

    width, height = driver.size

    power_status = power.read()
    artifacts.put_json(
        kind="power_status",
        title="Power status",
        payload=PowerMonitor.to_dict(power_status),
    )

    worker_ok = False
    worker_health = artifacts.latest_json("worker_health")
    if worker_health:
        ts = None
        raw = worker_health.get("ts")
        if raw:
            try:
                ts = datetime.fromisoformat(str(raw)).timestamp()
            except Exception:
                ts = None
        if ts is None:
            worker_ok = True
        else:
            worker_ok = (time.time() - ts) <= 120.0

    stage = None
    if hasattr(artifacts, "find_latest_pending_stage_request"):
        stage = artifacts.find_latest_pending_stage_request()
    if not stage:
        stage = artifacts.find_latest_stage_request()

    has_pending_stage = False
    if stage and hasattr(artifacts, "is_stage_request_pending"):
        has_pending_stage = artifacts.is_stage_request_pending(stage)
    else:
        has_pending_stage = bool(stage)
    stage_total = artifacts.count_kind("ai_stage_request")
    stage_pending = (
        artifacts.count_pending_stage_requests()
        if hasattr(artifacts, "count_pending_stage_requests")
        else (1 if has_pending_stage else 0)
    )

    screen = SCREENS[ui.screen_index]

    if screen == "STATUS":
        lines = [
            f"Smolotchi [{ui.mode}]",
            f"Display: {'OK' if hw_ok else 'OFF'}",
            f"Worker: {'OK' if worker_ok else 'OFF'}",
            f"Stage: {'PENDING' if has_pending_stage else '-'} ({stage_pending}/{stage_total})",
            f"Bat: {power_status.percent if power_status.percent is not None else '?'}% ({power_status.source})",
            _utc_iso().split("T")[1][:8],
            "",
            "BTN1 Next | BTN2 Mode",
            "BTN3 OK approve (if pending)",
        ]
        image = _render_text_screen(width, height, lines)
    elif screen == "JOBS":
        recent = jobs.list_recent(limit=4)
        lines = ["Jobs (latest):"]
        for job in recent:
            jid = str(job.id)
            lines.append(f"{job.status[:1].upper()} {job.kind[:10]} {jid[-6:]}")
        lines += ["", "BTN1 Next"]
        image = _render_text_screen(width, height, lines)
    elif screen == "STAGES":
        lines = ["Stages:"]
        if has_pending_stage and stage:
            lines.append("PENDING APPROVAL")
            lines.append(f"job:{str(stage.get('job_id', ''))[-6:]}")
            lines.append(
                f"step:{stage.get('step_index', '?')} {str(stage.get('action_id', ''))[:12]}"
            )
            lines.append("")
            lines.append("BTN3 OK -> approve")
        else:
            lines.append("none")
        lines += ["", "BTN1 Next"]
        image = _render_text_screen(width, height, lines)
    else:
        lines = [
            "Power:",
            f"Bat: {power_status.percent if power_status.percent is not None else '?'}%",
            f"Src: {power_status.source}",
            "",
            "sysfs:",
            "/sys/class/power_supply/*/capacity",
        ]
        image = _render_text_screen(width, height, lines)

    if _dryrun_enabled() or not hw_ok:
        return

    try:
        driver.display_image(image)
    except Exception:
        pass


if __name__ == "__main__":
    main()
