"""
rag_chatbot.py

Phase 2 Step 3: RAG-grounded chatbot for student-facing and
counsellor-facing responses.

Design choice: uses TF-IDF similarity (via scikit-learn, already a
project dependency) rather than a vector database. This is a
deliberate, defensible choice for a hackathon MVP - no external
services, no embedding API cost, fully reproducible offline. It can
be swapped for a proper embedding-based vector store later without
changing anything outside this file, since retrieve() is the only
function other modules call.

WHAT THIS MODULE DOES:
  1. Loads the tier-tagged knowledge base (knowledge_base.json)
  2. Retrieves the most relevant resources for a student's situation,
     filtered to their tier (from routing.py) or lower tiers
  3. Constructs a grounded prompt combining: student risk context
     (from risk_fusion.py), the routing tier (from routing.py), and
     retrieved resource content
  4. Exposes a call_llm() function as a clearly separated, swappable
     piece - the RAG/grounding logic works independently of which
     LLM provider is used.

WHAT THIS MODULE DELIBERATELY DOES NOT DO:
  - Does not decide whether to actually send anything to the student/
    counsellor/parent - that's Step 4 (guardrails / human-in-the-loop)
  - Does not fabricate resources; if nothing relevant is retrieved,
    it says so rather than letting the LLM improvise unfounded advice
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from routing import RiskTierResult

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / "knowledge_base.json"


class ResourceRetriever:
    """Loads the knowledge base once and serves TF-IDF-ranked retrieval."""

    def __init__(self, kb_path: Path = KNOWLEDGE_BASE_PATH):
        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.entries = data["entries"]

        # Build the TF-IDF index over "title + content + tags" for each entry
        corpus = [
            f"{e['title']} {e['content']} {' '.join(e['tags'])}"
            for e in self.entries
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(
        self,
        query: str,
        max_tier: int,
        top_k: int = 3,
    ) -> list[dict]:
        """
        Returns up to top_k resource entries most relevant to `query`,
        restricted to entries with tier <= max_tier (a Tier 3 student
        can still see Tier 1/2 self-help resources alongside escalation
        content; a Tier 1 student never sees Tier 3/4 content).
        """
        eligible_indices = [
            i for i, e in enumerate(self.entries) if e["tier"] <= max_tier
        ]
        if not eligible_indices:
            return []

        query_vec = self.vectorizer.transform([query])
        eligible_matrix = self.matrix[eligible_indices]
        similarities = cosine_similarity(query_vec, eligible_matrix).flatten()

        ranked = sorted(
            zip(eligible_indices, similarities),
            key=lambda pair: pair[1],
            reverse=True,
        )
        top_matches = [idx for idx, score in ranked[:top_k] if score > 0]
        return [self.entries[i] for i in top_matches]


def build_student_chatbot_prompt(
    student_query: str,
    tier_result: RiskTierResult,
    retrieved_resources: list[dict],
) -> str:
    """
    Constructs the grounded prompt for the STUDENT-facing chatbot.
    Tone: supportive, non-clinical, never presents itself as a
    diagnostic authority. Only references retrieved resources -
    does not invent institutional details.
    """
    if retrieved_resources:
        resource_block = "\n".join(
            f"- {r['title']}: {r['content']}" for r in retrieved_resources
        )
    else:
        resource_block = "(No specific matching resource found - respond supportively and suggest the student speak with their academic advisor for personalized help.)"

    prompt = f"""You are a supportive academic assistant for students. You are not a \
therapist or medical professional, and must never present yourself as one. \
Your job is to point students toward real, institute-approved resources and \
keep the conversation warm, practical, and non-judgmental.

RULES:
- Only recommend resources listed below. Do not invent programs, contacts, or policies.
- Never diagnose or label the student's mental state.
- If the student's message suggests they may be in crisis, do not attempt to handle \
this yourself - respond with care and clearly point them to the Student Counseling \
Center's immediate booking option, without waiting for further conversation.
- Keep responses concise and actionable.

RELEVANT RESOURCES:
{resource_block}

STUDENT MESSAGE:
{student_query}

Respond directly to the student now.
"""
    return prompt


def build_counsellor_briefing_prompt(
    tier_result: RiskTierResult,
    retrieved_resources: list[dict],
) -> str:
    """
    Constructs the grounded prompt for the COUNSELLOR-facing briefing.
    Tone: factual, structured, cites which model score(s) drove the
    flag. This is what a counsellor sees before deciding on next
    steps - it informs, it does not act on its own.
    """
    breakdown_lines = []
    for key, value in tier_result.score_breakdown.items():
        if key == "final_risk_score" or value is None:
            continue
        breakdown_lines.append(f"  - {key.replace('_', ' ').title()}: {value:.1f}/100")
    breakdown_block = "\n".join(breakdown_lines) if breakdown_lines else "  (no individual scores available)"

    if retrieved_resources:
        resource_block = "\n".join(
            f"- {r['title']}: {r['content']}" for r in retrieved_resources
        )
    else:
        resource_block = "(No tier-matched resource found in the knowledge base for this case.)"

    prompt = f"""You are drafting a factual briefing for a student support counsellor. \
Do not soften or exaggerate the data. Do not offer a clinical diagnosis. Present the \
risk pattern plainly and suggest which of the listed resources may be relevant, but \
make clear the counsellor makes the final call on next steps.

STUDENT ID: {tier_result.student_id}
FINAL RISK SCORE: {tier_result.final_risk_score:.1f}/100
TIER: {tier_result.tier} - {tier_result.tier_label}
PRIMARY DRIVER: {tier_result.primary_driver or "Not available"}

SCORE BREAKDOWN:
{breakdown_block}

RELEVANT INSTITUTIONAL RESOURCES:
{resource_block}

Write a concise briefing (4-6 sentences) a counsellor can read in under 30 seconds \
before deciding how to proceed.
"""
    return prompt


def call_llm(prompt: str, model: str = "claude-sonnet-4-6") -> str:
    """
    Thin wrapper around the Anthropic API. Kept separate from prompt
    construction so the LLM provider/model can change without touching
    any RAG or grounding logic above.

    Requires ANTHROPIC_API_KEY to be set in the environment.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for call_llm(). "
            "Install with: pip install anthropic"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Set it in your environment "
            "before calling call_llm()."
        )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    # Manual smoke test - does not call the LLM, just checks retrieval
    # and prompt construction work end-to-end.
    from routing import route_student

    retriever = ResourceRetriever()

    example_risk_result = {
        "dropout_score": 15.0,
        "wellbeing_score": 68.0,
        "depression_score": 55.0,
        "final_risk_score": 46.0,
    }
    tier_result = route_student(example_risk_result, student_id="demo_student_1")

    print(f"Tier: {tier_result.tier} - {tier_result.tier_label}\n")

    student_query = "I've been feeling really overwhelmed and behind on everything lately."
    resources = retriever.retrieve(student_query, max_tier=tier_result.tier)

    print("Retrieved resources:")
    for r in resources:
        print(f"  - [{r['tier']}] {r['title']}")

    print("\n--- STUDENT CHATBOT PROMPT ---\n")
    print(build_student_chatbot_prompt(student_query, tier_result, resources))

    print("\n--- COUNSELLOR BRIEFING PROMPT ---\n")
    print(build_counsellor_briefing_prompt(tier_result, resources))