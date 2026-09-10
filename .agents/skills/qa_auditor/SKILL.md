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

## Evaluation Rubric (100-point scale)

### 1. Technical Depth (Max 25)
Measures architectural clarity, design patterns, and handling of concurrency/distributed workflows.
- **0**: Completely generic description with no engineering depth.
- **15**: Uses terms like "APIs" or "databases" but lacks structural details.
- **25**: Anchored in explicit abstractions, connection pool routing, event streams, or durable state machines.

### 2. Technology Alignment (Max 15)
Measures how explicitly the requested stack is mapped to real-world achievements.
- **0**: Requested tools are mentioned as buzzwords or missing entirely.
- **15**: Each requested technology (e.g. TypeScript, React, NestJS, AWS) is directly connected to a concrete component, interface, or execution pattern.

### 3. Problem Framing (Max 10)
Measures the clarity of the technical, operational, or business bottleneck.
- **0**: Vague or missing problem context.
- **10**: Outlines a clear, relatable pain point (e.g., tight coupling slowing delivery, manual ingestion bottleneck).

### 4. Ownership & Leadership (Max 15)
Measures technical leadership, alignment, collaboration, or team-level velocity gains.
- **0**: Purely passive individual delivery task description.
- **15**: Explains how you led the team, standardizing patterns, driving ADR alignment, or mentoring junior developers.

### 5. Solution Quality & Trade-offs (Max 10)
Measures technical decision-making and architectural tradeoffs.
- **0**: Unjustified architectural decisions.
- **10**: Explicitly details the tradeoff chosen (e.g., modular adapter pattern vs. separate microservices) and explains the "why."

### 6. Impact & Outcomes (Max 15)
Measures concrete, business-grounded results or operational improvements.
- **0**: No stated outcomes or generic claims of success.
- **15**: Connects the solution to tangible velocity gains, manual workload reduction (e.g., 90% support reduction), or scaling capacity.

### 7. Communication & Scannability (Max 10)
Measures logical flow, punchy phrasing, and scannable written layout.
- **0**: Highly dense, repetitive, or whitepaper-style prose.
- **10**: Structured for 30-60 second scan limits with conversational yet professional engineer-to-engineer phrasing.

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
- **Repetitive sentence structure**: `-3` from **Communication & Scannability**
- **Generic startup praise**: `-3` from **Communication & Scannability**
- **Over-abstraction rewrite tendency**: `-5` from **Technical Depth**
- **Solution-selling / Over-explaining**: `-5` from **Technical Depth** (veering into designing/pitching hypothetical solutions instead of focusing on actual experience, communication style, background, thought process, and fit).
- **Motivation Answer Length**: `-5` from **Communication & Scannability** (if a motivation/interest-based answer exceeds 150 words).
- **Systems vs. AI Separation**: `-5` from **Technical Depth** (if platform scale entries include deep LLM details, or if AI capability entries repeat full system architecture descriptions).
- **Form-Optimized Word Limits**: `-5` from **Communication & Scannability** (if a general narrative/technical answer exceeds 180 words when intended for a scannable application field).
- **Concrete API Grounding**: `-5` to `-10` from **Technical Depth** (if an API or system description remains entirely abstract, lacking at least one concrete endpoint or CRUD example).
- **Subjective Language check**: `-3` from **Communication & Scannability** (if subjective adjectives like "complex" or "robust" are used to describe implementations).
- **Scaling Metrics Precision**: `-5` from **Technical Depth** (using generic claims like "concurrent client requests" instead of concrete capacity terms like "enterprise workloads").
- **Storytelling vs. Corporate/Whitepaper Voice**: `-5` from **Communication & Scannability** (if the response reads like an overly formal technical whitepaper or a dry corporate status update instead of a personal, conversational story centered on problem, decision, and impact).
- **Senior/Staff Maturity Signal**: Up to `+5` bonus (max score 100) or no penalty (if the response correctly frames legacy/refactoring work around understanding system evolution, complexity sources, and safe abstraction design, showing operational design pragmatism and connecting backend choices to UX outcomes).
   - *Technology & Stack Signals*: Verify that technology gaps are bridged with transferable cross-stack ownership by leading with adjacent strengths rather than starting with a flat negative sentence. Ensure frontend contexts are described using natural client-side terms (e.g., validation, caching, network traffic reduction) rather than forced server/database scale jargon.
   - *AI Tool Accountability*: Ensure Q&As describing AI tools or agent integrations frame output verification around junior-developer code reviews and rigorous validation (tests/linters/edge cases). Verify that human control is described using professional governance terms (human accountability, human-in-the-loop, approval gates) and that automation outcomes are mapped directly to unit economics (marginal costs, reduced coordination overhead, and platform resilience as profit levers).
   - *Fintech System Design*: Verify that backoffice/financial architectures evaluate the "cost of error" (restricting autonomy to low-cost-of-error domains), frame batch operations (like reconciliation) as continuous platform capabilities of proactive prevention, and portray heuristics as dynamic ROI optimizers adapting to behavioral telemetry.
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
    "technical_depth": 0,
    "technology_alignment": 0,
    "problem_framing": 0,
    "ownership_leadership": 0,
    "solution_quality": 0,
    "impact_outcomes": 0,
    "communication": 0
  },
  "total_score": 0,
  "classification": "weak | acceptable | strong | excellent",
  "deterministic_violations": [],
  "semantic_violations": [],
  "penalties": [],
  "rationale": {
    "technical_depth": "",
    "technology_alignment": "",
    "problem_framing": "",
    "ownership_leadership": "",
    "solution_quality": "",
    "impact_outcomes": "",
    "communication": ""
  }
}
```
*Scoring Classification Boundaries*:
- **Weak**: Total score $< 70$
- **Acceptable**: Total score $70$ to $79$
- **Strong**: Total score $80$ to $89$
- **Excellent**: Total score $90$ to $100$

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
