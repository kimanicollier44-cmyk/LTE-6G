"""Conversion-payload triage through the sandbox-api chamber.

Every payload that enters the LTE->6G converter passes through the
chamber first. The chamber (lte6g/sandbox_api.py, copied VERBATIM
from Darion's MonadDB-RE implementation of his credkellar/sandbox-api
merge, sha256 28b3365c04660270... identical in all three projects)
treats each payload as DATA ONLY: never executed, network attempts
always 0.

This module supplies the payload set and the static analyser the
chamber runs: a marker scan. Dangerous markers (eval/exec, shell,
raw sockets, pipe-to-shell) -> HOLD_IN_CHAMBER. Clean conversion
payloads -> ALLOW_STATIC_STUDY.
"""
from __future__ import annotations

from .sandbox_api import detonate_static

DANGER_MARKERS = {
    "eval(": "eval_call",
    "exec(": "exec_call",
    "os.system": "shell_command",
    "subprocess": "subprocess",
    "socket.connect": "raw_socket_connect",
    "| sh": "pipe_to_shell",
    "rm -rf": "destructive_delete",
}

PAYLOADS: list[dict] = [
    {"name": "lte-cell-config",
     "data": b'{"band": "B3", "freq_mhz": 1800, "carrier_mhz": 20, "mimo": "2x2"}'},
    {"name": "qci-bearer-map",
     "data": b'{"qci": 1, "service": "voice", "to_slice": "URLLC++"}'},
    {"name": "conversion-plan",
     "data": b'{"keep": ["fibre", "sim", "anchor-band"], "add_layers_ghz": [60, 140, 300]}'},
    {"name": "6g-slice-policy",
     "data": b'{"slice": "eMBB+", "peak_tbps": 1.0, "latency_ms": 1.0}'},
    {"name": "payload-eval-marker",
     "data": b'{"action": "run", "code": "eval(user_input)"}'},
    {"name": "payload-socket-attempt",
     "data": b'{"action": "exfil", "code": "socket.connect((host, 4444))"}'},
    {"name": "payload-shell-command",
     "data": b'{"action": "setup", "code": "os.system(cleanup)"}'},
]


def analyse_payload(data: bytes) -> dict:
    """Static marker scan. This is the function the chamber runs."""
    text = data.decode("utf-8", errors="replace")
    fingerprints = [label for marker, label in DANGER_MARKERS.items() if marker in text]
    return {
        "fingerprints": fingerprints,
        "node_count": len(text.splitlines()) or 1,
        "bytes_scanned": len(data),
        "verdict": "HOLD_IN_CHAMBER" if fingerprints else "ALLOW_STATIC_STUDY",
    }


def run_chamber() -> dict:
    """Run every payload through one fresh chamber each; summarise."""
    runs = []
    for payload in PAYLOADS:
        result = detonate_static(payload["name"], payload["data"], analyse_payload)
        report, telemetry = result["report"], result["telemetry"]
        runs.append({
            "name": payload["name"],
            "verdict": report["verdict"],
            "fingerprints": report["fingerprints"],
            "executed_sample_code": telemetry["executed_sample_code"],
            "network_attempts": telemetry["network_attempts"],
            "sha256": telemetry["sha256"][:16],
        })
    held = [r for r in runs if r["verdict"] == "HOLD_IN_CHAMBER"]
    return {
        "chamber": "sandbox-api (static, never executes)",
        "total": len(runs),
        "allowed": len(runs) - len(held),
        "held": len(held),
        "all_executed": any(r["executed_sample_code"] for r in runs),
        "total_network_attempts": sum(r["network_attempts"] for r in runs),
        "runs": runs,
    }
