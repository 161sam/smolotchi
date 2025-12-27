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

    db = os.environ.get("SMOLOTCHI_DB", "/var/lib/smolotchi/events.db")
    root = os.environ.get("SMOLOTCHI_ARTIFACT_ROOT", "/var/lib/smolotchi/artifacts")

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

    while True:
        _poll_buttons(bus, ui, artifacts)
        _tick_render(driver, hw_ok, artifacts, jobs, power, ui, profile)
        time.sleep(0.2)


def _poll_buttons(bus: SQLiteBus, ui: UIState, artifacts: ArtifactStore) -> None:
    events = bus.tail(limit=20, topic_prefix="ui.btn.")
    for evt in reversed(events):
        if evt.ts <= ui.last_btn_ts:
            continue
        ui.last_btn_ts = max(ui.last_btn_ts, evt.ts)
        ui.last_interaction_ts = time.time()

        if evt.topic == "ui.btn.next":
            ui.screen_index = (ui.screen_index + 1) % len(SCREENS)
        elif evt.topic == "ui.btn.mode":
            ui.mode = "ops" if ui.mode != "ops" else "observe"
        elif evt.topic == "ui.btn.ok":
            artifacts.put_json(
                kind="ui_intent_ok",
                title="UI intent OK",
                payload={"ts": _utc_iso(), "screen": SCREENS[ui.screen_index]},
            )

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

    worker_ok = bool(artifacts.latest_json("worker_health"))

    stage_metas = artifacts.list(limit=1, kind="ai_stage_request")
    has_pending_stage = False
    stage = None
    if stage_metas:
        stage = artifacts.get_json(stage_metas[0].id)
        has_pending_stage = bool(stage)

    screen = SCREENS[ui.screen_index]

    if screen == "STATUS":
        lines = [
            f"Smolotchi [{ui.mode}]",
            f"Display: {'OK' if hw_ok else 'OFF'}",
            f"Worker: {'OK' if worker_ok else 'OFF'}",
            f"Stage: {'PENDING' if has_pending_stage else '-'}",
            f"Bat: {power_status.percent if power_status.percent is not None else '?'}% ({power_status.source})",
            _utc_iso().split("T")[1][:8],
            "",
            "BTN1 Next | BTN2 Mode",
            "BTN3 OK (intent)",
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
            lines.append("BTN3 OK -> intent")
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
