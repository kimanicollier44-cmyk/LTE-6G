"""Tests for LTE-6G. Run: python -m pytest tests/ -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lte6g import checks, converter, council, gates, honeypotx, payloads, profiles, slices
from lte6g.link import fspl_db, shannon_efficiency


def test_fspl_increases_with_frequency():
    assert fspl_db(100, 300) > fspl_db(100, 1.8)


def test_shannon_capped_by_modulation():
    assert shannon_efficiency(60, 6.0) == 6.0
    assert shannon_efficiency(60, 12.0) == 12.0


def test_profiles_are_lte():
    for cfg in profiles.PROFILES_LTE.values():
        assert cfg.generation == "LTE"


def test_conversion_gain():
    rep = converter.convert_profile("lte")
    assert rep["gain_at_profile_distance"]["capacity_x"] > 100
    assert rep["before_lte"]["capacity_gbps"] < rep["after_6g"]["capacity_gbps"]


def test_conversion_keeps_anchor():
    rep = converter.convert_profile("lte-advanced")
    assert rep["after_6g"]["bands"][0] == "LTE-B7-2600"
    assert rep["after_6g"]["total_bandwidth_ghz"] > 24


def test_honesty_flags():
    rep = converter.convert_profile("lte")
    assert rep["physical_conversion_by_software_alone"] is False
    assert rep["modelled_not_measured"] is True


def test_all_qci_mapped():
    assert slices.mapping_report()["all_qci_mapped"]
    assert slices.map_qci(1)["to_6g_slice"] == "URLLC++"
    assert slices.map_qci(9)["to_6g_slice"] == "eMBB+"


def test_chamber():
    result = payloads.run_chamber()
    assert result["total"] == 7 and result["allowed"] == 4 and result["held"] == 3
    assert result["all_executed"] is False and result["total_network_attempts"] == 0


def test_honeypotx():
    result = honeypotx.honeypotx_summary()
    assert result["attempts"] == 12 and result["top_threat_score"] == 100
    assert result["listener_open"] is False and result["access_granted"] is False
    assert result["by_class"]["upload_attempt"] == 1


def test_gates_hold_live():
    assert gates.is_held("live_carrier_conversion")
    assert gates.is_held("live_honeypot_listener")
    try:
        gates.check("live_carrier_conversion")
        raise AssertionError("gate did not fire")
    except gates.HoldGate:
        pass


def test_council():
    assert council.council_run("live conversion", risk=90)["final"] == "HOLD"
    assert council.council_run("local model", risk=10)["final"] == "ALLOW_SIM"
    advice = council.MuseAdvisor().advise("x")
    assert advice["authority"] == "none" and len(advice["advice"]) == 4


def test_checks_all_pass():
    result = checks.run_checks()
    assert result["all_passed"], result
