"""
orchestration.py

Phase 2 Step 5: End-to-end pipeline.

WHAT THIS MODULE DOES:
  Wires the four Phase 1/2 modules into one callable sequence per student:

      risk_fusion.compute_student_risk()
              -> routing.route_student()
                      -> rag_chatbot.ResourceRetriever.retrieve() + prompt building
                              -> guardrails.submit_action() (one or more actions,
                                 cumulative by tier - see determine_actions_for_tier)

  run_weekly_batch() runs this for a list of students and is what a real
  scheduler would call once a week (see the note in __main__ below).

WHAT THIS MODULE DELIBERATELY DOES NOT DO:
  - Does not implement actual cron/Task Scheduler/cloud scheduler wiring.
    For a hackathon MVP, a callable batch function is the right scope -
    a screenshot or one line in the README saying "in production this
    is invoked weekly via [cron / Cloud Scheduler / Task Scheduler]" is
    honest and sufficient. Building real scheduling infra here would
    cost time without adding anything judges can meaningfully evaluate.
  - Does not trigger PARENT_NOTIFICATION automatically. That action type
    exists in guardrails.py but sending it requires knowing whether the
    student is a minor or has opted into family involvement - data this
    pipeline does not currently have. Documented here as a known gap
    rather than silently guessing at consent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from risk_fusion import compute_student_risk
from routing import route_student, RiskTierResult
from rag_chatbot import (
    ResourceRetriever,
    build_student_chatbot_prompt,
    build_counsellor_briefing_prompt,
)
from guardrails import submit_action, ActionType, ActionRecord


@dataclass
class StudentPipelineInput:
    student_id: str
    dropout_features_df: Optional[pd.DataFrame]
    wellbeing_features_df: Optional[pd.DataFrame]
    depression_features_df: Optional[pd.DataFrame]
    student_query: str  # what the student typed to the chatbot, or a
                        # standard weekly check-in prompt if this run
                        # isn't triggered by a live conversation


@dataclass
class StudentPipelineResult:
    student_id: str
    tier_result: RiskTierResult
    actions: list[ActionRecord]


# ---------------------------------------------------------------------------
# ESCALATION POLICY: which action types fire at which tier.
# Cumulative by design - see module docstring for rationale.
# ---------------------------------------------------------------------------
def determine_actions_for_tier(tier: int) -> list[ActionType]:
    actions = [ActionType.STUDENT_CHATBOT_REPLY]
    if tier >= 2:
        actions.append(ActionType.COUNSELLOR_BRIEFING)
    if tier >= 3:
        actions.append(ActionType.TEACHER_NOTIFICATION)
    if tier >= 4:
        actions.append(ActionType.INSTITUTIONAL_AUTHORITY_ALERT)
    return actions


def run_pipeline_for_student(
    student_input: StudentPipelineInput,
    models_dir: str,
    retriever: ResourceRetriever,
) -> StudentPipelineResult:
    """
    Runs the full pipeline for one student and returns every action
    submitted (auto-approved or pending review - check each record's
    .status). Does not perform review itself - that's a separate step,
    done via guardrails.review_action_cli() for the demo, or a real
    dashboard in production.
    """
    # 1. Score the student across the three independent models
    risk_result = compute_student_risk(
        dropout_features_df=student_input.dropout_features_df,
        wellbeing_features_df=student_input.wellbeing_features_df,
        depression_features_df=student_input.depression_features_df,
        models_dir=models_dir,
    )

    # 2. Determine tier + primary driver
    tier_result = route_student(risk_result, student_id=student_input.student_id)

    # 3. Retrieve tier-appropriate resources, grounded by the primary driver
    resources = retriever.retrieve(
        student_input.student_query,
        max_tier=tier_result.tier,
        primary_driver=tier_result.primary_driver,
    )

    # 4. Submit every action this tier calls for
    actions: list[ActionRecord] = []
    for action_type in determine_actions_for_tier(tier_result.tier):
        if action_type == ActionType.STUDENT_CHATBOT_REPLY:
            content = build_student_chatbot_prompt(student_input.student_query, tier_result, resources)
            recipient = "student"
        elif action_type == ActionType.COUNSELLOR_BRIEFING:
            content = build_counsellor_briefing_prompt(tier_result, resources)
            recipient = "counsellor"
        elif action_type == ActionType.TEACHER_NOTIFICATION:
            content = (
                f"Student {tier_result.student_id} has reached Tier {tier_result.tier} "
                f"(score {tier_result.final_risk_score:.1f}/100), primary driver: "
                f"{tier_result.primary_driver}. Recommend a check-in conversation."
            )
            recipient = "assigned_faculty_advisor"
        elif action_type == ActionType.INSTITUTIONAL_AUTHORITY_ALERT:
            content = (
                f"Student {tier_result.student_id} has reached Tier {tier_result.tier} "
                f"(score {tier_result.final_risk_score:.1f}/100), primary driver: "
                f"{tier_result.primary_driver}. Recommend institutional review."
            )
            recipient = "dean_of_students_office"
        else:
            continue  # PARENT_NOTIFICATION and anything else: not auto-triggered, see docstring

        record = submit_action(
            student_id=tier_result.student_id,
            tier=tier_result.tier,
            action_type=action_type,
            recipient=recipient,
            content=content,
        )
        actions.append(record)

    return StudentPipelineResult(
        student_id=student_input.student_id,
        tier_result=tier_result,
        actions=actions,
    )


def run_weekly_batch(
    students: list[StudentPipelineInput],
    models_dir: str,
) -> list[StudentPipelineResult]:
    """
    Runs the pipeline for every student in the list. This is the
    function a real scheduler (cron / Windows Task Scheduler / a
    cloud scheduler like GCP Cloud Scheduler or AWS EventBridge)
    would call once a week in production - it is not itself a
    scheduler, it's what the scheduler triggers.
    """
    retriever = ResourceRetriever()  # loaded once, reused across all students
    results = []
    for student_input in students:
        result = run_pipeline_for_student(student_input, models_dir, retriever)
        results.append(result)
    return results


if __name__ == "__main__":
    # Demo: run the batch for the same three synthetic students used in
    # demo_synthetic_students.py, then print a summary. This simulates
    # what "the weekly scheduled run" produces, before any human review.
    from pathlib import Path
    from demo_synthetic_students import (
        build_dropout_row, build_wellbeing_row, build_depression_row,
        student_1_dropout_raw, student_1_wellbeing_raw, student_1_depression_raw,
        student_2_dropout_raw, student_2_wellbeing_raw, student_2_depression_raw,
        student_3_dropout_raw, student_3_wellbeing_raw, student_3_depression_raw,
    )

    ROOT = Path(__file__).resolve().parent
    MODELS_DIR = str(ROOT / "models")

    students = [
        StudentPipelineInput(
            student_id="student_1_low_risk",
            dropout_features_df=build_dropout_row(student_1_dropout_raw),
            wellbeing_features_df=build_wellbeing_row(student_1_wellbeing_raw),
            depression_features_df=build_depression_row(student_1_depression_raw),
            student_query="Just checking in, things are going okay this week.",
        ),
        StudentPipelineInput(
            student_id="student_2_medium_risk",
            dropout_features_df=build_dropout_row(student_2_dropout_raw),
            wellbeing_features_df=build_wellbeing_row(student_2_wellbeing_raw),
            depression_features_df=build_depression_row(student_2_depression_raw),
            student_query="I'm a bit stressed about upcoming exams and money.",
        ),
        StudentPipelineInput(
            student_id="student_3_high_risk",
            dropout_features_df=build_dropout_row(student_3_dropout_raw),
            wellbeing_features_df=build_wellbeing_row(student_3_wellbeing_raw),
            depression_features_df=build_depression_row(student_3_depression_raw),
            student_query="I've been feeling really overwhelmed and behind on everything lately.",
        ),
    ]

    print("Running weekly batch pipeline for 3 students...")
    print("(In production, this run would be triggered by a scheduler - "
          "cron, Windows Task Scheduler, or a cloud scheduler - not run manually.)\n")

    results = run_weekly_batch(students, MODELS_DIR)

    for result in results:
        print(f"\n{result.student_id}")
        print(f"  Dropout score:     {result.tier_result.score_breakdown.get('dropout_score')}")
        print(f"  Wellbeing score:   {result.tier_result.score_breakdown.get('wellbeing_score')}")
        print(f"  Depression score:  {result.tier_result.score_breakdown.get('depression_score')}")
        print(f"  Final risk score:  {result.tier_result.final_risk_score:.1f}/100")
        print(f"  Tier: {result.tier_result.tier} - {result.tier_result.tier_label}")
        print(f"  Primary driver: {result.tier_result.primary_driver}")
        print(f"  Actions submitted: {len(result.actions)}")
        for action in result.actions:
            print(f"    - {action.action_type.value}: {action.status.value}")

    print("\nAll actions logged to audit_log.jsonl.")
    print("Review pending actions separately with guardrails.get_pending_actions() "
          "(e.g. from a counsellor dashboard) - this batch run does not review anything itself.")