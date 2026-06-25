---
name: qa_auditor
description: Reviews the answers database (answers.json) and audits each entry to verify compliance with all formatting, length, and narrative voice rules stated in AGENTS.md.
---

# Q&A Rules Compliance Auditor (Hybrid LLM-as-a-Judge)

This skill performs hybrid evaluation (deterministic + semantic) of Q&A pairs stored in `answers.json`. Its goal is to enforce narrative, technical, and stylistic compliance without altering semantic meaning or over-optimizing language into unnatural abstraction.

The system prioritizes:
1. **Semantic fidelity** (meaning preservation)
2. **Human readability**
3. **Senior engineering signal clarity**
4. **Controlled abstraction** (no over-engineering of language)

---

## How to Run the Auditor

### Step 1: Run the Deterministic Python Scan (Layer 1)
Execute the local Python script to perform fast, rule-based checks:
```powershell
python .agents/skills/qa_auditor/scripts/qa_auditor.py
```
This script returns a JSON array containing the formatting errors and deterministic flags for each entry, structured as follows:
```json
{
  "entry_id": 12,
  "format_errors": [],
  "word_count": 198,
  "deterministic_flags": []
}
```

### Step 2: Ingest the Guidelines & Active Data
- Read your styling rules in `AGENTS.md` at: `d:\Projects\MyBio\.agents\AGENTS.md`
- Ingest `answers.json` at: `d:\Projects\MyBio\answers.json`
- Ingest the JSON output from Step 1.

### Step 3: Perform Semantic Evaluation (Layer 2 — LLM Judge)
Evaluate each Q&A entry independently against the scoring rubric. Do NOT rewrite the text during this phase; only evaluate it.

---

## Evaluation Rubric (0–5 per dimension)

### 1. Information Density (ID)
Measures how much actionable engineering signal exists.
- **0**: No meaningful content.
- **3**: Partial technical relevance.
- **5**: Each sentence introduces a system constraint, technical decision, or operational insight.

### 2. Technical Grounding (TG)
Measures anchoring in real engineering concepts.
- **0**: Completely generic claims.
- **5**: Anchored in system boundaries, architecture tradeoffs, data modeling, access control planes, or delivery workflows.

### 3. Signal-to-Fluff Ratio (SFR)
Measures elimination of generic corporate language.
- **Allowed**: *"early-stage startups"*, *"system architecture decisions"*.
- **Penalized**: *"robust solutions"*, *"accelerate delivery"*, *"fast-paced environment"* (when ungrounded).

### 4. Context Fit (CF)
Measures relevance to the target role type, company business model, and domain constraints.
- **0**: Generic corporate response.
- **5**: Tailored to agency execution, startup ambiguity, or specific regulatory frameworks.

### 5. Clarity (CL)
Measures readability, structure, logical flow, and absence of redundancy.
- **0**: Unreadable or highly repetitive.
- **5**: Dense, punchy, and logically sound.

---

## Critical Constraints (Non-Negotiable Rules)

### 1. Semantic Preservation Rule (HARD CONSTRAINT)
The meaning of the original answer must NOT be changed during evaluation or correction.
- **Forbidden**: changing intent, adding new technical concepts not implied, increasing abstraction beyond original content.

### 2. Anti-Over-Abstraction Rule
Do not increase abstraction unless it directly reduces ambiguity.
- *Example Violation*: replacing *"clean TypeScript code"* with *"structural safety barriers"* is considered an invalid transformation unless explicitly justified by ambiguity reduction.

### 3. No Synthetic Seniority Inflation
Do NOT automatically upgrade simple phrasing into complex theoretical framing. Seniority signal comes from constraints, tradeoffs, and system ownership, not vocabulary inflation.

---

## Penalty System (Applied Post-Scoring)

Apply these reductions to the scores calculated in Layer 2:
- **Buzzword usage**: `-1` to `-2` from **Signal-to-Fluff Ratio (SFR)**
- **Repetitive sentence structure**: `-1` from **Clarity (CL)**
- **Generic startup praise**: `-2` from **Context Fit (CF)**
- **Over-abstraction rewrite tendency**: `-2` from **Technical Grounding (TG)**
- **Solution-selling / Over-explaining**: `-2` from **Technical Grounding (TG)** (veering into designing/pitching hypothetical solutions instead of focusing on actual experience, communication style, background, thought process, and fit).
- **Motivation Answer Length**: `-2` from **Clarity (CL)** (if a motivation/interest-based answer exceeds 150 words).
- **Systems vs. AI Separation**: `-2` from **Technical Grounding (TG)** (if platform scale entries include deep LLM details, or if AI capability entries repeat full system architecture descriptions).
- **Form-Optimized Word Limits**: `-2` from **Clarity (CL)** (if a general narrative/technical answer exceeds 180 words when intended for a scannable application field).
- **Loss of semantic fidelity**: **INVALID OUTPUT** (Fail the run)

---

## Output Consolidation & Reporting (Layer 3)

Compile the deterministic analysis and your semantic evaluation. The output contains two parts:

### Part 1: Structured JSON Records
Produce a structured JSON record for each analyzed entry using this format:
```json
{
  "entry_id": 1,
  "scores": {
    "information_density": 0,
    "technical_grounding": 0,
    "signal_to_fluff_ratio": 0,
    "context_fit": 0,
    "clarity": 0
  },
  "total_score": 0,
  "classification": "weak | acceptable | strong | excellent",
  "deterministic_violations": [],
  "semantic_violations": [],
  "penalties": [],
  "rationale": {
    "information_density": "",
    "technical_grounding": "",
    "signal_to_fluff_ratio": "",
    "context_fit": "",
    "clarity": ""
  }
}
```
*Scoring Classification Boundaries*:
- **Weak**: Total score $< 12$
- **Acceptable**: Total score $12$ to $17$
- **Strong**: Total score $18$ to $22$
- **Excellent**: Total score $23$ to $25$

### Part 2: Isomorphic Rewrite Module (STRICTLY OPTIONAL)
If a rewrite is suggested for a weak/acceptable entry, it must be **isomorphic in meaning space**:
- Preserve meaning exactly.
- Do not add abstractions or system design jargon not present in the original.
- Improve clarity, remove buzzwords, and reduce repetitions only.
- *Example Valid*: *"I prefer fast-paced environments."* $\rightarrow$ *"I perform well in fast-moving environments."*
- *Example Invalid*: *"I prefer fast-paced environments."* $\rightarrow$ *"I operate effectively in high-velocity system environments with rapid architectural iteration cycles."*

---

## Audit Report Format
Present the final report to the user in clean Markdown using these sections:

### Section 1 — Summary Table
- Total entries, compliance rate, and average score.

### Section 2 — Violations
- Grouped by deterministic and semantic violations.

### Section 3 — Scoring Table
- A Markdown table showing scores for all entries across all dimensions.

### Section 4 — Safe Rewrites
- Only include isomorphic rewrite suggestions if semantic preservation is guaranteed.
