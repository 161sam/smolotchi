from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List, Set


def parse_nmap_xml_up_hosts(xml_text: str) -> List[str]:
    """
    Extract IPv4 addresses of hosts with <status state="up"> from Nmap XML.
    """
    if not xml_text or "<nmaprun" not in xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    hosts: List[str] = []
    seen: Set[str] = set()

    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.attrib.get("state") != "up":
            continue

        addr = None
        for address in host.findall("address"):
            if address.attrib.get("addrtype") == "ipv4":
                addr = address.attrib.get("addr")
                break
        if addr and addr not in seen:
            seen.add(addr)
            hosts.append(addr)

    return hosts
