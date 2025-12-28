from __future__ import annotations

import json

from .base import BaseParser


class BettercapParser(BaseParser):
    name = "bettercap"

    def parse(self, raw: str | bytes) -> list[dict]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        evt = json.loads(raw)
        if evt.get("type") != "net.probe":
            return []

        return [
            {
                "host": {
                    "ip": evt.get("ip"),
                    "mac": evt.get("mac"),
                    "vendor": evt.get("vendor"),
                },
                "network": {
                    "iface": evt.get("iface"),
                    "ssid": evt.get("ssid"),
                },
                "sources": ["bettercap"],
                "first_seen": evt.get("ts"),
                "last_seen": evt.get("ts"),
            }
        ]
