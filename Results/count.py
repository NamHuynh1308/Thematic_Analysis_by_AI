from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


STEP1_CODES = "step1_codes.jsonl"
STEP2_SUBTHEMES = "step2_subthemes.json"
STEP3_THEMES = "step3_themes.json"
THRESHOLD = 10


def load_codes_from_jsonl(path: str | Path) -> list[str]:
    codes: list[str] = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            obj = json.loads(line)
            row_codes = obj.get("codes", [])

            if isinstance(row_codes, list):
                for code in row_codes:
                    if isinstance(code, str) and code.strip():
                        codes.append(code.strip())

    return codes


def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    all_codes = load_codes_from_jsonl(STEP1_CODES)
    code_counter = Counter(all_codes)

    total_codes = len(all_codes)
    distinct_codes = len(code_counter)

    eliminated_codes = {code: count for code, count in code_counter.items() if count < THRESHOLD}
    remaining_codes = {code: count for code, count in code_counter.items() if count >= THRESHOLD}

    step2 = load_json(STEP2_SUBTHEMES)
    step3 = load_json(STEP3_THEMES)

    num_subthemes = len(step2.get("groups", []))
    num_themes = len(step3.get("groups", []))




    print(f"Total codes (all occurrences): {total_codes}")
    print(f"Distinct codes: {distinct_codes}")
    print(f"Distinct codes eliminated (count < {THRESHOLD}): {len(eliminated_codes)}")
    print(f"Distinct codes kept (count >= {THRESHOLD}): {len(remaining_codes)}")
    print(f"Number of subthemes: {num_subthemes}")
    print(f"Number of themes: {num_themes}")


    print("\n")
    print(f"Total occurrences removed from low-frequency codes: {sum(eliminated_codes.values())}")
    print(f"Total occurrences kept after threshold: {sum(remaining_codes.values())}")


if __name__ == "__main__":
    main()