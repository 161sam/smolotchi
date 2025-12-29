from smolotchi.core.policy import evaluate_tool_action


def test_nmap_requires_approval() -> None:
    dec = evaluate_tool_action(
        tool="nmap",
        job_kind="scan.nmap",
        scope="10.0.0.0/24",
        cfg_policy={"allowed_tools": ["nmap"]},
    )
    assert dec.requires_approval is True
    assert dec.ok is False


def test_masscan_disabled_by_default() -> None:
    dec = evaluate_tool_action(
        tool="masscan",
        job_kind="scan.masscan",
        scope="10.0.0.0/24",
        cfg_policy={"allowed_tools": ["masscan"], "enable_masscan": False},
    )
    assert dec.ok is False
    assert dec.requires_approval is False


def test_tool_not_in_allowlist_denies() -> None:
    dec = evaluate_tool_action(
        tool="bettercap",
        job_kind="scan.bettercap",
        scope="10.0.0.0/24",
        cfg_policy={"allowed_tools": ["nmap"]},
    )
    assert dec.ok is False
    assert "not allowed" in dec.reason
