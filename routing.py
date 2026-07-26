"""
routing.py

Takes the output of risk_fusion.compute_student_risk() and determines
which action tier a student falls into, based on the thresholds
described in the Disha pitch deck:

    0-10   -> Tier 1: self-serve agentic bot (backlog/roadmap help)
    11-20  -> Tier 2: targeted intervention (financial aid matching,
                       psychologist referral, etc.)
    21-39  -> Tier 3: escalation (teachers/parents involved)
    40+    -> Tier 4: institutional authority involvement — reserved for
                       the highest-severity, sustained-risk cases where
                       teacher/parent escalation alone (Tier 3) has not
                       been enough, or the initial score itself indicates
                       acute risk requiring institution-level response.

This module only decides WHICH tier applies and packages the context
a downstream LLM/notification step will need. It does not draft
messages or send anything — that's Phase 2 Step 3 (LLM prompts) and
Step 4 (guardrails / human-in-the-loop send step).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# TIER THRESHOLDS
# Matches the ranges described in the pitch deck. Adjust here if the
# team decides to recalibrate based on real score distributions later —
# this is the single source of truth other modules should import from,
# rather than hardcoding thresholds elsewhere.
# ---------------------------------------------------------------------------
TIER_1_MAX = 10   # 0-10: self-serve bot
TIER_2_MAX = 20   # 11-20: targeted intervention
TIER_3_MAX = 39   # 21-39: escalation (teachers/parents)
# 40+ : Tier 4, institutional authority involvement


@dataclass
class RiskTierResult:
    student_id: Optional[str]
    final_risk_score: float
    tier: int                      # 1, 2, 3, or 4
    tier_label: str                # human-readable
    primary_driver: Optional[str]  # which model score was highest, for context
    score_breakdown: dict = field(default_factory=dict)


def determine_tier(final_risk_score: float) -> tuple[int, str]:
    """Pure threshold logic. Kept separate and simple so it's easy to
    unit test and easy to explain to judges/counsellors."""
    if final_risk_score <= TIER_1_MAX:
        return 1, "Self-serve support (agentic bot, roadmap/backlog help)"
    elif final_risk_score <= TIER_2_MAX:
        return 2, "Targeted intervention (financial aid match, psychologist referral)"
    elif final_risk_score <= TIER_3_MAX:
        return 3, "Escalation (teacher + parent involvement)"
    else:
        return 4, "Institutional authority involvement (acute/sustained high risk)"


def identify_primary_driver(score_breakdown: dict) -> Optional[str]:
    """
    Given a dict like {'dropout_score': 62.0, 'wellbeing_score': 40.0,
    'depression_score': None}, returns the name of the highest available
    score, so the counsellor briefing can lead with the most relevant
    signal instead of just the blended number.
    """
    available = {
        k: v for k, v in score_breakdown.items()
        if v is not None and k != "final_risk_score"
    }
    if not available:
        return None
    return max(available, key=available.get)


def route_student(risk_result: dict, student_id: Optional[str] = None) -> RiskTierResult:
    """
    Main entry point for Phase 2 Step 1.

    risk_result: the dict returned by risk_fusion.compute_student_risk(),
    e.g. {'dropout_score': 62.0, 'wellbeing_score': 40.0,
          'depression_score': None, 'final_risk_score': 52.6}
    """
    final_score = risk_result["final_risk_score"]
    tier, tier_label = determine_tier(final_score)
    primary_driver = identify_primary_driver(risk_result)

    return RiskTierResult(
        student_id=student_id,
        final_risk_score=final_score,
        tier=tier,
        tier_label=tier_label,
        primary_driver=primary_driver,
        score_breakdown=risk_result,
    )


if __name__ == "__main__":
    # Quick manual check using the same shape of output compute_student_risk() returns.
    examples = [
        {"dropout_score": 8.0, "wellbeing_score": 12.0, "depression_score": 5.0, "final_risk_score": 8.5},
        {"dropout_score": 45.0, "wellbeing_score": 60.0, "depression_score": 30.0, "final_risk_score": 47.0},
        {"dropout_score": 30.0, "wellbeing_score": 35.0, "depression_score": 25.0, "final_risk_score": 29.5},
        {"dropout_score": 85.0, "wellbeing_score": 90.0, "depression_score": 88.0, "final_risk_score": 87.5},
    ]
    for i, ex in enumerate(examples, start=1):
        result = route_student(ex, student_id=f"demo_student_{i}")
        print(f"\nStudent {i}")
        print(f"  Final score: {result.final_risk_score}")
        print(f"  Tier: {result.tier} — {result.tier_label}")
        print(f"  Primary driver: {result.primary_driver}")