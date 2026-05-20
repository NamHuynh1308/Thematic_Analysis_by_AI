import json
from collections import defaultdict

INPUT_JSONL = "validation_jobs_extracted.jsonl"
SUBTHEMES_JSON = "subthemes.json"
THEMES_JSON = "themes.json"
OUTPUT_JSONL = "validation_jobs_extracted_with_subthemes_themes.jsonl"


def normalize(text):
    return " ".join(str(text).strip().lower().split())


# ----------------------------
# Load subthemes and themes
# ----------------------------
with open(SUBTHEMES_JSON, "r", encoding="utf-8") as f:
    subthemes_data = json.load(f)

with open(THEMES_JSON, "r", encoding="utf-8") as f:
    themes_data = json.load(f)

# ----------------------------
# Build code -> subtheme map
# ----------------------------
code_to_subtheme = {}
normalized_code_to_subtheme = {}
duplicate_codes = defaultdict(list)

for subtheme, codes in subthemes_data.items():
    for code in codes:
        if code in code_to_subtheme:
            duplicate_codes[code].append(subtheme)
        else:
            code_to_subtheme[code] = subtheme

        norm_code = normalize(code)
        if norm_code not in normalized_code_to_subtheme:
            normalized_code_to_subtheme[norm_code] = subtheme

# ----------------------------
# Build subtheme -> theme map
# ----------------------------
subtheme_to_theme = {}
for theme, subthemes in themes_data.items():
    for subtheme in subthemes:
        subtheme_to_theme[subtheme] = theme

# ----------------------------
# Process JSONL
# ----------------------------
total_lines = 0
total_codes = 0
matched_codes = 0
unmatched_codes = defaultdict(int)

with open(INPUT_JSONL, "r", encoding="utf-8") as fin, open(
    OUTPUT_JSONL, "w", encoding="utf-8"
) as fout:
    for line in fin:
        line = line.strip()
        if not line:
            continue

        total_lines += 1
        record = json.loads(line)

        codes = record.get("codes", [])
        total_codes += len(codes)

        matched_subthemes = []
        matched_themes = []

        seen_subthemes = set()
        seen_themes = set()

        for code in codes:
            subtheme = None

            # 1. Exact match
            if code in code_to_subtheme:
                subtheme = code_to_subtheme[code]

            # 2. Normalized fallback
            else:
                norm_code = normalize(code)
                if norm_code in normalized_code_to_subtheme:
                    subtheme = normalized_code_to_subtheme[norm_code]

            if subtheme:
                matched_codes += 1

                if subtheme not in seen_subthemes:
                    matched_subthemes.append(subtheme)
                    seen_subthemes.add(subtheme)

                theme = subtheme_to_theme.get(subtheme)
                if theme and theme not in seen_themes:
                    matched_themes.append(theme)
                    seen_themes.add(theme)
            else:
                unmatched_codes[code] += 1

        record["subthemes"] = matched_subthemes
        record["themes"] = matched_themes

        fout.write(json.dumps(record, ensure_ascii=False) + "\n")

# ----------------------------
# Print summary
# ----------------------------
print(f"Done. Output saved to: {OUTPUT_JSONL}")
print(f"Total lines processed: {total_lines}")
print(f"Total codes found in JSONL: {total_codes}")
print(f"Matched codes: {matched_codes}")
print(f"Unmatched codes: {sum(unmatched_codes.values())}")
print(f"Unique unmatched codes: {len(unmatched_codes)}")

if unmatched_codes:
    print("\nTop unmatched codes:")
    for code, count in sorted(unmatched_codes.items(), key=lambda x: (-x[1], x[0]))[:50]:
        print(f"{code}: {count}")

if duplicate_codes:
    print("\nWarning: duplicate code names detected in subthemes.json")
    for code, subtheme_list in list(duplicate_codes.items())[:20]:
        print(f"{code} -> {subtheme_list}")