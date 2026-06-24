import os
import sys
import json
import re
import math
import tempfile
import argparse
from collections import Counter
from typing import List, Dict, Any, Set

# --- Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
DEFAULT_ANSWERS_PATH = os.path.join(WORKSPACE_DIR, "answers.json")
DEFAULT_QA_BANK_PATH = os.path.join(WORKSPACE_DIR, "QA_BANK.md")

# --- Stopwords for Similarity Engine ---
STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "arent", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "cant", "cannot", "could", 
    "couldnt", "did", "didnt", "do", "does", "doesnt", "doing", "dont", "down", "during", "each", "few", "for", 
    "from", "further", "had", "hadnt", "has", "hasnt", "have", "havent", "having", "he", "hed", "hell", "hes", 
    "her", "here", "heres", "hers", "herself", "him", "himself", "his", "how", "hows", "i", "id", "ill", "im", 
    "ive", "if", "in", "into", "is", "isnt", "it", "its", "itself", "lets", "me", "more", "most", "mustnt", "my", 
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
    "ourselves", "out", "over", "own", "same", "she", "shed", "shell", "shes", "should", "shouldnt", "so", "some", 
    "such", "than", "that", "thats", "the", "their", "theirs", "them", "themselves", "then", "there", "theres", 
    "these", "they", "theyd", "theyll", "theyre", "theyve", "this", "those", "through", "to", "too", "under", 
    "until", "up", "very", "was", "wasnt", "we", "wed", "well", "were", "weve", "werent", "what", "whats", "when", 
    "whens", "where", "wheres", "which", "while", "who", "whos", "whom", "why", "whys", "with", "wont", "would", 
    "wouldnt", "you", "youd", "youll", "youre", "youve", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: Any) -> List[str]:
    """Converts text into lowercase alphanumeric tokens, filtering out standard stopwords."""
    if not text:
        return []
    text_str = str(text).lower()
    text_str = re.sub(r'[^a-z0-9\s]', ' ', text_str)
    tokens = text_str.split()
    return [t for t in tokens if t not in STOPWORDS]


def compute_idfs(documents: List[List[str]]) -> Dict[str, float]:
    """Computes Inverse Document Frequency (IDF) for all terms in a document collection."""
    n_docs = len(documents)
    df = Counter()
    for doc in documents:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1
            
    idfs = {}
    for term, count in df.items():
        idfs[term] = math.log((1 + n_docs) / (1 + count)) + 1
    return idfs


def get_cosine_similarity(query_tokens: List[str], doc_tokens: List[str], idfs: Dict[str, float]) -> float:
    """Calculates TF-IDF cosine similarity between query and document token lists."""
    if not query_tokens or not doc_tokens:
        return 0.0
        
    query_counter = Counter(query_tokens)
    doc_counter = Counter(doc_tokens)
    vocab = set(query_tokens).union(doc_tokens)
    
    dot_product = 0.0
    query_norm_sq = 0.0
    doc_norm_sq = 0.0
    
    for t in vocab:
        idf = idfs.get(t, 1.0)
        q_tf = query_counter.get(t, 0)
        d_tf = doc_counter.get(t, 0)
        
        q_val = q_tf * idf
        d_val = d_tf * idf
        
        dot_product += q_val * d_val
        query_norm_sq += q_val * q_val
        doc_norm_sq += d_val * d_val
        
    if query_norm_sq == 0 or doc_norm_sq == 0:
        return 0.0
    return dot_product / (math.sqrt(query_norm_sq) * math.sqrt(doc_norm_sq))


def load_db(path: str = DEFAULT_ANSWERS_PATH) -> List[Dict[str, Any]]:
    """Loads the database of Q&A pairs. Returns an empty list if file doesn't exist or is invalid."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Warning: Failed to load database from {path}: {e}", file=sys.stderr)
        return []


def save_db(data: List[Dict[str, Any]], path: str = DEFAULT_ANSWERS_PATH) -> None:
    """Saves the Q&A database atomically to prevent file corruption."""
    dir_name = os.path.dirname(os.path.abspath(path))
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    # Write to a temporary file in the same directory, then rename to avoid truncation bugs
    fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise IOError(f"Failed to write database file atomically: {e}")


def search_questions(query: str, db: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Searches questions using cosine similarity on questions and answers."""
    if not db:
        return []
        
    query_tokens = tokenize(query)
    if not query_tokens:
        return []
        
    # Build document lists for IDF calculations safely
    q_docs = [tokenize(item.get("question", "")) for item in db]
    a_docs = [tokenize(item.get("answer", "")) for item in db]
    
    q_idfs = compute_idfs(q_docs)
    a_idfs = compute_idfs(a_docs)
    
    results = []
    for idx, item in enumerate(db):
        q_tokens = q_docs[idx]
        a_tokens = a_docs[idx]
        
        q_sim = get_cosine_similarity(query_tokens, q_tokens, q_idfs)
        a_sim = get_cosine_similarity(query_tokens, a_tokens, a_idfs)
        
        # Combined score: 70% weight on question similarity, 30% on answer similarity
        combined_score = (0.7 * q_sim) + (0.3 * a_sim)
        
        if combined_score > 0.05:  # Low similarity cutoff
            results.append({
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "tags": item.get("tags", []),
                "scores": {
                    "question_similarity": round(q_sim, 4),
                    "answer_similarity": round(a_sim, 4),
                    "combined": round(combined_score, 4)
                }
            })
            
    results.sort(key=lambda x: x["scores"]["combined"], reverse=True)
    return results


def compile_markdown(db: List[Dict[str, Any]], output_path: str = DEFAULT_QA_BANK_PATH) -> None:
    """Compiles the database into a readable Markdown index file."""
    if not db:
        markdown_content = "# Q&A Bank\n\nNo questions answered yet."
    else:
        # Group by tag
        by_tag: Dict[str, List[Dict[str, Any]]] = {}
        for item in db:
            tags = item.get("tags")
            if not isinstance(tags, list) or not tags:
                tags = ["Uncategorized"]
            for tag in tags:
                tag_name = str(tag).strip().title()
                if tag_name not in by_tag:
                    by_tag[tag_name] = []
                by_tag[tag_name].append(item)
                
        markdown_content = "# Q&A Interview Bank\n\n"
        markdown_content += "This bank contains your curated responses, organized by category. Use it to quickly locate pre-formulated experience stories and technical explanations.\n\n"
        
        # Table of Contents
        markdown_content += "## Table of Contents\n\n"
        for tag in sorted(by_tag.keys()):
            anchor = tag.lower().replace(' ', '-').replace('&', '')
            markdown_content += f"- [{tag}](#{anchor})\n"
        markdown_content += "\n---\n\n"
        
        # Content sections
        for tag in sorted(by_tag.keys()):
            markdown_content += f"## {tag}\n\n"
            for item in by_tag[tag]:
                markdown_content += f"### Q: {item.get('question', '')}\n\n"
                markdown_content += f"{item.get('answer', '')}\n\n"
                tags_list = item.get("tags")
                if isinstance(tags_list, list) and tags_list:
                    tags_str = ", ".join(f"`{t}`" for t in tags_list)
                    markdown_content += f"*Tags: {tags_str}*\n\n"
                markdown_content += "---\n\n"
                
    dir_name = os.path.dirname(os.path.abspath(output_path))
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)


def run_tests() -> None:
    """Executes the test suite for verification."""
    print("Running db_manager.py self-test suite...")
    test_db = [
        {
            "question": "Tell me about a time you had a conflict with a stakeholder.",
            "answer": "I had a conflict with a project manager about timelines. I resolved it by presenting a data-backed plan using the STAR method.",
            "tags": ["Conflict", "Behavioral"]
        },
        {
            "question": "How do you optimize page load times in React?",
            "answer": "I use lazy loading, code splitting, memoization, and image optimization to improve Web Vitals.",
            "tags": ["React", "Performance"]
        },
        {
            "question": "Describe a difficult technical challenge you solved.",
            "answer": "We had a race condition in our payment service. I solved it using Redis distributed locks.",
            "tags": ["Technical", "Concurrency"]
        }
    ]
    
    # Test 1: Exact question match
    res1 = search_questions("Tell me about a conflict with a stakeholder", test_db)
    assert len(res1) > 0, "Test 1 Failed: No matches found"
    assert res1[0]["question"] == test_db[0]["question"], f"Test 1 Failed: Top match was {res1[0]['question']}"
    print("[PASS] Test 1: Exact question match passed.")
    
    # Test 2: Phrase/synonym match
    res2 = search_questions("how to speed up react application load speed", test_db)
    assert len(res2) > 0, "Test 2 Failed: No matches found"
    assert "React" in res2[0]["tags"], "Test 2 Failed: Top match did not contain React"
    print("[PASS] Test 2: Synonym/concept match passed.")
    
    # Test 3: Answer keyword overlap search
    res3 = search_questions("redis race condition", test_db)
    assert len(res3) > 0, "Test 3 Failed: No matches found"
    assert "Concurrency" in res3[0]["tags"], "Test 3 Failed: Top match was not concurrency"
    print("[PASS] Test 3: Answer content overlap match passed.")
    
    # Test 4: Completely unrelated query
    res4 = search_questions("what is your favorite food", test_db)
    assert len(res4) == 0 or res4[0]["scores"]["combined"] < 0.1, f"Test 4 Failed: High score for unrelated query: {res4}"
    print("[PASS] Test 4: Unrelated query scoring passed.")
    
    # Test 5: Compile markdown
    test_md_path = "test_qa_bank.md"
    try:
        compile_markdown(test_db, test_md_path)
        assert os.path.exists(test_md_path), "Test 5 Failed: MD file not written"
        with open(test_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "React" in content, "Test 5 Failed: Content missing expected tag"
            assert "Table of Contents" in content, "Test 5 Failed: TOC missing"
        print("[PASS] Test 5: Compilation to markdown passed.")
    finally:
        if os.path.exists(test_md_path):
            os.remove(test_md_path)
            
    print("All tests passed successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Curated Q&A Database Manager for Interview Prep.")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: test
    subparsers.add_parser("test", help="Run self-test suite")

    # Command: compile
    parser_compile = subparsers.add_parser("compile", help="Recompile QA_BANK.md from answers database")
    parser_compile.add_argument("--db", type=str, default=DEFAULT_ANSWERS_PATH, help="Path to database JSON file")
    parser_compile.add_argument("--md", type=str, default=DEFAULT_QA_BANK_PATH, help="Path to output Markdown file")

    # Command: lookup
    parser_lookup = subparsers.add_parser("lookup", help="Search the Q&A database using cosine similarity")
    parser_lookup.add_argument("query", type=str, nargs="+", help="Query string to search for")
    parser_lookup.add_argument("--db", type=str, default=DEFAULT_ANSWERS_PATH, help="Path to database JSON file")

    # Command: add
    parser_add = subparsers.add_parser("add", help="Add a new Q&A pair to the database")
    parser_add.add_argument("question", type=str, help="The interview question")
    parser_add.add_argument("answer", type=str, help="Your customized story or response")
    parser_add.add_argument("--tags", type=str, default="", help="Comma-separated list of tags")
    parser_add.add_argument("--db", type=str, default=DEFAULT_ANSWERS_PATH, help="Path to database JSON file")
    parser_add.add_argument("--md", type=str, default=DEFAULT_QA_BANK_PATH, help="Path to compiled Markdown file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "test":
        run_tests()
        sys.exit(0)

    db_path = getattr(args, "db", DEFAULT_ANSWERS_PATH)
    db = load_db(db_path)

    if args.command == "lookup":
        query_str = " ".join(args.query)
        results = search_questions(query_str, db)
        print(json.dumps(results, indent=2, ensure_ascii=False))

    elif args.command == "add":
        tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
        db.append({
            "question": args.question,
            "answer": args.answer,
            "tags": tags_list
        })
        try:
            save_db(db, db_path)
            md_path = getattr(args, "md", DEFAULT_QA_BANK_PATH)
            compile_markdown(db, md_path)
            print("Successfully added new Q&A and recompiled QA_BANK.md")
        except Exception as e:
            print(f"Error: Failed to save changes: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "compile":
        try:
            md_path = getattr(args, "md", DEFAULT_QA_BANK_PATH)
            compile_markdown(db, md_path)
            print(f"Successfully recompiled Q&A markdown bank to {md_path}")
        except Exception as e:
            print(f"Error: Failed to compile markdown: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
