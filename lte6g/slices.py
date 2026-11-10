"""Bearer / QCI mapping: LTE has NO network slices - 6G creates them.

LTE QoS runs on EPS bearers labelled by QCI (1-9). There is nothing
in LTE to "rename" into a slice, so a conversion CREATES the slice
layer for the first time: each LTE service class and each QCI bearer
is assigned to a 6G slice (from the Q6G-1TB model). Q-SLICE has no
LTE source at all - it is new in 6G, keyed by BB84 QKD.
"""
from __future__ import annotations

SLICE_MAP = [
    {"from_lte": "Broadband data (default EPS bearers)", "to_6g": "eMBB+",
     "change": "Best-effort / GBR data bearers -> 1 Tbps-class slice, XR / holographic media",
     "latency_lte_ms": 10.0, "latency_6g_ms": 1.0},
    {"from_lte": "Voice + signalling (GBR bearers, QCI 1/5)", "to_6g": "URLLC++",
     "change": "VoLTE voice + IMS signalling -> 0.1 ms / 99.99999% slice, industrial control class",
     "latency_lte_ms": 10.0, "latency_6g_ms": 0.1},
    {"from_lte": "Machine-type comms (LTE-M / NB-IoT)", "to_6g": "mMTC+",
     "change": "Narrowband IoT bearers -> 10M devices/km2 massive sensing slice",
     "latency_lte_ms": 10.0, "latency_6g_ms": 10.0},
    {"from_lte": "(none - LTE has no slicing)", "to_6g": "Q-SLICE",
     "change": "NEW in 6G model: quantum-secured traffic, BB84 QKD key management",
     "latency_lte_ms": None, "latency_6g_ms": 1.0},
]

# Standardised QCI values (3GPP TS 23.203) and where each lands in 6G.
QCI_MAP = [
    {"qci": 1, "service": "Conversational voice (GBR)", "to_6g_slice": "URLLC++"},
    {"qci": 2, "service": "Conversational video (GBR)", "to_6g_slice": "eMBB+"},
    {"qci": 3, "service": "Real-time gaming (GBR)", "to_6g_slice": "URLLC++"},
    {"qci": 4, "service": "Buffered streaming video (GBR)", "to_6g_slice": "eMBB+"},
    {"qci": 5, "service": "IMS signalling", "to_6g_slice": "URLLC++"},
    {"qci": 6, "service": "TCP-based data, buffered video", "to_6g_slice": "eMBB+"},
    {"qci": 7, "service": "Voice / video interactive", "to_6g_slice": "URLLC++"},
    {"qci": 8, "service": "TCP-based data (priority)", "to_6g_slice": "eMBB+"},
    {"qci": 9, "service": "Default bearer, best-effort internet", "to_6g_slice": "eMBB+"},
]


def map_qci(qci: int) -> dict | None:
    for row in QCI_MAP:
        if row["qci"] == qci:
            return row
    return None


def mapping_report() -> dict:
    return {"slices": SLICE_MAP, "qci_bearers": QCI_MAP,
            "lte_had_slices": False,
            "all_qci_mapped": all(map_qci(r["qci"]) for r in QCI_MAP),
            "all_service_classes_mapped": all(r["to_6g"] for r in SLICE_MAP)}
