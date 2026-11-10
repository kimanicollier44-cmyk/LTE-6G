"""LTE-6G - LTE to 6G internet converter (model, mapper, planner).

Package layout:
- link.py        shared Shannon + FSPL link model (LTE and 6G sides)
- profiles.py    LTE / LTE-Advanced source profiles + the 6G layers
- converter.py   the conversion: model, map, KEEP/UPGRADE/NEW/HOLD plan
- slices.py      QCI bearers -> 6G slices (LTE had no slicing)
- sandbox_api.py sandbox-api chamber, VERBATIM from MonadDB-RE
                 (sha256 28b3365c...) - samples are data only, never run
- payloads.py    conversion payloads triaged through the chamber
- honeypotx.py   HoneypotX: honeyroot-x style log analysis, no listener
- council.py     Gemini Carbon 4 Extended Thinking DECIDER + Muse advisor
- gates.py       HOLD gates for anything live
- checks.py      self-checks (`python main.py checks`)
"""
