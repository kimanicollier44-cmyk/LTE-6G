"""LTE source profiles - typical 3GPP LTE / LTE-Advanced configurations.

Two representative deployed LTE profiles:

- ``lte``           : classic LTE, Band 3 (1.8 GHz), ONE 20 MHz carrier,
                      2 MIMO streams, 64-QAM, 2-antenna array.
- ``lte-advanced``  : LTE-Advanced Pro class, Band 7 (2.6 GHz),
                      5-carrier aggregation = 100 MHz, 4 MIMO streams,
                      256-QAM, 32-antenna FD-MIMO array.

These are peak-profile models, not a claim that every LTE cell looks
like this. Real cells vary by carrier, band and load. LTE predates
network slicing entirely - QoS runs on EPS bearers labelled by QCI
(see slices.py), and the packet core is the EPC, not a 5G/6G core.
"""
from __future__ import annotations

from .link import Band, LinkConfig

PROFILES_LTE: dict[str, LinkConfig] = {
    "lte": LinkConfig(
        generation="LTE",
        bands=[Band("LTE-B3-1800", 1.8, 0.02)],
        mimo_streams=2, antennas=2,
        overhead=0.25, max_bits_per_symbol=6.0,
        processing_ms=8.0, queueing_ms=2.0,
    ),
    "lte-advanced": LinkConfig(
        generation="LTE",
        bands=[Band("LTE-B7-2600", 2.6, 0.1)],
        mimo_streams=4, antennas=32,
        overhead=0.22, max_bits_per_symbol=8.0,
        processing_ms=8.0, queueing_ms=2.0,
    ),
}

# The 6G capacity layers a conversion ADDS. Identical trio to the
# Q6G-1TB default link (24 GHz aggregated), so a converted cell is
# directly comparable to that project.
SIXG_LAYERS = [
    Band("mmWave-60", 60.0, 2.0),
    Band("sub-THz-140", 140.0, 10.0),
    Band("THz-300", 300.0, 12.0),
]


def get_lte_profile(name: str) -> LinkConfig:
    if name not in PROFILES_LTE:
        raise ValueError(f"unknown LTE profile {name!r}; choose from {sorted(PROFILES_LTE)}")
    return PROFILES_LTE[name]


def list_profiles() -> list[dict]:
    return [{"name": name, **cfg.report()} for name, cfg in PROFILES_LTE.items()]
