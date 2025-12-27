from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.resources import ResourceManager
from smolotchi.device.buttons import ButtonConfig, ButtonWatcher
from smolotchi.device.power import PowerMonitor
from smolotchi.device.profile import DeviceProfile, get_device_profile

from .waveshare_driver import EPDDriver

SCREENS = ("STATUS", "JOBS", "STAGES", "POWER")


@dataclass
class UIState:
    screen_index: int = 0
    mode: str = "observe"
    last_interaction_ts: float = 0.0
    last_render_ts: float = 0.0
    last_low_battery_ts: float = 0.0
    low_battery_active: bool = False


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
    for line in lines[:10]:
        drawer.text((2, y), line, font=font, fill=0)
        y += 12
        if y > height - 12:
            break
    return image


def _parse_iso(ts: Optional[str]) -> Optional[float]:
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _latest_artifact_json(artifacts: ArtifactStore, kind: str) -> Optional[Dict[str, Any]]:
    latest = artifacts.list(limit=1, kind=kind)
    if not latest:
        return None
    return artifacts.get_json(latest[0].id)


def _handle_button_event(
    bus: SQLiteBus,
    artifacts: ArtifactStore,
    ui: UIState,
    kind: str,
    payload: Dict[str, Any],
) -> None:
    ui.last_interaction_ts = time.time()
    if kind == "ui.btn.next":
        ui.screen_index = (ui.screen_index + 1) % len(SCREENS)
    elif kind == "ui.btn.mode":
        ui.mode = "ops" if ui.mode != "ops" else "observe"
    elif kind == "ui.btn.ok":
        bus.publish(
            "ui.intent.ok",
            {"ts": time.time(), "screen": SCREENS[ui.screen_index]},
        )

    artifacts.put_json(
        kind="ui_display_state",
        title="UI Display State",
        payload={
            "screen": SCREENS[ui.screen_index],
            "screen_index": ui.screen_index,
            "mode": ui.mode,
            "ts": _utc_iso(),
        },
    )


def _render_screen(
    driver: EPDDriver,
    artifacts: ArtifactStore,
    jobs: JobStore,
    power: PowerMonitor,
    ui: UIState,
    profile: DeviceProfile,
    bus: SQLiteBus,
) -> None:
    now = time.time()
    if now - ui.last_render_ts < profile.display_refresh_min_s:
        return
    ui.last_render_ts = now

    width, height = driver.size
    screen = SCREENS[ui.screen_index]

    power_status = power.read()
    artifacts.put_json(
        kind="power_status",
        title="Power Status",
        payload=PowerMonitor.to_dict(power_status),
    )

    if (
        power_status.percent is not None
        and profile.low_battery_percent is not None
        and power_status.percent <= profile.low_battery_percent
    ):
        if (
            not ui.low_battery_active
            or now - ui.last_low_battery_ts > 300.0
        ):
            ui.low_battery_active = True
            ui.last_low_battery_ts = now
            bus.publish(
                "power.low_battery",
                {
                    "percent": power_status.percent,
                    "threshold": profile.low_battery_percent,
                    "ts": now,
                },
            )
    else:
        ui.low_battery_active = False

    worker_health = _latest_artifact_json(artifacts, "worker_health")
    worker_ok = False
    if worker_health:
        health_ts = _parse_iso(worker_health.get("ts"))
        if health_ts:
            worker_ok = (now - health_ts) < 120.0

    stage_request = _latest_artifact_json(artifacts, "ai_stage_request")
    has_pending_stage = bool(stage_request)

    if screen == "STATUS":
        lines = [
            f"Smolotchi [{ui.mode}]",
            f"Screen: {screen}",
            f"Worker: {'OK' if worker_ok else 'OFF'}",
            f"Stage: {'PENDING' if has_pending_stage else '-'}",
            f"Bat: {power_status.percent if power_status.percent is not None else '?'}% ({power_status.source})",
            _utc_iso().split("T")[1][:8],
            "",
            "BTN1 Next | BTN2 Mode",
            "BTN3 OK",
        ]
        image = _render_text_screen(width, height, lines)
    elif screen == "JOBS":
        recent = jobs.list(limit=3)
        lines = ["Jobs (latest):"]
        for job in recent:
            jid = str(job.id)
            lines.append(f"{job.status[:1].upper()} {job.kind[:10]} {jid[-5:]}")
        lines += ["", "BTN1 Next"]
        image = _render_text_screen(width, height, lines)
    elif screen == "STAGES":
        lines = ["Stages:"]
        if has_pending_stage:
            lines.append("PENDING APPROVAL")
            lines.append(f"job:{str(stage_request.get('job_id', ''))[-6:]}")
            lines.append(
                f"step:{stage_request.get('step_index', '?')} {str(stage_request.get('action_id', ''))[:12]}"
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
            "Tip: sysfs capacity",
            "/sys/class/power_supply/*/capacity",
        ]
        image = _render_text_screen(width, height, lines)

    driver.display_image(image)


def main() -> None:
    bus = SQLiteBus()
    artifacts = ArtifactStore()
    jobs = JobStore()
    resources = ResourceManager("/run/smolotchi/locks")

    owner = "displayd"
    driver = EPDDriver()
    ok_hw = driver.init()
    if ok_hw:
        driver.clear()

    profile_name = os.environ.get("SMOLOTCHI_DEVICE_PROFILE", "pi_zero")
    profile = get_device_profile(profile_name)
    ui = UIState()
    power = PowerMonitor()

    def on_btn(evt: str) -> None:
        bus.publish(evt, {"ts": time.time()})
        _handle_button_event(bus, artifacts, ui, evt, {"ts": time.time()})

    buttons = ButtonWatcher(
        ButtonConfig(
            next_pin=profile.btn_next_pin,
            mode_pin=profile.btn_mode_pin,
            ok_pin=profile.btn_ok_pin,
        ),
        on_event=on_btn,
    )
    buttons.start()

    last_tick = 0.0
    last_evt_ts = 0.0
    while True:
        have_display_lock = resources.acquire("display", owner=owner, ttl=20.0)
        if not have_display_lock:
            bus.publish("display.lock.denied", {"owner": owner})
        else:
            bus.publish("display.lock.ok", {"owner": owner})

        events = bus.tail(limit=10, topic_prefix="ui.btn.")
        for event in events:
            if event.ts <= last_evt_ts:
                continue
            last_evt_ts = event.ts
            _handle_button_event(bus, artifacts, ui, event.topic, event.payload)

        now = time.time()
        if now - last_tick >= profile.display_tick_s:
            last_tick = now
            if ok_hw and have_display_lock:
                _render_screen(driver, artifacts, jobs, power, ui, profile, bus)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
