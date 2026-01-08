from __future__ import annotations

import importlib
import importlib.util
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class ButtonConfig:
    next_pin: Optional[int]
    mode_pin: Optional[int]
    ok_pin: Optional[int]
    debounce_ms: int = 180


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    raw = raw.strip().lower()
    if raw in ("1", "true", "yes", "y", "on"):
        return True
    if raw in ("0", "false", "no", "n", "off"):
        return False
    return default


class ButtonWatcher:
    """
    Optional GPIO button watcher.

    Design goals:
    - Must never crash the display daemon if GPIO/buttons are missing.
    - Can be disabled globally via SMOLOTCHI_BUTTONS=0.
    - If pins are not configured (all None), it disables itself automatically.
    """

    def __init__(self, cfg: ButtonConfig, on_event: Callable[[str], None]):
        self.cfg = cfg
        self.on_event = on_event
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._enabled = False
        self.GPIO = None

        # Global toggle; default: OFF (since your device currently has no buttons)
        if not _env_bool("SMOLOTCHI_BUTTONS", False):
            return

        # Auto-disable if no pins configured
        if cfg.next_pin is None and cfg.mode_pin is None and cfg.ok_pin is None:
            return

        # Try importing RPi.GPIO safely
        try:
            spec = importlib.util.find_spec("RPi.GPIO")
        except ModuleNotFoundError:
            spec = None

        if spec is None:
            return

        try:
            self.GPIO = importlib.import_module("RPi.GPIO")
        except Exception:
            self.GPIO = None
            return

        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start(self) -> None:
        if not self._enabled:
            return

        GPIO = self.GPIO
        if GPIO is None:
            self._enabled = False
            return

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        except Exception:
            self._enabled = False
            return

        def setup(pin: Optional[int]) -> None:
            if pin is None:
                return
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            except Exception:
                # If a pin can't be set up (not present / permissions / already used),
                # keep the daemon alive by just skipping it.
                pass

        setup(self.cfg.next_pin)
        setup(self.cfg.mode_pin)
        setup(self.cfg.ok_pin)

        def register(pin: Optional[int], name: str) -> None:
            if pin is None:
                return

            def cb(_channel: int) -> None:
                time.sleep(self.cfg.debounce_ms / 1000.0)
                try:
                    if GPIO.input(pin) == 0:
                        self.on_event(name)
                except Exception:
                    # Never crash from callback
                    return

            try:
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=cb,
                    bouncetime=self.cfg.debounce_ms,
                )
            except Exception:
                # Edge detection may fail if kernel/gpio subsystem doesn't support it
                # or pin isn't valid. Skip silently.
                pass

        register(self.cfg.next_pin, "ui.btn.next")
        register(self.cfg.mode_pin, "ui.btn.mode")
        register(self.cfg.ok_pin, "ui.btn.ok")

        self._thread = threading.Thread(target=self._run, name="buttons", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            time.sleep(0.25)

    def stop(self) -> None:
        self._stop.set()
        GPIO = self.GPIO
        if GPIO is None:
            return
        try:
            GPIO.cleanup()
        except Exception:
            pass
