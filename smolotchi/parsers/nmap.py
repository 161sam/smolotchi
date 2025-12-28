from __future__ import annotations

import time
import xml.etree.ElementTree as ET

from .base import BaseParser


class NmapParser(BaseParser):
    name = "nmap"

    def parse(self, raw: str | bytes) -> list[dict]:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        root = ET.fromstring(raw)
        out = []

        for host in root.findall("host"):
            addr = host.find("address[@addrtype='ipv4']")
            if addr is None:
                continue

            ports = []
            for p in host.findall(".//port"):
                state_node = p.find("state")
                state = state_node.get("state") if state_node is not None else None
                if state != "open":
                    continue
                svc = p.find("service")
                ports.append(
                    {
                        "port": int(p.get("portid")),
                        "proto": p.get("protocol"),
                        "state": state,
                        "service": svc.get("name") if svc is not None else None,
                        "version": svc.get("version") if svc is not None else None,
                    }
                )

            out.append(
                {
                    "host": {"ip": addr.get("addr")},
                    "ports": ports,
                    "services": list({p["service"] for p in ports if p["service"]}),
                    "sources": ["nmap"],
                    "first_seen": time.time(),
                    "last_seen": time.time(),
                }
            )

        return out
