---
name: interview_griller
description: Intercepts and matches job application questions against answered ones, registers profile context, and conducts interactive grilling sessions.
---

# Interview Griller Custom Skill

This skill is designed to manage the Q&A database and conduct interactive interview grilling.

## Executing Commands

When this skill is active, you have access to the local Python script `db_manager.py` located at `d:\Projects\MyBio\.agents\skills\interview_griller\scripts\db_manager.py`.

### 1. Perform Q&A Database Lookup
Always run this command when a new question is introduced to see if we already have a similar answer:
```powershell
python .agents/skills/interview_griller/scripts/db_manager.py lookup "<question>"
```

### 2. Save an Answered Question
When the user approves a final response draft, write it back to `answers.json` and automatically recompile `QA_BANK.md`:
```powershell
python .agents/skills/interview_griller/scripts/db_manager.py add "<question>" "<answer>" --tags "<tag1,tag2>"
```
*Note: Make sure to wrap the arguments in double quotes and properly escape any embedded double quotes in the shell invocation.*

### 3. Read Profile Context
Read `profile.json` at the start of a grilling session to customize the interview questions:
- Path: `d:\Projects\MyBio\profile.json`

## Grilling Workflow Guidance
- Read `profile.json` to familiarize yourself with the user's projects, technologies, and target roles.
- Ask one question at a time.
- For behavioral questions, structure the interview to extract the STAR components:
  - **Situation**: What was the context/problem?
  - **Task**: What was the user's specific responsibility?
  - **Action**: What did the user do (focusing on their individual contribution)?
  - **Result**: What was the quantitative or qualitative outcome?
- Once the interview is complete, synthesize the inputs into a polished response and present it to the user.

### Handling Role and Company Specific Templates
- **Detection**: Intercept questions mentioning "this company", "this role", "why us", etc.
- **JD Request**: Prompt the user to provide the Job Description and Company details.
- **Extraction**: Extract core responsibilities, tech stack requirements, and company domain keywords.
- **Lookup**: Use these extracted terms to run a keyword search via `db_manager.py lookup` to locate similar past templates.
- **Save Format**: Save finalized responses as structured questions:
  - Role Fit: `Role Fit: [Role Title] requiring [Key Requirements & Tech Stack]` (Tags: `RoleFit`, `[Role Title]`, `[Core Tech]`)
  - Company Fit: `Company Fit: [Company Name] operating in [Domain/Industry/Core Business]` (Tags: `CompanyFit`, `[Company Name]`, `[Domain Tag]`)
