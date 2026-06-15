import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "paste-your-key-here":
        print(
            "Error: OPENAI_API_KEY is not set. Add your key to the .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "What are the top 10 most painful unsolved problems for B2B businesses in India in 2026 across any industry?",
                }
            ],
        )
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error calling the OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
