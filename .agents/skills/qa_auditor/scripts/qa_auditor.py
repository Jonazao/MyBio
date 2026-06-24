import os
import sys
import json
import re
import argparse
import tempfile
from typing import Dict, Any, Optional

# --- Constants ---
DEFAULT_ANSWERS_FILE = "answers.json"
MAX_DIRECT_WORDS = 100
MAX_NARRATIVE_WORDS = 250
DIRECT_QUESTION_LENGTH_THRESHOLD = 8
DIRECT_QUESTION_TAGS = {"collaboration", "direct", "quick"}

# Common robotic bold headers (e.g. **Situation:** or **Situation**:)
ROBOTIC_HEADERS_REGEX = re.compile(
    r'\*\*(situation|task|action|result|internal|production|why)\s*.*?(:\*\*|\*\*:)',
    re.IGNORECASE
)
# Generic bold headers starting a paragraph (e.g., "**Context:**" or "**Context**:")
GENERIC_BOLD_START = re.compile(r'^\s*\*\*.*?(:\*\*|\*\*:)', re.MULTILINE)


def audit_database(answers_path: str) -> Optional[Dict[str, Any]]:
    """Audits the Q&A database for style and format violations.

    Args:
        answers_path: Absolute or relative path to the answers JSON file.

    Returns:
        Optional[Dict[str, Any]]: The compliance report on success, or None on failure.
    """
    if not os.path.exists(answers_path):
        print(
            json.dumps({"status": "error", "message": f"File not found at {answers_path}"}, indent=2),
            file=sys.stderr
        )
        return None
        
    try:
        with open(answers_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception as e:
        print(
            json.dumps({"status": "error", "message": f"Failed to parse JSON: {str(e)}"}, indent=2),
            file=sys.stderr
        )
        return None

    if not isinstance(db, list):
        print(
            json.dumps({"status": "error", "message": "Invalid database format: root element must be a JSON array."}, indent=2),
            file=sys.stderr
        )
        return None

    violations = []
    total_q = len(db)
    clean_q = 0
    
    for idx, item in enumerate(db):
        if not isinstance(item, dict):
            violations.append({
                "index": idx,
                "question": "<Invalid Item>",
                "word_count": 0,
                "errors": ["Item is not a JSON object"]
            })
            continue

        q_text = str(item.get("question", ""))
        a_text = str(item.get("answer", ""))
        
        # Safely convert tags to a list of lowercase strings
        raw_tags = item.get("tags")
        if isinstance(raw_tags, list):
            tags = [str(t).lower() for t in raw_tags if t is not None]
        else:
            tags = []
        
        errors = []
        
        # 1. Check for em-dashes
        if "—" in a_text or "\u2014" in a_text:
            errors.append("Contains em-dashes (—)")
            
        # 2. Check for robotic bold subheadings
        if ROBOTIC_HEADERS_REGEX.search(a_text) or GENERIC_BOLD_START.search(a_text):
            errors.append("Contains robotic bold subheadings (e.g. **Header**:)")
            
        # 3. Check length constraints
        word_count = len(a_text.split())
        
        # Direct questions check
        is_direct = (
            any(t in DIRECT_QUESTION_TAGS for t in tags) or 
            len(q_text.split()) < DIRECT_QUESTION_LENGTH_THRESHOLD
        )
        
        if is_direct and word_count > MAX_DIRECT_WORDS:
            errors.append(f"Direct Q&A answer is too long ({word_count} words; limit is {MAX_DIRECT_WORDS})")
        elif word_count > MAX_NARRATIVE_WORDS:
            errors.append(f"Answer exceeds word count recommendation ({word_count} words; recommended max is {MAX_NARRATIVE_WORDS})")
            
        if errors:
            violations.append({
                "index": idx,
                "question": q_text[:60] + "..." if len(q_text) > 60 else q_text,
                "word_count": word_count,
                "errors": errors
            })
        else:
            clean_q += 1
            
    compliance_score = round((clean_q / total_q) * 100, 2) if total_q > 0 else 100.0
    
    report = {
        "status": "success",
        "total_questions": total_q,
        "clean_questions": clean_q,
        "compliance_score_percent": compliance_score,
        "violations": violations
    }
    
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def run_tests() -> None:
    """Executes unit tests for the database style auditor."""
    print("Running qa_auditor.py self-test suite...")
    
    # Test case 1: Completely clean Q&A
    clean_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "When starting a task, I collaborate with stakeholders to align on goals. I resolve alignment issues by presenting data-backed options. This establishes velocity and reduces coordination overhead.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 2: Em-dash violation
    em_dash_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "I talk to stakeholders—they usually have different timelines—and resolve it.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 3: Robotic subheadings violation (colon inside bold)
    robotic_db_inside = [
        {
            "question": "How do you handle conflicts?",
            "answer": "**Situation:** Stakeholder had a conflict. **Action:** I aligned them.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 4: Robotic subheadings violation (colon outside bold)
    robotic_db_outside = [
        {
            "question": "How do you handle conflicts?",
            "answer": "**Situation**: Stakeholder had a conflict. **Action**: I aligned them.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 5: Direct Q&A too long (>100 words)
    long_direct_db = [
        {
            "question": "Quick question?",
            "answer": " ".join(["word"] * 105),
            "tags": ["quick"]
        }
    ]
    
    # Test case 6: Narrative Q&A too long (>250 words)
    long_narrative_db = [
        {
            "question": "Tell me about a very long project that you worked on last year.",
            "answer": " ".join(["word"] * 260),
            "tags": ["narrative"]
        }
    ]

    def run_audit_on_db(db_data):
        fd, temp_path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(db_data, f)
            # Redirect stdout to capture/mute report dump during assertions
            import io
            from contextlib import redirect_stdout
            f_out = io.StringIO()
            with redirect_stdout(f_out):
                res = audit_database(temp_path)
            return res
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Verification
    report = run_audit_on_db(clean_db)
    assert report is not None, "Clean DB should audit successfully"
    assert report["compliance_score_percent"] == 100.0, "Clean DB compliance should be 100%"
    assert len(report["violations"]) == 0, "Clean DB should have no violations"
    print("[PASS] Test 1: Clean Q&A passed.")

    report = run_audit_on_db(em_dash_db)
    assert report is not None and len(report["violations"]) == 1, "Em-dash violation not flagged"
    assert "Contains em-dashes (—)" in report["violations"][0]["errors"][0], "Expected em-dash error message"
    print("[PASS] Test 2: Em-dash violation flagged.")

    report = run_audit_on_db(robotic_db_inside)
    assert report is not None and len(report["violations"]) == 1, "Robotic subheadings violation (inside colon) not flagged"
    assert "Contains robotic bold subheadings" in report["violations"][0]["errors"][0], "Expected robotic subheading error"
    print("[PASS] Test 3: Robotic subheadings violation (inside colon) flagged.")

    report = run_audit_on_db(robotic_db_outside)
    assert report is not None and len(report["violations"]) == 1, "Robotic subheadings violation (outside colon) not flagged"
    assert "Contains robotic bold subheadings" in report["violations"][0]["errors"][0], "Expected robotic subheading error"
    print("[PASS] Test 4: Robotic subheadings violation (outside colon) flagged.")

    report = run_audit_on_db(long_direct_db)
    assert report is not None and len(report["violations"]) == 1, "Long direct Q&A not flagged"
    assert "too long" in report["violations"][0]["errors"][0], "Expected too long direct Q&A error"
    print("[PASS] Test 5: Long direct Q&A flagged.")

    report = run_audit_on_db(long_narrative_db)
    assert report is not None and len(report["violations"]) == 1, "Long narrative Q&A not flagged"
    assert "exceeds word count recommendation" in report["violations"][0]["errors"][0], "Expected too long narrative error"
    print("[PASS] Test 6: Long narrative Q&A flagged.")

    print("All auditor tests passed successfully!")


if __name__ == "__main__":
    # Determine default path fallback
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_workspace = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    default_path = os.path.join(default_workspace, DEFAULT_ANSWERS_FILE)

    parser = argparse.ArgumentParser(description="Audit Q&A database for styling and formatting rules.")
    parser.add_argument(
        "--file", 
        type=str, 
        default=default_path,
        help="Path to the answers JSON file to audit"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-test suite"
    )
    args = parser.parse_args()

    if args.test:
        run_tests()
        sys.exit(0)

    report = audit_database(args.file)
    if report is None:
        sys.exit(1)
