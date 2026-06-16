import json
import os
import sys

import requests
from dotenv import load_dotenv

SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"

QUERIES = [
    "site:reddit.com India B2B founder problems",
    "site:reddit.com Indian startup operational nightmare",
    "site:quora.com what problems do Indian businesses face",
    "India business owner frustrated reddit",
    "B2B India problem nobody has solved reddit",
    "Indian founder what I wish existed",
    "site:reddit.com India SME supplier payment problem",
]

PAIN_KEYWORDS = [
    "problem",
    "frustrated",
    "annoying",
    "pain",
    "broken",
    "challenge",
    "terrible",
    "wish",
    "nobody",
]


def matches_pain(snippet):
    text = snippet.lower()
    return any(keyword in text for keyword in PAIN_KEYWORDS)


def main():
    load_dotenv()

    api_key = os.getenv("SEARCHAPI_KEY")
    if not api_key:
        print(
            "Error: SEARCHAPI_KEY is not set. Add your key to the .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_results = []

    for query in QUERIES:
        print(f"Searching: {query}")
        params = {
            "q": query,
            "engine": "google",
            "api_key": api_key,
        }

        try:
            response = requests.get(SEARCHAPI_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"  Error searching '{query}': {e}", file=sys.stderr)
            continue

        organic = data.get("organic_results", [])
        kept = 0
        for result in organic:
            snippet = result.get("snippet", "")
            if not matches_pain(snippet):
                continue
            all_results.append(
                {
                    "query": query,
                    "title": result.get("title", ""),
                    "snippet": snippet,
                    "link": result.get("link", ""),
                }
            )
            kept += 1
        print(f"  Kept {kept} of {len(organic)} results")

    with open("google_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nTotal results found: {len(all_results)}")
    print("Saved to google_results.json")


if __name__ == "__main__":
    main()
