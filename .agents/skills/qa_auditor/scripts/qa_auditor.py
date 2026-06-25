import os
import sys
import json
import re
import argparse
import tempfile
from typing import Dict, List, Any, Optional

# --- Constants ---
DEFAULT_ANSWERS_FILE = "answers.json"
MAX_DIRECT_WORDS = 100
MAX_NARRATIVE_WORDS = 250
DIRECT_QUESTION_LENGTH_THRESHOLD = 8
DIRECT_QUESTION_TAGS = {"collaboration", "direct", "quick"}

ROBOTIC_HEADERS_REGEX = re.compile(
    r'\*\*(situation|task|action|result|internal|production|why)\s*.*?(:\*\*|\*\*:)',
    re.IGNORECASE
)
GENERIC_BOLD_START = re.compile(r'^\s*\*\*.*?(:\*\*|\*\*:)', re.MULTILINE)

WHITELISTED_ALL_CAPS = {
    "SOC", "HIPAA", "SaaS", "HTML", "CSS", "REST", "API", "AWS", "ADR", "ADRs",
    "STAR", "JSON", "JSONL", "TF", "IDF", "RAM", "CPU", "PR", "PRs", "UX", "UI",
    "SDK", "IT", "EM", "B2B", "CI", "CD", "NET"
}


def check_banned_punctuation(text: str) -> List[str]:
    """Checks for banned punctuation patterns."""
    errors = []
    # Space before ending punctuation or clause markers (ignoring dot prefixes like .NET)
    if re.search(r'\s+[.,!?;:](?!\w)', text):
        errors.append("Space before punctuation")
    # Repeated commas
    if re.search(r',{2,}', text):
        errors.append("Repeated commas (,,)")
    # Repeated exclamations
    if re.search(r'!{2,}', text):
        errors.append("Repeated exclamation marks (!!)")
    # Repeated question marks
    if re.search(r'\?{2,}', text):
        errors.append("Repeated question marks (??)")
    
    # Repeated periods that are not exactly three (...)
    for match in re.finditer(r'\.{2,}', text):
        dot_seq = match.group(0)
        if len(dot_seq) != 3:
            errors.append(f"Invalid punctuation sequence: '{dot_seq}'")
            break
            
    return errors


def check_excessive_capitalization(text: str) -> List[str]:
    """Checks for excessive capitalization violations, ignoring a whitelist of technical abbreviations."""
    errors = []
    # Find all words that are fully capitalized and length >= 4
    raw_words = re.findall(r'\b[A-Z]{4,}\b', text)
    for word in raw_words:
        if word not in WHITELISTED_ALL_CAPS:
            errors.append(f"Excessive capitalization: '{word}'")
    return errors


def get_sentences(text: str) -> List[str]:
    """Splits a paragraph into sentences using standard ending punctuation."""
    raw_sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in raw_sentences if s.strip()]


def check_repeated_sentence_starters(text: str) -> List[str]:
    """Flags adjacent sentences in the text that start with the same word."""
    flags = []
    sentences = get_sentences(text)
    prev_first_word = None
    
    for idx, s in enumerate(sentences):
        # Extract first word character-only
        match = re.match(r'^([a-zA-Z]+)', s)
        if match:
            first_word = match.group(1).lower()
            if prev_first_word and first_word == prev_first_word:
                flags.append(f"Repeated sentence starter '{first_word}' in adjacent sentences")
            prev_first_word = first_word
        else:
            prev_first_word = None
            
    return flags


def audit_database(answers_path: str) -> Optional[List[Dict[str, Any]]]:
    """Audits the Q&A database for Layer 1 style and format violations.

    Args:
        answers_path: Absolute or relative path to the answers JSON file.

    Returns:
        Optional[List[Dict[str, Any]]]: The compliance report per entry on success, or None on failure.
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

    results = []
    
    for idx, item in enumerate(db):
        if not isinstance(item, dict):
            results.append({
                "entry_id": idx,
                "format_errors": ["Item is not a JSON object"],
                "word_count": 0,
                "deterministic_flags": []
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
            
        format_errors = []
        deterministic_flags = []
        
        # 1. Check for em-dashes
        if "—" in a_text or "\u2014" in a_text:
            format_errors.append("Contains em-dashes (—)")
            
        # 2. Check banned punctuation
        format_errors.extend(check_banned_punctuation(a_text))
        
        # 3. Check excessive capitalization
        format_errors.extend(check_excessive_capitalization(a_text))
        
        # 4. Check length constraints
        word_count = len(a_text.split())
        is_direct = (
            any(t in DIRECT_QUESTION_TAGS for t in tags) or 
            len(q_text.split()) < DIRECT_QUESTION_LENGTH_THRESHOLD
        )
        
        if is_direct and word_count > MAX_DIRECT_WORDS:
            format_errors.append(f"Direct Q&A answer is too long ({word_count} words; limit is {MAX_DIRECT_WORDS})")
        elif word_count > MAX_NARRATIVE_WORDS:
            format_errors.append(f"Answer exceeds word count limit ({word_count} words; limit is {MAX_NARRATIVE_WORDS})")
            
        # 5. Check repeated sentence starters
        deterministic_flags.extend(check_repeated_sentence_starters(a_text))
        
        # 6. Check robotic bold subheadings
        if ROBOTIC_HEADERS_REGEX.search(a_text) or GENERIC_BOLD_START.search(a_text):
            deterministic_flags.append("Contains robotic bold subheadings (e.g. **Header**:)")
            
        results.append({
            "entry_id": idx,
            "format_errors": format_errors,
            "word_count": word_count,
            "deterministic_flags": deterministic_flags
        })
        
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return results


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
    
    # Test case 3: Space before punctuation and duplicate commas
    punctuation_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "I talk to stakeholders , they have different timelines,, and I resolve it.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 4: Double periods violation
    double_dots_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "I talk to stakeholders.. They have different timelines... Then I resolve it.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 5: Excessive capitalization (HIPAA is allowed, OVERENGINEERED is not)
    capitalization_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "I use HIPAA compliant tools but avoid OVERENGINEERED systems.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 6: Repeated sentence starters
    starters_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "I align stakeholders first. I present data-backed options next.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 7: Robotic bold subheadings
    robotic_db = [
        {
            "question": "How do you handle conflicts?",
            "answer": "**Situation**: Stakeholder had a conflict. **Action**: I aligned them.",
            "tags": ["collaboration"]
        }
    ]
    
    # Test case 8: Direct Q&A too long (>100 words)
    long_direct_db = [
        {
            "question": "Quick question?",
            "answer": " ".join(["word"] * 105),
            "tags": ["quick"]
        }
    ]

    def run_audit_on_db(db_data):
        fd, temp_path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(db_data, f)
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
    assert len(report[0]["format_errors"]) == 0, "Clean DB should have no format errors"
    assert len(report[0]["deterministic_flags"]) == 0, "Clean DB should have no flags"
    print("[PASS] Test 1: Clean Q&A passed.")

    report = run_audit_on_db(em_dash_db)
    assert report is not None and "Contains em-dashes (—)" in report[0]["format_errors"], "Em-dash violation not flagged"
    print("[PASS] Test 2: Em-dash violation flagged.")

    report = run_audit_on_db(punctuation_db)
    assert report is not None
    assert "Space before punctuation" in report[0]["format_errors"], "Space before punctuation not flagged"
    assert "Repeated commas (,,)" in report[0]["format_errors"], "Repeated commas not flagged"
    print("[PASS] Test 3: Banned punctuation (space & commas) flagged.")

    report = run_audit_on_db(double_dots_db)
    assert report is not None
    assert any("Invalid punctuation sequence" in err for err in report[0]["format_errors"]), "Double dots not flagged"
    print("[PASS] Test 4: Banned punctuation (double dots) flagged.")

    report = run_audit_on_db(capitalization_db)
    assert report is not None
    assert any("Excessive capitalization: 'OVERENGINEERED'" in err for err in report[0]["format_errors"]), "Overengineered not flagged"
    assert not any("HIPAA" in err for err in report[0]["format_errors"]), "HIPAA should be whitelisted"
    print("[PASS] Test 5: Excessive capitalization flagged (and whitelisted acronyms ignored).")

    report = run_audit_on_db(starters_db)
    assert report is not None and len(report[0]["deterministic_flags"]) == 1, "Repeated sentence starters not flagged"
    assert "Repeated sentence starter 'i'" in report[0]["deterministic_flags"][0], "Expected starter flag"
    print("[PASS] Test 6: Repeated sentence starters flagged.")

    report = run_audit_on_db(robotic_db)
    assert report is not None and "Contains robotic bold subheadings (e.g. **Header**:)" in report[0]["deterministic_flags"], "Robotic subheading not flagged"
    print("[PASS] Test 7: Robotic bold subheading flagged.")

    report = run_audit_on_db(long_direct_db)
    assert report is not None and any("too long" in err for err in report[0]["format_errors"]), "Long direct Q&A not flagged"
    print("[PASS] Test 8: Long direct Q&A length constraint flagged.")

    print("All Layer 1 auditor tests passed successfully!")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_workspace = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
    default_path = os.path.join(default_workspace, DEFAULT_ANSWERS_FILE)

    parser = argparse.ArgumentParser(description="Audit Q&A database for Layer 1 styling and formatting rules.")
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
