import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

import database

INPUT_FILE = "google_results.json"
OUTPUT_FILE = "analysed_problems.json"
BATCH_SIZE = 5

SYSTEM_PROMPT = (
    "You are an experienced startup founder and venture capitalist evaluating "
    "business opportunities in India. You have built and invested in B2B "
    "companies. When you read a problem description your job is to identify "
    "whether this represents a genuine founder opportunity — a specific, "
    "painful, recurring problem that someone would pay to have solved and that "
    "is not already well addressed by existing solutions. For each item return "
    "JSON with: problem (the specific painful situation in one sentence — be "
    "concrete not generic, name the exact friction), who_has_it (the specific "
    "type of person or business, be precise — not SMEs but textile "
    "manufacturers in Surat or logistics ops managers at mid-size "
    "manufacturers), pain_score (1-10 where 10 means they would pay "
    "significant money today to fix this), is_opportunity (true only if this "
    "is specific enough to build a startup around), category (payments, "
    "compliance, procurement, technology, workforce, logistics, communication, "
    "trust, other), why_interesting (one sentence on why a founder should care "
    "about this specifically), existing_solutions (what people use today to "
    "solve this — even if it is just phone calls and Excel), gap (what is "
    "missing from existing solutions). Return only valid JSON array"
)


def parse_json_response(content):
    """Parse a JSON array from the model response, tolerating code fences."""
    text = content.strip()

    # Strip markdown code fences if present.
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # drop opening fence (``` or ```json)
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Fall back to extracting the outermost array.
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])

    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "paste-your-key-here":
        print(
            "Error: OPENAI_API_KEY is not set. Add your key to the .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Run google_scraper.py first.", file=sys.stderr)
        sys.exit(1)

    if not results:
        print(f"No results in {INPUT_FILE}; nothing to analyse.")
        return

    client = OpenAI(api_key=api_key)

    analysed = []
    total_batches = (len(results) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num, batch in enumerate(chunked(results, BATCH_SIZE), start=1):
        print(f"\nProcessing batch {batch_num} of {total_batches} ({len(batch)} items)...")
        user_content = json.dumps(batch, ensure_ascii=False, indent=2)

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            content = response.choices[0].message.content
        except Exception as e:
            print(f"  Error calling OpenAI API for batch {batch_num}: {e}", file=sys.stderr)
            continue

        try:
            batch_results = parse_json_response(content)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Error parsing JSON for batch {batch_num}: {e}", file=sys.stderr)
            continue

        for item in batch_results:
            analysed.append(item)
            problem = item.get("problem", "(no problem field)")
            pain_score = item.get("pain_score", "?")
            print(f"  [pain {pain_score}] {problem}")

        inserted = database.save_problems(batch_results, "google")
        print(f"  Saved {inserted} new problem(s) to the database.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(analysed, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysed {len(analysed)} problems. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
