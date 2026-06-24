# Job Application Interview Griller & Q&A Bank

An offline, agentic workflow designed to help you store, match, and tailor responses for written job application forms. It runs completely locally and offline, utilizing an agent customization environment to manage your career context and perform similarity lookups before conducting mock interviews.

## Prerequisites

1. **Agent Runner**: An editor or terminal-based agent runner that supports workspace customization rules and skills (such as **Antigravity**, **Open Code**, or **Claude Code**).
2. **Python 3.x**: Used to run local, offline similarity lookups and markdown compilations without requiring API keys or external services.

---

## Getting Started

This repository has a `.gitignore` configured to prevent your personal job application data from being pushed to Git. Before using the workflow, **you must create and initialize the following three files** at the root of the workspace:

### 1. Initialize Your Profile (`profile.json`)
This acts as your career resume context.
- Copy the provided template file:
  ```powershell
  Copy-Item profile-example.json profile.json
  ```
- Open `profile.json` and update it with your own career summary, achievements, roles, and technical skills.

### 2. Initialize the Q&A Database (`answers.json`)
This stores your approved questions and finalized responses.
- Initialize it as an empty JSON array:
  ```powershell
  "[]" | Out-File -FilePath answers.json -Encoding utf8
  ```
- Alternatively, you can copy the example database to start with sample entries:
  ```powershell
  Copy-Item answers-example.json answers.json
  ```

### 3. Initialize the Compiled Q&A Bank (`QA_BANK.md`)
This is the compiled, human-readable repository of your Q&As grouped by category.
- Compile it using the local database manager script:
  ```powershell
  python .agents/skills/interview_griller/scripts/db_manager.py compile
  ```

---

## How It Works

1. **Automatic Lookup**: When you paste a job application question into your agent-enabled editor, the agent automatically runs a similarity lookup against `answers.json` using a local TF-IDF matcher.
2. **Dynamic Grilling**: 
   - If a matching answer exists, the agent suggests adapting it.
   - If no match exists, the agent enters the **Grilling Phase**, acting as an interviewer asking you focused questions (one at a time) to extract a clean, STAR-method (Situation, Task, Action, Result) response.
3. **Written Form Optimization**: The agent ensures your final draft strictly conforms to your writing guidelines: no em-dashes, no robotic list headings, direct 1-2 sentence answers for short questions, and concise story responses under 250 words.
4. **Save, Compile & Enrich**: Once you approve the draft, the agent:
   - Saves it to `answers.json` and updates `QA_BANK.md`.
   - Extracts new accomplishments or metrics and appends them to the `"ai_extracted_facts"` array in `profile.json` (safely isolated from your manual profile).

---

## Claude Code Integration

For developers using **Claude Code**, this workspace includes a [CLAUDE.md](CLAUDE.md) file at the root:

```markdown
@.agents/AGENTS.md
```

### Why we use this configuration:
- Claude Code does not read `.agents/AGENTS.md` directly. Setting up `CLAUDE.md` with the `@.agents/AGENTS.md` syntax instructs Claude Code to import your workspace rules directly into its context.
- Using the `@` import convention is preferred over creating a filesystem symlink (e.g. `ln -s .agents/AGENTS.md CLAUDE.md`), as it is fully portable and compatible across different OS environments, particularly on Windows.

---

## CLI Command Reference

You can run these database management and quality control scripts directly in your terminal:

### Run Q&A Database Self-Tests
Verify that similarity scoring and markdown compilation function correctly:
```powershell
python .agents/skills/interview_griller/scripts/db_manager.py test
```

### Run Q&A Compliance Auditor
Deterministic and length scan of your database entries to check for rules compliance:
```powershell
python .agents/skills/qa_auditor/scripts/qa_auditor.py
```
*(To perform a full semantic review, simply ask the agent in the chat: "audit my database" or "check rules compliance").*
