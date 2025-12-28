from __future__ import annotations

import json
import time

from .base import BaseParser


class MasscanParser(BaseParser):
    name = "masscan"

    def parse(self, raw: str | bytes) -> list[dict]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        data = json.loads(raw)
        hosts: dict[str, dict] = {}

        for entry in data:
            ip = entry["ip"]
            hosts.setdefault(
                ip,
                {
                    "host": {"ip": ip},
                    "ports": [],
                    "services": [],
                    "sources": ["masscan"],
                    "first_seen": time.time(),
                },
            )
            hosts[ip]["ports"].append(
                {
                    "port": entry["port"],
                    "proto": entry["proto"],
                    "state": "open",
                    "service": None,
                    "version": None,
                }
            )

        now = time.time()
        for host in hosts.values():
            host["last_seen"] = now

        return list(hosts.values())
