# Disha

**AI-Powered Early-Warning & Counselling System for Student Dropout Prevention**

Summer School '26 · AI First Hackathon · Track: AI for Education & Skill Development
i3C · IIT Jammu · Techible

**Team Creators** — Anshika Rana (IGDTUW) · Akash Pachauri (Thapar University) · Ashish Beniwal (JK Lakshmipat University)
Contact: anshikaranaa.114@gmail.com

---

## The Problem

Institutions with a high student-to-counsellor ratio (200+ students per counsellor is common) cannot give every student individual attention. Attendance, fee records, grades, and counsellor notes typically sit in disconnected systems, so intervention is reactive rather than preventive. NCRB recorded 13,892 student suicides in 2023, a 64.9% rise over the decade — an accelerating crisis, not a slow trend. States like Rajasthan (SIH25102) now mandate proactive student-welfare tooling from institutions.

**Disha** unifies academic, financial, and wellbeing signals into a single explainable risk score per student, and routes that score through an escalating, human-supervised response pipeline — from self-serve resources at low risk, up to institutional-authority involvement at the highest risk tier.

---

## Architecture

```
Raw student data (academic / financial / wellbeing survey inputs)
        │
        ▼
 preprocessing.py ── feature engineering per model, matching each
        │             model's training-time feature schema
        ▼
 ┌─────────────────────────────────────────────────────┐
 │  Three independently-trained XGBoost classifiers      │
 │  train_dropout.py    → Dropout / Enrolled / Graduate  │
 │  train_wellbeing.py  → Low / Medium / High risk        │
 │  train_depression.py → Depression present / absent     │
 │  (SHAP explainability generated per model, see /shap)  │
 └─────────────────────────────────────────────────────┘
        │  three 0–100 scores (dropout_score, wellbeing_score, depression_score)
        ▼
 risk_fusion.py ── weighted fusion (0.4 / 0.3 / 0.3), with automatic
        │           weight renormalization if any score is unavailable
        ▼
 routing.py ── maps final_risk_score to an action tier:
        │        Tier 1 (0–10)   self-serve agentic bot
        │        Tier 2 (11–20)  targeted intervention (financial aid /
        │                        psychologist referral)
        │        Tier 3 (21–39)  escalation (teacher/advisor notified)
        │        Tier 4 (40+)    institutional authority involvement
        ▼
 rag_chatbot.py ── TF-IDF retrieval over a tier-tagged knowledge base,
        │           grounds LLM prompts (student chatbot reply +
        │           counsellor briefing) in real, retrieved resources
        │           only — never fabricated
        ▼
 guardrails.py ── every action is logged; anything reaching a third
        │          party (teacher, parent, institutional authority)
        │          always requires explicit human sign-off before
        │          being marked "approved". Append-only audit trail
        │          in audit_log.jsonl.
        ▼
 orchestration.py ── ties the full pipeline together per student, and
                      batches it across a student list — this is what
                      a weekly scheduler (cron / Task Scheduler / a
                      cloud scheduler) would invoke in production.
```

### Why three separate models instead of one

The three models are trained on three separate, unrelated public datasets (UCI dropout dataset, a general student mental-health/burnout dataset, and a Kaggle student-depression dataset). They do not share a student ID or feature schema — there is currently no single real dataset where one student has records across all three domains. `risk_fusion.py` treats each score as optional per student and renormalizes weights across whichever scores are available, so the architecture is ready for real institutional data (which would have all three signal types for the same student) without requiring a redesign. For this MVP, the pipeline is demonstrated end-to-end on hand-built synthetic student profiles — see `demo_synthetic_students.py` and the [Example Usage](#example-usage) section below.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend Components | React.js, Vite, Space Grotesk Typography, Cyber Dark Glassmorphism CSS |
| Application API | Node.js, Express.js REST architecture |
| Database | MongoDB, Mongoose ODM (Users, Notifications) |
| System ML Service | Flask & flask-cors, transforming models into live inference REST endpoints |
| Risk classifiers | XGBoost (3 independently trained models), scikit-learn preprocessing pipelines |
| Explainability | SHAP (per-model feature importance, `/shap`, `/feature_importance`) |
| Feature engineering | pandas, scikit-learn `ColumnTransformer` |
| Risk fusion | Custom weighted-average fusion with missing-data renormalization |
| Retrieval (RAG) | TF-IDF + cosine similarity (scikit-learn) over a tier-tagged JSON knowledge base — no external vector DB required |
| LLM | Anthropic API (`anthropic` Python SDK) for counsellor briefings and student chatbot replies, grounded strictly in retrieved resources |
| Guardrails / audit | Custom human-in-the-loop review layer, append-only JSON Lines audit log |
| Orchestration | Python batch pipeline (`orchestration.py`), designed to be invoked by an external scheduler in production |

---

## Repository Structure

```
student-risk-ai-models/
├── backend/                         # Express.js Node API, MongoDB schemas & controllers
├── frontend/                        # React.js Vite Frontend (Dashboards & Simulator)
├── app.py                           # Flask backend bridging ML inference with Express
├── data/raw/                        # Training datasets (UCI, wellbeing, depression)
├── models/                          # Trained model + preprocessor pickles (joblib)
├── feature_importance/              # Per-model feature importance CSVs
├── shap/                            # SHAP summary plots per model
├── plots/ results/ reports/         # Evaluation outputs
├── preprocessing.py                 # Feature engineering + target encoding (all 3 models)
├── evaluation.py                    # Metrics, SHAP, feature selection utilities
├── train_dropout.py                 # Dropout risk classifier training
├── train_wellbeing.py               # Wellbeing risk classifier training
├── train_depression.py              # Depression risk classifier training
├── risk_fusion.py                   # Combines 3 model scores into one 0–100 score
├── routing.py                       # Maps final score → action tier (1–4)
├── knowledge_base.json              # Tier-tagged resource content (placeholder, see below)
├── rag_chatbot.py                   # RAG retrieval + grounded prompt construction
├── guardrails.py                    # Human-in-the-loop review + audit log
├── orchestration.py                 # Full pipeline, single student + batch runner
├── demo_synthetic_students.py       # Hand-built example students for end-to-end demo
├── utils.py                         # Logging, pickle I/O, JSON I/O helpers
└── requirements.txt
```

---

## Local Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Ashish-Beniwal004/student-risk-ai-models.git
cd student-risk-ai-models
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Important:** the trained models in `/models` were pickled using **scikit-learn 1.7.2**. A newer scikit-learn (e.g. 1.9.x) can load the files without erroring on import, but will fail at inference time with an `AttributeError` inside `SimpleImputer`, because internal attribute names changed between versions. Confirm your installed version matches:
> ```bash
> python -c "import sklearn; print(sklearn.__version__)"
> ```
> If it doesn't print `1.7.2`, run `pip install scikit-learn==1.7.2 --force-reinstall` before doing anything else.

### 3. (Optional) Enable live LLM calls

The RAG/prompt-construction layer works fully offline without this — `rag_chatbot.py` and `orchestration.py` build grounded prompts either way. This step is only needed if you want to actually send a constructed prompt to Claude and see a generated response via `rag_chatbot.call_llm()`.

```bash
pip install anthropic
```

Set your API key (do not commit it):
```powershell
$env:ANTHROPIC_API_KEY = "your-key-here"
```

### 4. Run the pipeline

**Start the full-stack MERN + AI Pipeline application:**
Open three separate terminals and run the following to boot the Data, API, and Interface layers:
1. `npm run dev` inside `/backend` (Runs MongoDB-backed Express Server)
2. `python app.py` at the root folder (Runs the Flask AI Microservice)
3. `npm run dev` inside `/frontend` (Runs the React.js web client)
Then visit `http://localhost:5173` to see the complete application live.

**Score three example students end-to-end and see individual + fused risk scores (Original CLI Demo):**
```bash
python demo_synthetic_students.py
```

**See RAG retrieval and grounded prompt construction for one student:**
```bash
python rag_chatbot.py
```

**Run the human-in-the-loop review flow (CLI approve/reject demo):**
```bash
python guardrails.py
```

**Run the full pipeline (risk scoring → routing → RAG → guardrails) across all three demo students, as a scheduler would invoke it weekly:**
```bash
python orchestration.py
```

---

## Example Usage

Output from `python demo_synthetic_students.py`, showing the fused risk score for three hand-built example students spanning the full tier range:

```
Student 1 (expected: low risk)
------------------------------
  Dropout score:     4.56
  Wellbeing score:   0.00
  Depression score:  5.86
  FINAL RISK SCORE:  3.58        → Tier 1 (self-serve support)

Student 2 (expected: medium risk)
---------------------------------
  Dropout score:     22.37
  Wellbeing score:   0.83
  Depression score:  27.69
  FINAL RISK SCORE:  17.50       → Tier 2 (targeted intervention)

Student 3 (expected: high risk)
-------------------------------
  Dropout score:     97.67
  Wellbeing score:   99.97
  Depression score:  99.39
  FINAL RISK SCORE:  98.88       → Tier 4 (institutional authority involvement)
```

Running `python orchestration.py` on the same three students shows the full pipeline in action — each student's tier determines exactly which actions fire (a Tier 1 student only gets a self-serve chatbot reply; a Tier 4 student additionally triggers a counsellor briefing, a teacher/advisor notification, and an institutional authority alert, each independently logged and routed through the guardrail review step before being marked approved).

---

## Live Demo / Build

No hosted live demo link yet — this is a locally-runnable MVP at this stage of development (backend pipeline complete; dashboard/frontend and deployment are listed under Roadmap below). See the demo video for a full walkthrough of the pipeline running end-to-end.

---

## Known Limitations & Ethical Considerations

We're documenting these explicitly rather than glossing over them, since we think that's more useful to judges (and to us) than pretending the MVP is further along than it is.

- **No unified real-student dataset yet.** The three models are trained on three separate public datasets with no shared student ID. The fusion layer is built to handle real institutional data (one student, three real signal types) once available, but is currently demonstrated on synthetic composite profiles.
- **Tier thresholds are illustrative, not yet statistically calibrated.** The 0–10 / 11–20 / 21–39 / 40+ boundaries come from the original project proposal, not from an analysis of real score distributions. Early testing showed two students with meaningfully different severity could both land in Tier 4 under stress-tested synthetic inputs; recalibration against a larger, more realistic student sample is a clear next step.
- **Wellbeing model may have a target-leakage-style issue.** In `preprocessing.py`, `encode_wellbeing_target()` has a fallback branch that derives the training label directly from `mental_health_index` — a feature also included in the model's input features. If the training dataset lacked a `risk_level` column and this fallback fired, the model may have partly learned a near-deterministic rule on a single feature rather than a genuinely learned risk pattern. This needs verification against the actual training run before the wellbeing score should be trusted at face value.
- **CV/OCR behavioral modules are roadmap only, not built.** The original proposal describes an optional computer-vision layer for classroom engagement signals. This was intentionally not built for the MVP — facial-recognition-based monitoring of students raises real consent, accuracy, and bias concerns that need institutional review, not a hackathon-timeframe implementation. If pursued later, it should remain a clearly opt-in, institution-approved enhancement module, not a core dependency.
- **Parent/guardian notification is defined but not automatically triggered.** `guardrails.py` includes a `PARENT_NOTIFICATION` action type, but firing it requires knowing whether a student is a minor or has consented to family involvement — data this pipeline does not currently model. Left as a deliberate gap rather than an assumed default.
- **The CLI review step is a stand-in for a real counsellor dashboard.** `guardrails.py`'s approve/reject flow demonstrates the human-in-the-loop concept; a production system would replace this with an actual dashboard UI, with the same underlying policy logic.
- **No real scheduler is wired up.** `orchestration.py`'s batch runner is what a scheduler (cron, Windows Task Scheduler, or a cloud scheduler) would invoke weekly in production; actual scheduling infrastructure is out of scope for this MVP.
- **Knowledge base content is placeholder.** `knowledge_base.json` contains illustrative institutional resources (scholarship funds, counseling center booking, escalation contacts) clearly marked as placeholders. Real deployment requires real institutional resource details.

---

## Roadmap

- Frontend dashboard (counsellor prioritized list, SHAP drill-down) and student-facing chatbot UI
- Backend API wrapping the pipeline for a real frontend to call
- Recalibrate tier thresholds against a larger, realistic score distribution
- Verify and, if needed, retrain the wellbeing model to remove the target-leakage-style fallback
- Real scheduler integration for the weekly batch run
- Optional, consent-gated CV/OCR enhancement modules

---

## Phase 2: Full-Stack Web Application (MERN)

The original MVP Python machine learning pipeline has now been integrated into a complete MERN stack web application with the following additions:

### New Architecture Layers
- **Express / Node.js Backend**: A secure REST API that brokers interactions between the frontend, the MongoDB database, and the Flask ML inference service. Features JWT authentication, role-based middleware, and custom alert orchestration.
- **React + Vite Frontend**: A modern, interactive web interface utilizing a premium "Cyber Dark Glassmorphism" aesthetic. Contains custom hooks, context providers, and responsive role-based layouts.
- **MongoDB Database**: Persistent storage for Users (Students, Teachers, Authorities) and Notifications, complete with a seeder script (`backend/seed.js`) to instantly populate the environment.

### Key Web Features
- **Role-Based Access & Dashboards**:
  - `STUDENT`: Views their personal notifications and overall academic standing.
  - `TEACHER`: Monitors their assigned classes, issues warnings, and manages interventions.
  - `AUTHORITY`: System-wide analytics and top-level intervention tracking.
- **Live AI Simulator Modal**: A frontend component where Teachers and Authorities can input potential student variables (Attendance, CGPA, etc.) to simulate risk. Includes an **Assigned Mode** that allows them to run the AI prediction strictly on a specific student via their email and department.
- **Automated Alerting**: If an assigned prediction runs successfully, the system immediately computes the result and dispatches a persistent database notification directly to the matched student's dashboard.

