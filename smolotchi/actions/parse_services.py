from __future__ import annotations

from typing import Any, Dict, List, Set
import xml.etree.ElementTree as ET


def parse_nmap_xml_services(xml_text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns:
      { "1.2.3.4": [ {port:22, proto:"tcp", name:"ssh", product:"OpenSSH", version:"9.3", tunnel:"", state:"open"} ] }
    """
    if not xml_text or "<nmaprun" not in xml_text:
        return {}
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return {}

    out: Dict[str, List[Dict[str, Any]]] = {}

    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.attrib.get("state") != "up":
            continue

        ip = None
        for address in host.findall("address"):
            if address.attrib.get("addrtype") == "ipv4":
                ip = address.attrib.get("addr")
                break
        if not ip:
            continue

        ports = host.find("ports")
        if ports is None:
            continue

        services: List[Dict[str, Any]] = []
        for port in ports.findall("port"):
            proto = port.attrib.get("protocol", "")
            portid = int(port.attrib.get("portid", "0") or 0)
            state_el = port.find("state")
            if state_el is None or state_el.attrib.get("state") != "open":
                continue

            svc = port.find("service")
            name = (svc.attrib.get("name") if svc is not None else "") or ""
            product = (svc.attrib.get("product") if svc is not None else "") or ""
            version = (svc.attrib.get("version") if svc is not None else "") or ""
            tunnel = (svc.attrib.get("tunnel") if svc is not None else "") or ""

            services.append(
                {
                    "port": portid,
                    "proto": proto,
                    "state": "open",
                    "name": name,
                    "product": product,
                    "version": version,
                    "tunnel": tunnel,
                }
            )

        if services:
            out[ip] = services

    return out


def summarize_service_keys(services: List[Dict[str, Any]]) -> Set[str]:
    """
    Produces coarse service keys for planning (ssh/http/smb/rdp/etc).
    """
    keys: Set[str] = set()
    for service in services:
        name = (service.get("name") or "").lower()
        port = int(service.get("port") or 0)
        tunnel = (service.get("tunnel") or "").lower()

        if name.startswith("http") or port in (80, 81, 443, 8080, 8443) or tunnel == "ssl":
            keys.add("http")
        if name == "ssh" or port == 22:
            keys.add("ssh")
        if name in ("microsoft-ds", "netbios-ssn") or port in (139, 445) or "smb" in name:
            keys.add("smb")
        if name == "ms-wbt-server" or port == 3389:
            keys.add("rdp")
        if name == "ftp" or port == 21:
            keys.add("ftp")

    return keys
