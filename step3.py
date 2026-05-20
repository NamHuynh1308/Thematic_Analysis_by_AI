from __future__ import annotations

import argparse
import json
from pathlib import Path

from openai import OpenAI


MODEL = "gpt-5"


# ------------------------------------------------------------------------------------------------------
# LOAD PROMPT
def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------------------------------------------------
# MAIN
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--input", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    input_path = Path(args.input)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    print("Loading subthemes...")

    with open(input_path, "r", encoding="utf-8") as f:
        subthemes_json = json.load(f)

    groups = subthemes_json.get("groups", [])

    print("Subthemes count:", len(groups))

    if len(groups) == 0:
        print("ERROR: no subthemes found")
        return

    prompt = load_prompt(prompt_path)

    client = OpenAI()

    # send only groups, not whole object
    full_prompt = (
        prompt
        + "\n\nInput:\n"
        + json.dumps(groups, indent=2)
    )

    print("Calling LLM...")

    resp = client.responses.create(
        model=MODEL,
        input=full_prompt,
    )

    raw = resp.output_text.strip()

    try:
        data = json.loads(raw)
    except Exception:
        print("Failed to parse JSON. Raw output:")
        print(raw)
        raise

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Saved:", output_path)


# =========================

if __name__ == "__main__":
    main()