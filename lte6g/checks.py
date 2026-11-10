"""Self-checks for LTE-6G. `python main.py checks` exits 0 only if all pass."""
from __future__ import annotations

from . import converter, council, gates, honeypotx, payloads, profiles, slices
from .link import LinkConfig


def run_checks() -> dict:
    results = []

    def check(name, fn):
        try:
            ok = bool(fn())
            detail = ""
        except Exception as exc:  # a failing check must report, not crash
            ok, detail = False, str(exc)
        results.append({"name": name, "passed": ok, "detail": detail})

    lte = profiles.get_lte_profile("lte")
    adv = profiles.get_lte_profile("lte-advanced")
    rep = converter.convert_profile("lte")
    rep_adv = converter.convert_profile("lte-advanced")
    chamber = payloads.run_chamber()
    honey = honeypotx.honeypotx_summary()
    mapping = slices.mapping_report()

    check("two_lte_profiles", lambda: set(profiles.PROFILES_LTE) == {"lte", "lte-advanced"})
    check("lte_is_lte_generation", lambda: lte.generation == "LTE" and adv.generation == "LTE")
    check("lte_bandwidths_real", lambda: lte.total_bandwidth_ghz == 0.02
          and adv.total_bandwidth_ghz == 0.1)
    check("converted_bandwidth_grows", lambda: rep["after_6g"]["total_bandwidth_ghz"] > 24
          and rep_adv["after_6g"]["total_bandwidth_ghz"] > 24)
    check("converted_capacity_gain_over_100x", lambda: rep["gain_at_profile_distance"]["capacity_x"] > 100
          and rep_adv["gain_at_profile_distance"]["capacity_x"] > 100)
    check("converted_latency_improves", lambda: rep["gain_at_profile_distance"]["latency_improvement_x"] > 10)
    check("anchor_band_kept", lambda: rep["after_6g"]["bands"][0] == "LTE-B3-1800")
    check("streams_and_antennas_scale", lambda: rep["after_6g"]["mimo_streams"] == 8
          and rep["after_6g"]["antennas"] == 256)
    check("distance_sweep_falls_with_distance", lambda:
          rep["distance_sweep"][0]["g6_gbps"] > rep["distance_sweep"][-1]["g6_gbps"])
    check("honesty_flags", lambda: rep["physical_conversion_by_software_alone"] is False
          and rep["modelled_not_measured"] is True)
    check("lte_had_no_slices", lambda: mapping["lte_had_slices"] is False)
    check("all_qci_mapped", lambda: mapping["all_qci_mapped"] and len(slices.QCI_MAP) == 9)
    check("q_slice_is_new", lambda: any(r["to_6g"] == "Q-SLICE" for r in slices.SLICE_MAP))
    check("plan_has_all_four_actions", lambda:
          {p["action"] for p in rep["upgrade_plan"]} == {"KEEP", "UPGRADE", "NEW", "HOLD"})
    check("chamber_triages_7", lambda: chamber["total"] == 7)
    check("chamber_allows_4_holds_3", lambda: chamber["allowed"] == 4 and chamber["held"] == 3)
    check("chamber_never_executes", lambda: chamber["all_executed"] is False
          and chamber["total_network_attempts"] == 0)
    check("honeypotx_12_attempts", lambda: honey["attempts"] == 12)
    check("honeypotx_class_counts", lambda: honey["by_class"] ==
          {"scanner": 4, "env_harvest": 3, "lfi_probe": 2, "sqli_probe": 2, "upload_attempt": 1})
    check("honeypotx_top_threat_100", lambda: honey["top_threat_score"] == 100)
    check("honeypotx_no_listener", lambda: honey["listener_open"] is False
          and honey["access_granted"] is False)
    check("hold_gates_at_least_14", lambda: len(gates.HOLD_GATES) >= 14)
    check("live_conversion_held", lambda: gates.is_held("live_carrier_conversion")
          and gates.is_held("live_honeypot_listener"))
    check("council_holds_live", lambda:
          council.council_run("convert live carrier network", risk=90)["final"] == "HOLD")
    check("council_allows_sim", lambda:
          council.council_run("run local conversion model", risk=10)["final"] == "ALLOW_SIM")
    check("council_muse_authority_none", lambda:
          council.MuseAdvisor().advise("x")["authority"] == "none"
          and len(council.MuseAdvisor().advise("x")["advice"]) == 4)
    check("linkconfig_roundtrip", lambda: isinstance(lte.at_distance(500), LinkConfig))

    passed = sum(1 for r in results if r["passed"])
    return {"checks": results, "passed": passed, "total": len(results),
            "all_passed": passed == len(results)}
