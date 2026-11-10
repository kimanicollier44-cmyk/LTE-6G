"""Shared link-budget model for LTE and 6G links.

Same physics on both sides so the conversion comparison is fair:
Shannon capacity + free-space path loss (FSPL), the exact model family
used in Darion's Q6G-1TB project.

Honest scope: this is a *model*. It computes what a link configuration
would carry under stated assumptions. It does not measure a real link,
and no software converts a physical LTE radio into a 6G radio - 6G needs
new spectrum, new radio hardware and new antennas. See converter.py
for what is kept, upgraded, and newly required.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Band:
    name: str
    freq_ghz: float
    bandwidth_ghz: float

    @property
    def bandwidth_hz(self) -> float:
        return self.bandwidth_ghz * 1e9


def fspl_db(distance_m: float, freq_ghz: float) -> float:
    """Free-space path loss: 20log10(d_km) + 20log10(f_GHz) + 92.45."""
    d_km = max(distance_m, 1.0) / 1000.0
    return 20 * math.log10(d_km) + 20 * math.log10(freq_ghz) + 92.45


def beamforming_gain_db(n_antennas: int) -> float:
    return round(10 * math.log10(max(n_antennas, 1)), 2)


def shannon_efficiency(snr_db: float, max_bits_per_symbol: float) -> float:
    """Spectral efficiency (bps/Hz/stream), Shannon capped by modulation.

    LTE caps at 64-QAM = 6 bits/symbol (256-QAM = 8 in LTE-Advanced
    Pro); the 6G model caps at 4096-QAM = 12 bits/symbol (same cap
    as Q6G-1TB).
    """
    snr_linear = 10 ** (snr_db / 10)
    return min(math.log2(1 + snr_linear), max_bits_per_symbol)


@dataclass
class LinkConfig:
    """One aggregated radio link, either generation."""

    generation: str  # "LTE" or "6G"
    bands: list[Band] = field(default_factory=list)
    mimo_streams: int = 4
    antennas: int = 64
    distance_m: float = 100.0
    overhead: float = 0.20
    base_snr_db: float = 20.0
    max_bits_per_symbol: float = 8.0
    processing_ms: float = 0.9
    queueing_ms: float = 0.09

    @property
    def total_bandwidth_ghz(self) -> float:
        return round(sum(b.bandwidth_ghz for b in self.bands), 3)

    def snr_at_distance(self) -> float:
        """SNR vs the 140 GHz / 100 m reference, plus beamforming gain.

        Identical formula to Q6G-1TB's LinkConfig.snr_at_distance so
        numbers from the two projects are directly comparable.
        """
        ref_loss = fspl_db(100.0, 140.0)
        loss = sum(fspl_db(self.distance_m, b.freq_ghz) for b in self.bands) / len(self.bands)
        return round(self.base_snr_db - (loss - ref_loss)
                     + beamforming_gain_db(self.antennas) - 24.08, 2)

    def capacity_bps(self) -> float:
        eff = shannon_efficiency(self.snr_at_distance(), self.max_bits_per_symbol)
        bw = self.total_bandwidth_ghz * 1e9
        return bw * eff * self.mimo_streams * (1 - self.overhead)

    def capacity_gbps(self) -> float:
        return self.capacity_bps() / 1e9

    def latency_ms(self) -> dict:
        prop = (self.distance_m / 3e8) * 1000  # one-way propagation
        total = prop + self.processing_ms + self.queueing_ms
        return {
            "propagation_ms": round(prop, 6),
            "processing_ms": self.processing_ms,
            "queueing_ms": self.queueing_ms,
            "total_ms": round(total, 4),
        }

    def at_distance(self, distance_m: float) -> "LinkConfig":
        return LinkConfig(
            generation=self.generation, bands=list(self.bands),
            mimo_streams=self.mimo_streams, antennas=self.antennas,
            distance_m=distance_m, overhead=self.overhead,
            base_snr_db=self.base_snr_db,
            max_bits_per_symbol=self.max_bits_per_symbol,
            processing_ms=self.processing_ms, queueing_ms=self.queueing_ms)

    def report(self) -> dict:
        return {
            "generation": self.generation,
            "bands": [b.name for b in self.bands],
            "total_bandwidth_ghz": self.total_bandwidth_ghz,
            "mimo_streams": self.mimo_streams,
            "antennas": self.antennas,
            "beamforming_gain_db": beamforming_gain_db(self.antennas),
            "distance_m": self.distance_m,
            "snr_db": self.snr_at_distance(),
            "spectral_efficiency_bps_hz": round(
                shannon_efficiency(self.snr_at_distance(), self.max_bits_per_symbol), 3),
            "capacity_gbps": round(self.capacity_gbps(), 2),
            "capacity_tbps": round(self.capacity_bps() / 1e12, 4),
            "latency": self.latency_ms(),
            "note": "Modelled capacity, not a measured physical link.",
        }
