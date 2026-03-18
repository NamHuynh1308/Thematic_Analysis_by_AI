from __future__ import annotations

import argparse
import json
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-4.1-mini"


# =========================
# LOAD PROMPT
# =========================

def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# =========================
# LOAD JSONL CODES
# =========================

def load_codes_from_jsonl(path: Path):

    codes = []

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            if not line.strip():
                continue

            obj = json.loads(line)

            codes.extend(obj.get("codes", []))

    return codes


# =========================
# MAIN
# =========================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    prompt = load_prompt(prompt_path)

    print("Loading codes...")

    all_codes = load_codes_from_jsonl(input_path)

    unique_codes = sorted(set(all_codes))

    print("Unique codes:", len(unique_codes))

    client = OpenAI()

    full_prompt = (
        prompt
        + "\n\nInput:\n"
        + json.dumps(unique_codes, indent=2)
    )

    resp = client.responses.create(
        model=MODEL,
        input=full_prompt,
        temperature=0,
    )

    raw = resp.output_text.strip()

    data = json.loads(raw)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved:", output_path)


if __name__ == "__main__":
    main()