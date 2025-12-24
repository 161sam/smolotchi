from __future__ import annotations

from typing import Any, Dict
import xml.etree.ElementTree as ET


def _summarize_output(output: str, max_lines: int = 6, max_chars: int = 600) -> str:
    """
    Keep it safe & compact: strip and keep only a short snippet.
    """
    if not output:
        return ""
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    snippet = "\n".join(lines[:max_lines])
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rstrip() + "…"
    return snippet


def parse_nmap_xml_findings(xml_text: str) -> Dict[str, Any]:
    """
    Safe extraction:
      - open_ports with service product/version
      - script outputs (id, output snippet)
    Returns:
      { hosts: {ip: { ports:[...], scripts:[...] } } }
    """
    out: Dict[str, Any] = {"hosts": {}}
    if not xml_text or "<nmaprun" not in xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return out

    for host in root.findall("host"):
        status = host.find("status")
        if status is None or status.attrib.get("state") != "up":
            continue

        ip = None
        for addr in host.findall("address"):
            if addr.attrib.get("addrtype") == "ipv4":
                ip = addr.attrib.get("addr")
                break
        if not ip:
            continue

        host_obj = {"ports": [], "scripts": []}

        ports_el = host.find("ports")
        if ports_el is not None:
            for port in ports_el.findall("port"):
                proto = port.attrib.get("protocol", "")
                portid = int(port.attrib.get("portid", "0") or 0)

                state_el = port.find("state")
                if state_el is None or state_el.attrib.get("state") != "open":
                    continue

                svc_el = port.find("service")
                svc = {
                    "port": portid,
                    "proto": proto,
                    "name": (svc_el.attrib.get("name") if svc_el is not None else "") or "",
                    "product": (
                        svc_el.attrib.get("product") if svc_el is not None else ""
                    )
                    or "",
                    "version": (
                        svc_el.attrib.get("version") if svc_el is not None else ""
                    )
                    or "",
                    "extrainfo": (
                        svc_el.attrib.get("extrainfo") if svc_el is not None else ""
                    )
                    or "",
                    "tunnel": (
                        svc_el.attrib.get("tunnel") if svc_el is not None else ""
                    )
                    or "",
                }
                host_obj["ports"].append(svc)

                for script in port.findall("script"):
                    sid = script.attrib.get("id", "") or "script"
                    output = (script.attrib.get("output", "") or "").strip()
                    host_obj["scripts"].append(
                        {
                            "scope": f"{proto}/{portid}",
                            "id": sid,
                            "output": _summarize_output(output),
                            "raw_len": len(output),
                        }
                    )

        for script in host.findall("hostscript/script"):
            sid = script.attrib.get("id", "") or "hostscript"
            output = (script.attrib.get("output", "") or "").strip()
            host_obj["scripts"].append(
                {
                    "scope": "host",
                    "id": sid,
                    "output": _summarize_output(output),
                    "raw_len": len(output),
                }
            )

        host_obj["ports"].sort(key=lambda x: (x.get("proto", ""), x.get("port", 0)))
        host_obj["scripts"].sort(key=lambda x: (x.get("scope", ""), x.get("id", "")))

        out["hosts"][ip] = host_obj

    return out
