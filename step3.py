from __future__ import annotations

import argparse
import json
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-4.1-mini"


def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    with open(input_path, "r", encoding="utf-8") as f:
        subthemes = json.load(f)

    prompt = load_prompt(prompt_path)

    client = OpenAI()

    full_prompt = (
        prompt
        + "\n\nInput:\n"
        + json.dumps(subthemes, indent=2)
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