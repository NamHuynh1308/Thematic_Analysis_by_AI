from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd



# LOAD JSON
def load_json(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# LOAD JSONL
def load_jsonl_to_df(path):

    rows = []

    with open(path, "r", encoding="utf-8") as f:

        for line in f:

            if not line.strip():
                continue

            obj = json.loads(line)

            rows.append(obj)

    df = pd.DataFrame(rows)

    # make sure codes column exists
    if "codes" not in df.columns:
        df["codes"] = [[] for _ in range(len(df))]

    return df







# -----------------------------------------------------------------------------------------------------
# BUILD MAPS

def build_code_to_subtheme(subthemes_json):

    mapping = {}

    for g in subthemes_json.get("groups", []):

        sub = g.get("name")

        for code in g.get("members", []):
            mapping[code] = sub

    return mapping


def build_subtheme_to_theme(themes_json):

    mapping = {}

    for g in themes_json.get("groups", []):

        theme = g.get("name")

        for sub in g.get("members", []):
            mapping[sub] = theme

    return mapping


# -----------------------------------------------------------------------------------------------------------------
# MAIN

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--jobs", required=True)
    parser.add_argument("--codes", required=True)
    parser.add_argument("--subthemes", required=True)
    parser.add_argument("--themes", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    print("Loading jobs")
    jobs_df = pd.read_csv(args.jobs)

    print("Loading codes")
    codes_df = load_jsonl_to_df(args.codes)

    print("Loading subthemes")
    subthemes_json = load_json(args.subthemes)

    print("Loading themes")
    themes_json = load_json(args.themes)

    code_to_sub = build_code_to_subtheme(subthemes_json)

    sub_to_theme = build_subtheme_to_theme(themes_json)

    print("Merging jobs + codes")

    df = jobs_df.merge(
        codes_df,
        on="line_id",
        how="left",
    )

    df["codes"] = df["codes"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    rows = []

    print("Expanding rows")

    for r in df.itertuples(index=False):

        codes = r.codes

        if not codes:

            rows.append(
                {
                    "job_id": r.job_id,
                    "line_id": r.line_id,
                    "sentence": r.text,
                    "code": None,
                    "subtheme": None,
                    "theme": None,
                }
            )

            continue

        for c in codes:

            sub = code_to_sub.get(c)

            theme = sub_to_theme.get(sub)

            rows.append(
                {
                    "job_id": r.job_id,
                    "line_id": r.line_id,
                    "sentence": r.text,
                    "code": c,
                    "subtheme": sub,
                    "theme": theme,
                }
            )

    out_df = pd.DataFrame(rows)

    print("Saving...")

    out_df.to_csv(args.output, index=False)

    print("Saved:", args.output)





# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()