from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import Counter

from openai import OpenAI


MODEL = "gpt-5"


def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_codes_from_jsonl(path: Path):

    codes = []

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            if not line.strip():
                continue

            obj = json.loads(line)

            codes.extend(obj.get("codes", []))

    return codes


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    prompt = load_prompt(Path(args.prompt))

    print("Loading codes...")

    all_codes = load_codes_from_jsonl(Path(args.input))

    counter = Counter(all_codes)

    filtered_codes = [c for c, n in counter.items() if n >= 10] # Eliminate codes that only have less than 10 counts

    unique_codes = sorted(filtered_codes)

    print("Total codes:", len(all_codes))
    print("Unique codes:", len(counter))
    print("Filtered codes:", len(unique_codes))

    client = OpenAI()

    full_prompt = (
        prompt
        + "\n\nInput:\n"
        + json.dumps(unique_codes)
    )

    resp = client.responses.create(
        model=MODEL,
        input=full_prompt,
    )

    raw = resp.output_text.strip()

    try:
        data = json.loads(raw)
    except:
        print(raw)
        raise

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved:", args.output)


if __name__ == "__main__":
    main()