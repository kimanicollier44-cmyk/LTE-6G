"""HOLD gates: actions this system will never do autonomously.

Modelling, mapping and planning a conversion are always allowed.
Touching a live carrier network, live spectrum or live subscribers
is HOLD, and needs Darion's explicit approval.
"""
from __future__ import annotations

HOLD_GATES = [
    ("live_carrier_conversion", "Converting a live carrier network from LTE to 6G"),
    ("live_subscriber_cutover", "Cutting live subscribers over to a converted cell"),
    ("rf_spectrum_transmission", "Transmitting on real RF / sub-THz / THz spectrum"),
    ("spectrum_license_bypass", "Bypassing spectrum licensing for the 6G layers"),
    ("radio_firmware_flashing", "Flashing radio / baseband firmware to 'make it 6G'"),
    ("physical_6g_claim", "Claiming a physical 6G link exists where only a model ran"),
    ("live_network_reconfiguration", "Reconfiguring a live network autonomously"),
    ("user_traffic_routing", "Routing real user traffic through the converter"),
    ("core_network_migration_live", "Migrating a live EPC core to a 6G core"),
    ("live_sample_detonation", "Detonating a live/unknown sample outside the static sandbox-api chamber"),
    ("live_honeypot_listener", "Opening a live HoneypotX listener or deploying it on a public host"),
    ("satellite_uplink", "Transmitting to a satellite as part of a conversion"),
    ("safety_critical_control", "Controlling medical / safety-critical systems over a converted link"),
    ("live_gemini_api_call", "Calling the live Gemini / Carbon 4 API with a real key"),
]

_GATE_NAMES = {name for name, _ in HOLD_GATES}


class HoldGate(Exception):
    pass


def check(action: str) -> None:
    if action in _GATE_NAMES:
        raise HoldGate(f"HOLD: {action} requires Darion's explicit approval")


def is_held(action: str) -> bool:
    return action in _GATE_NAMES


def list_gates() -> list[dict]:
    return [{"gate": name, "description": desc} for name, desc in HOLD_GATES]
