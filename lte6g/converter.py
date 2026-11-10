"""The converter: an LTE profile in, a 6G conversion out.

What "converting LTE to 6G" honestly means, in three parts:

1. MODEL - recompute the same cell on the 6G link model: the LTE
   band is kept as the coverage anchor, the three 6G capacity
   layers (60 / 140 / 300 GHz) are aggregated on top, MIMO streams
   scale x4 (capped at 8), the antenna array is replaced by a
   256-element array, modulation cap rises to 4096-QAM, overhead
   falls to 15%, and the latency budget drops from LTE's ~10 ms
   class to the 6G targets from Q6G-1TB (0.0703 ms at 100 m).
2. MAP - create the slice layer LTE never had: QCI bearers and
   LTE service classes are assigned to 6G slices (see slices.py),
   and the EPC core is replaced by a 6G core in the plan.
3. PLAN - list what a real conversion keeps, upgrades, must add
   new, and what stays on HOLD. Software alone does NOT convert a
   physical radio: ``physical_conversion_by_software_alone`` is
   False everywhere in this project, on purpose. Every conversion
   payload is triaged through the sandbox-api chamber first, and
   HoneypotX watches the converter's doors (see payloads.py and
   honeypotx.py).
"""
from __future__ import annotations

from .link import LinkConfig
from .profiles import SIXG_LAYERS, get_lte_profile
from .slices import QCI_MAP, SLICE_MAP

DISTANCES_M = [10, 100, 500, 1000]


def convert_link(src: LinkConfig) -> LinkConfig:
    """Apply the conversion rules to one LTE link configuration."""
    bands = list(src.bands) + list(SIXG_LAYERS)  # LTE anchor + 6G layers
    return LinkConfig(
        generation="6G",
        bands=bands,
        mimo_streams=min(8, src.mimo_streams * 4),
        antennas=256,
        distance_m=src.distance_m,
        overhead=0.15,
        base_snr_db=src.base_snr_db,
        max_bits_per_symbol=12.0,
        processing_ms=0.05,
        queueing_ms=0.02,
    )


def upgrade_plan(src: LinkConfig, dst: LinkConfig) -> list[dict]:
    """KEEP / UPGRADE / NEW / HOLD checklist for a real conversion."""
    return [
        {"action": "KEEP", "item": "Fibre backhaul",
         "detail": "Capacity headroom permitting, the fibre plant carries over."},
        {"action": "KEEP", "item": "Subscriber identity (SIM / USIM)",
         "detail": "Identities migrate at the core; no new SIM is modelled here."},
        {"action": "KEEP", "item": f"Coverage anchor band ({src.bands[0].name})",
         "detail": "The LTE band stays as the wide-coverage layer under the 6G cell."},
        {"action": "KEEP", "item": "Site, power and tower",
         "detail": "Physical site is reused; power budget must be re-checked for THz radios."},
        {"action": "UPGRADE", "item": f"Antenna array {src.antennas} -> {dst.antennas} elements",
         "detail": "LTE arrays cannot beamform at sub-THz; a 256-element array replaces them."},
        {"action": "UPGRADE", "item": f"MIMO streams {src.mimo_streams} -> {dst.mimo_streams}",
         "detail": "Spatial streams scale x4, capped at 8 in this model."},
        {"action": "UPGRADE", "item": "eNodeB -> 6G base station (baseband + radios)",
         "detail": "New baseband for aggregated 24+ GHz channel bandwidth."},
        {"action": "UPGRADE", "item": "Packet core EPC -> 6G core",
         "detail": "Two core generations skipped in one step; bearers become slices per slices.py."},
        {"action": "NEW", "item": "Network slicing (LTE has none)",
         "detail": "eMBB+ / URLLC++ / mMTC+ are created from QCI classes; nothing is renamed."},
        {"action": "NEW", "item": "Sub-THz radio units (140 / 300 GHz)",
         "detail": "No LTE radio transmits there. New hardware, new type approval."},
        {"action": "NEW", "item": "Spectrum licence for 60 / 140 / 300 GHz layers",
         "detail": "Licensing is a regulator step, never a software setting."},
        {"action": "NEW", "item": "Q-SLICE key management (BB84 QKD)",
         "detail": "The slice with no LTE equivalent; keys managed per Q6G-1TB."},
        {"action": "HOLD", "item": "Live subscriber cutover",
         "detail": "Migrating real subscribers on a live carrier network is HOLD-gated."},
        {"action": "HOLD", "item": "Live RF transmission on 6G layers",
         "detail": "Transmitting on real spectrum is HOLD-gated. This tool models only."},
    ]


def convert_profile(name: str, distance_m: float = 100.0) -> dict:
    """Full conversion report for one named LTE profile."""
    src = get_lte_profile(name).at_distance(distance_m)
    dst = convert_link(src)
    sweep = []
    for d in DISTANCES_M:
        s = src.at_distance(d)
        t = dst.at_distance(d)
        sweep.append({
            "distance_m": d,
            "lte_gbps": round(s.capacity_gbps(), 3),
            "g6_gbps": round(t.capacity_gbps(), 2),
            "gain_x": round(t.capacity_gbps() / s.capacity_gbps(), 1)
            if s.capacity_gbps() else None,
        })
    return {
        "profile": name,
        "physical_conversion_by_software_alone": False,
        "modelled_not_measured": True,
        "before_lte": src.report(),
        "after_6g": dst.report(),
        "gain_at_profile_distance": {
            "capacity_x": round(dst.capacity_gbps() / src.capacity_gbps(), 1),
            "bandwidth_x": round(dst.total_bandwidth_ghz / src.total_bandwidth_ghz, 1),
            "latency_before_ms": src.latency_ms()["total_ms"],
            "latency_after_ms": dst.latency_ms()["total_ms"],
            "latency_improvement_x": round(
                src.latency_ms()["total_ms"] / dst.latency_ms()["total_ms"], 1),
        },
        "distance_sweep": sweep,
        "slice_mapping": SLICE_MAP,
        "qci_mapping": QCI_MAP,
        "upgrade_plan": upgrade_plan(src, dst),
    }


def convert_all(distance_m: float = 100.0) -> dict:
    from .profiles import PROFILES_LTE
    return {"profiles": {name: convert_profile(name, distance_m)
                         for name in PROFILES_LTE},
            "physical_conversion_by_software_alone": False,
            "modelled_not_measured": True}
