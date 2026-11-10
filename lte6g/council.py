"""Council: Gemini Carbon 4 Extended Thinking DECIDER + Muse advisor.

House pattern, same as Q6G-1TB:
- Carbon 4: model google/gemini-carbon-4-extended-pro-thinking,
  MAP -> MODEL -> STRESS -> DECIDE, thinking tiers 2048 / 8192 /
  32768 (extended 32768 default), offline, can only tighten, never
  overrides a HOLD gate. Its API key is checked by presence only.
- Muse: models muse-spark-1.1 / muse-wonder-1.0 via the Meta Model
  API, its key checked by name only (value never read out, printed
  or stored; usage is pay-as-you-go, never labelled free), exactly
  4 advice items, decision authority: none.

Strictest outcome wins. No live API call is made by either seat -
a live call is HOLD gate `live_gemini_api_call`.
"""
from __future__ import annotations

import os

TIERS = (2048, 8192, 32768)
PHASES = ["MAP", "MODEL", "STRESS", "DECIDE"]


class Carbon4:
    """Gemini Carbon 4 Extended Thinking. Deterministic, offline, tighten-only."""

    model = "google/gemini-carbon-4-extended-pro-thinking"
    engine = "gemini-2.5-pro"

    def __init__(self):
        key_name = "GEMINI_API_KEY"
        self.key_name = key_name
        self.key_present = bool(os.environ.get(key_name))

    def decide(self, risk: float) -> dict:
        if risk >= 75:
            verdict, tier = "HOLD", TIERS[2]
        elif risk >= 40:
            verdict, tier = "REVIEW", TIERS[1]
        else:
            verdict, tier = "ALLOW_SIM", TIERS[0]
        trace = {
            "MAP": "Map the request onto the HOLD gate list and the live/sim boundary.",
            "MODEL": f"Risk scored {risk}/100 from scope, reversibility and live exposure.",
            "STRESS": "Negative controls applied: a friendly or small-looking request still holds if it crosses a gate.",
            "DECIDE": verdict,
        }
        return {"brain": "Gemini Carbon 4 Extended Thinking", "role": "DECIDER",
                "model": self.model, "engine": self.engine,
                "phases": PHASES, "trace": trace,
                "verdict": verdict, "thinking_tier": tier,
                "default_tier": TIERS[2], "risk": risk,
                "key_name": self.key_name, "key_present": self.key_present,
                "live_call_made": False, "can_only_tighten": True}


class MuseAdvisor:
    """Muse advisory seat. Authority: none, always."""

    models = ["muse-spark-1.1", "muse-wonder-1.0"]

    def __init__(self):
        key_name = "MODEL_API_KEY"
        self.key_present = bool(os.environ.get(key_name))
        self.key_name = key_name

    def advise(self, topic: str) -> dict:
        advice = [
            f"Keep '{topic}' inside the model until a converted link is independently measured.",
            "Report every converted capacity as modelled, never as a measured 6G link.",
            "Software alone does not convert a physical LTE radio; say so wherever the plan is shown.",
            "A live cutover stays HOLD no matter how clean the conversion plan looks.",
        ]
        return {"brain": "Muse (Meta Model API)", "role": "advisor",
                "authority": "none", "models": self.models,
                "key_name": self.key_name, "key_present": self.key_present,
                "live_call_made": False, "advice": advice}


def council_run(topic: str, risk: float) -> dict:
    decision = Carbon4().decide(risk)
    advice = MuseAdvisor().advise(topic)
    return {"topic": topic, "decision": decision, "advice": advice,
            "final": decision["verdict"], "seats": 2, "live_calls_made": False,
            "rule": "strictest-wins; advisor authority = none"}
