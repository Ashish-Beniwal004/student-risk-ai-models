"""
guardrails.py

Phase 2 Step 4: Human-in-the-loop review layer.

WHAT THIS MODULE DOES:
  1. Defines an ActionRecord representing anything the system wants to
     do (send a chatbot reply, notify a teacher, contact a parent,
     alert institutional authorities).
  2. Applies an explicit review policy: actions reaching a third party
     (anyone other than the student themselves) ALWAYS require human
     sign-off before sending, regardless of tier. Lower-stakes,
     student-only actions at Tier 1 can be auto-approved.
  3. Provides a CLI-based approve/reject step for the hackathon demo.
     This is a deliberate stand-in for a real counsellor dashboard —
     swap review_action_cli() for a dashboard button later without
     touching submit_action() or the policy logic.
  4. Persists every action (auto-approved or reviewed) to an
     append-only audit log (audit_log.jsonl), so there's always a
     record of what was proposed, by whom it was reviewed, and when.

WHAT THIS MODULE DELIBERATELY DOES NOT DO:
  - Does not actually send emails/messages. "Sent" here just means
    the action was approved and marked as ready to send — wiring to
    a real email/SMS/dashboard API is a separate, later integration
    step, kept out of this module on purpose so the review logic
    stays testable and provider-independent.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

AUDIT_LOG_PATH = Path(__file__).resolve().parent / "audit_log.jsonl"


class ActionType(str, Enum):
    STUDENT_CHATBOT_REPLY = "student_chatbot_reply"
    COUNSELLOR_BRIEFING = "counsellor_briefing"
    TEACHER_NOTIFICATION = "teacher_notification"
    PARENT_NOTIFICATION = "parent_notification"
    INSTITUTIONAL_AUTHORITY_ALERT = "institutional_authority_alert"


class ActionStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ActionRecord:
    action_id: str
    student_id: Optional[str]
    tier: int
    action_type: ActionType
    recipient: str          # e.g. "student", "teacher:advisor_id", "parent:contact_id", "dean_of_students"
    content: str
    status: ActionStatus
    created_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None


# ---------------------------------------------------------------------------
# REVIEW POLICY
# Explicit and centralized on purpose - this is the single place that
# decides what needs a human, so it's easy to explain and easy to audit.
# ---------------------------------------------------------------------------
def requires_human_review(action_type: ActionType, tier: int) -> bool:
    # Anything reaching someone other than the student always needs review,
    # regardless of tier - the student didn't necessarily consent to that
    # contact, so a human must confirm it's warranted.
    third_party_actions = {
        ActionType.TEACHER_NOTIFICATION,
        ActionType.PARENT_NOTIFICATION,
        ActionType.INSTITUTIONAL_AUTHORITY_ALERT,
    }
    if action_type in third_party_actions:
        return True

    # Counsellor briefings are informational and consumed by the
    # counsellor themselves - no separate review needed before they see it.
    if action_type == ActionType.COUNSELLOR_BRIEFING:
        return False

    # Student chatbot replies: auto-approve only at the lowest tier
    # (self-serve, low stakes). Tier 2+ replies may reference sensitive
    # topics (financial aid, psychologist referral) - require review.
    if action_type == ActionType.STUDENT_CHATBOT_REPLY:
        return tier >= 2

    return True  # default to safe: review required for anything unclassified


def _append_to_log(record: ActionRecord) -> None:
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record)) + "\n")


def submit_action(
    student_id: Optional[str],
    tier: int,
    action_type: ActionType,
    recipient: str,
    content: str,
) -> ActionRecord:
    """
    Main entry point. Call this whenever the system wants to do
    something (send a chatbot reply, notify a teacher, etc.). Returns
    the resulting ActionRecord - check its `.status` to know whether
    it's ready to act on immediately (AUTO_APPROVED) or needs review
    (PENDING_REVIEW).
    """
    needs_review = requires_human_review(action_type, tier)
    record = ActionRecord(
        action_id=str(uuid.uuid4()),
        student_id=student_id,
        tier=tier,
        action_type=action_type,
        recipient=recipient,
        content=content,
        status=ActionStatus.PENDING_REVIEW if needs_review else ActionStatus.AUTO_APPROVED,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _append_to_log(record)
    return record


def review_action_cli(record: ActionRecord, reviewer: str) -> ActionRecord:
    """
    Hackathon-demo stand-in for a counsellor dashboard approve/reject
    button. Prompts in the terminal. Replace this function's internals
    with a real dashboard action later - submit_action() and the
    policy above don't need to change.
    """
    if record.status != ActionStatus.PENDING_REVIEW:
        print(f"Action {record.action_id} is not pending review (status: {record.status}). Skipping.")
        return record

    print(f"\n--- ACTION PENDING REVIEW ---")
    print(f"Student: {record.student_id}  |  Tier: {record.tier}  |  Type: {record.action_type.value}")
    print(f"Recipient: {record.recipient}")
    print(f"Content:\n{record.content}\n")

    decision = input("Approve this action? [y/n]: ").strip().lower()
    notes = input("Optional review notes (press Enter to skip): ").strip()

    record.status = ActionStatus.APPROVED if decision == "y" else ActionStatus.REJECTED
    record.reviewed_by = reviewer
    record.reviewed_at = datetime.now(timezone.utc).isoformat()
    record.review_notes = notes or None

    _append_to_log(record)  # log the reviewed state as a new line - the log is append-only history
    return record


def get_pending_actions() -> list[ActionRecord]:
    """
    Reads the audit log and returns actions currently awaiting review -
    i.e. the most recent record per action_id, where that latest
    record's status is still PENDING_REVIEW.
    """
    if not AUDIT_LOG_PATH.exists():
        return []

    latest_by_id: dict[str, dict] = {}
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            latest_by_id[entry["action_id"]] = entry  # later lines overwrite earlier ones

    pending = []
    for entry in latest_by_id.values():
        if entry["status"] != ActionStatus.PENDING_REVIEW.value:
            continue
        # json.dumps wrote these as plain strings (since ActionType/ActionStatus
        # are str-based enums) - convert them back to real enum members here,
        # otherwise .value calls downstream (e.g. in review_action_cli) fail
        # with AttributeError on a plain str.
        entry = dict(entry)
        entry["action_type"] = ActionType(entry["action_type"])
        entry["status"] = ActionStatus(entry["status"])
        pending.append(ActionRecord(**entry))

    return pending


if __name__ == "__main__":
    # Demo: wire routing.py + rag_chatbot.py output through the
    # guardrail layer end-to-end.
    from routing import route_student
    from rag_chatbot import ResourceRetriever, build_student_chatbot_prompt, build_counsellor_briefing_prompt

    example_risk_result = {
        "dropout_score": 15.0,
        "wellbeing_score": 68.0,
        "depression_score": 55.0,
        "final_risk_score": 46.0,
    }
    tier_result = route_student(example_risk_result, student_id="demo_student_1")

    retriever = ResourceRetriever()
    student_query = "I've been feeling really overwhelmed and behind on everything lately."
    resources = retriever.retrieve(
        student_query, max_tier=tier_result.tier, primary_driver=tier_result.primary_driver
    )

    # Action 1: student chatbot reply (auto-approved only at Tier 1, else needs review)
    chatbot_prompt = build_student_chatbot_prompt(student_query, tier_result, resources)
    action_1 = submit_action(
        student_id=tier_result.student_id,
        tier=tier_result.tier,
        action_type=ActionType.STUDENT_CHATBOT_REPLY,
        recipient="student",
        content=chatbot_prompt,
    )
    print(f"Action 1 ({action_1.action_type.value}) status: {action_1.status.value}")

    # Action 2: counsellor briefing (never needs review - counsellor is the consumer)
    briefing_prompt = build_counsellor_briefing_prompt(tier_result, resources)
    action_2 = submit_action(
        student_id=tier_result.student_id,
        tier=tier_result.tier,
        action_type=ActionType.COUNSELLOR_BRIEFING,
        recipient="counsellor",
        content=briefing_prompt,
    )
    print(f"Action 2 ({action_2.action_type.value}) status: {action_2.status.value}")

    # Action 3: this student's tier is 4, so simulate an institutional authority alert
    # - this ALWAYS requires review regardless of tier or content.
    alert_content = (
        f"Student {tier_result.student_id} has reached Tier 4 (score "
        f"{tier_result.final_risk_score:.1f}/100), primary driver: "
        f"{tier_result.primary_driver}. Recommend institutional review."
    )
    action_3 = submit_action(
        student_id=tier_result.student_id,
        tier=tier_result.tier,
        action_type=ActionType.INSTITUTIONAL_AUTHORITY_ALERT,
        recipient="dean_of_students_office",
        content=alert_content,
    )
    print(f"Action 3 ({action_3.action_type.value}) status: {action_3.status.value}")

    submitted_this_run = [action_1, action_2, action_3]
    pending_this_run = [a for a in submitted_this_run if a.status == ActionStatus.PENDING_REVIEW]

    print(f"\n{len(pending_this_run)} action(s) from this run need review.")
    print("(Note: audit_log.jsonl may also contain older pending actions from "
          "previous runs - those aren't reviewed here. Use get_pending_actions() "
          "separately, e.g. in a real dashboard, to see the full backlog.)\n")
    print("Run the CLI review step now:\n")

    for pending in pending_this_run:
        review_action_cli(pending, reviewer="demo_counsellor")

    print(f"\nAudit log written to: {AUDIT_LOG_PATH}")