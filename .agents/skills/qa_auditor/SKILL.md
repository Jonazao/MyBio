---
name: qa_auditor
description: Reviews the answers database (answers.json) and audits each entry to verify compliance with all formatting, length, and narrative voice rules stated in AGENTS.md.
---

# Q&A Rules Compliance Auditor

This skill provides a hybrid auditing system (deterministic checks + semantic analysis) to verify that all Q&A pairs comply with the workspace guidelines.

## How to Run the Auditor

### Step 1: Run the Deterministic Python Scan
Execute the local Python script to check for raw formatting violations (such as em-dashes, robotic bold subheadings, and basic word count violations):
```powershell
python .agents/skills/qa_auditor/scripts/qa_auditor.py
```
This script returns a JSON report containing formatting errors and word counts.

### Step 2: Read the Q&A Database and Rules
- Read `answers.json` at: `d:\Projects\MyBio\answers.json`
- Read your styling rules in `AGENTS.md` at: `d:\Projects\MyBio\.agents\AGENTS.md`

### Step 3: Perform Semantic/Narrative Review
For each Q&A in the database, evaluate the text against the narrative rules:
- **Storytelling vs. Corporate Voice**: Does the response read like a personal story of a problem observed, the action taken, and the lesson learned? Mark it as a violation if it sounds like a corporate project status report (e.g. using administrative terms like "rollout management").
- **Upfront Answers**: Check if the core sub-questions of the prompt (such as "what was your first action?") are answered explicitly in the first paragraph.
- **Outcome Focus**: Verify that the outcome is concise and focused on the main topic, rather than branching into a lengthy secondary story.
- **Staff-Level Vocabulary**: Verify that the answer uses high-leverage phrasing (such as "initiatives" instead of "features").

### Step 4: Compile and Present the Report
Synthesize the Python script violations and your semantic analysis into a clean markdown audit report:
1. Show a summary table of the database status (total questions, clean questions, compliance score).
2. Detail any violations found (question index, question text, formatting errors, and narrative errors).
3. **Draft corrections**: For any violating Q&A, provide a recommended corrected draft that fully complies with all rules, and ask the user if they would like to apply the corrections.
