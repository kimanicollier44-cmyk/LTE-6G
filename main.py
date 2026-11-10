#!/usr/bin/env python3
"""LTE-6G - LTE to 6G Internet Converter (model, mapper, planner).

One entry point. Zero dependencies (Python stdlib only).

Usage:
  python main.py demo              # full run: convert both profiles + security + council
  python main.py convert lte       # one profile: lte | lte-advanced
  python main.py convert-all       # both profiles
  python main.py profiles          # the LTE source profiles
  python main.py slices            # QCI bearers -> 6G slices (LTE had no slicing)
  python main.py sandbox           # sandbox-api chamber: conversion payload triage
  python main.py honeypot          # HoneypotX log analysis (no listener)
  python main.py council           # Carbon 4 DECIDER + Muse advisor
  python main.py checks            # self-checks (exit 0 only if all pass)
  python main.py hold-demo         # shows a HOLD gate firing (exit 2)

Honest scope: this CONVERTER IS A MODEL. Software alone does not
convert a physical LTE radio into a 6G radio - 6G is not commercially
deployed, and a real conversion needs new spectrum, radios and
antennas. What this tool converts is the *configuration*: link model,
QoS bearers, slices and the upgrade plan.
"""
from __future__ import annotations

import argparse
import json
import sys

from lte6g import (checks, converter, council, gates, honeypotx, payloads,
                   profiles, slices)


def _print(obj) -> None:
    print(json.dumps(obj, indent=2))


def cmd_demo(_args) -> int:
    print("== 📡 LTE -> 6G CONVERSION (modelled) ==")
    for name in profiles.PROFILES_LTE:
        rep = converter.convert_profile(name)
        gain = rep["gain_at_profile_distance"]
        print(f"-- {name}: {rep['before_lte']['capacity_gbps']} Gbps LTE -> "
              f"{rep['after_6g']['capacity_gbps']} Gbps 6G "
              f"(x{gain['capacity_x']} capacity, x{gain['bandwidth_x']} bandwidth, "
              f"latency {gain['latency_before_ms']} ms -> {gain['latency_after_ms']} ms)")
    print("== 🗂️ QCI -> SLICES ==")
    _print(slices.mapping_report()["qci_bearers"])
    print("== 🧪 SANDBOX-API CHAMBER ==")
    _print(payloads.run_chamber())
    print("== 🍯 HONEYPOTX ==")
    honey = honeypotx.honeypotx_summary()
    _print({k: honey[k] for k in ("name", "mode", "listener_open", "attempts",
                                  "by_class", "top_threat_score", "bursts",
                                  "access_granted")})
    print("== 🧠 COUNCIL ==")
    _print(council.council_run("convert LTE cell in local model", risk=10))
    print(f"⛔ HOLD gates armed: {len(gates.HOLD_GATES)}")
    return 0


def cmd_convert(args) -> int:
    _print(converter.convert_profile(args.profile))
    return 0


def cmd_convert_all(_args) -> int:
    _print(converter.convert_all())
    return 0


def cmd_profiles(_args) -> int:
    _print(profiles.list_profiles())
    return 0


def cmd_slices(_args) -> int:
    _print(slices.mapping_report())
    return 0


def cmd_sandbox(_args) -> int:
    _print(payloads.run_chamber())
    return 0


def cmd_honeypot(_args) -> int:
    _print(honeypotx.honeypotx_summary())
    return 0


def cmd_council(_args) -> int:
    _print({
        "simulation_request": council.council_run("run local conversion model", risk=10),
        "live_request": council.council_run("convert live carrier network", risk=90),
    })
    return 0


def cmd_checks(_args) -> int:
    result = checks.run_checks()
    _print(result)
    print(f"CHECKS {result['passed']}/{result['total']}")
    return 0 if result["all_passed"] else 1


def cmd_hold_demo(_args) -> int:
    try:
        gates.check("live_carrier_conversion")
        print("NOT HELD (unexpected)")
        return 1
    except gates.HoldGate as exc:
        print(str(exc))
        return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="lte-6g", description=__doc__)
    sub = parser.add_subparsers(dest="cmd")
    for name, fn in [
        ("demo", cmd_demo), ("convert-all", cmd_convert_all),
        ("profiles", cmd_profiles), ("slices", cmd_slices),
        ("sandbox", cmd_sandbox), ("honeypot", cmd_honeypot),
        ("council", cmd_council), ("checks", cmd_checks),
        ("hold-demo", cmd_hold_demo),
    ]:
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
    p = sub.add_parser("convert")
    p.add_argument("profile", choices=sorted(profiles.PROFILES_LTE))
    p.set_defaults(fn=cmd_convert)
    args = parser.parse_args(argv)
    if not getattr(args, "fn", None):
        return cmd_demo(args)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
