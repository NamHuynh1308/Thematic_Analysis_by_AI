import pandas as pd
import re
from pathlib import Path


INPUT = "jobs_cleaned.csv"
OUTPUT = "jobs_split.csv"


def sanitize(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace('"', "'")
    text = text.replace("“", "'")
    text = text.replace("”", "'")

    return text.strip()


def split_sentences(text):

    text = sanitize(text)

    parts = re.split(r"(?<=[.!?])\s+", text)

    final = []

    for p in parts:

        p = p.strip()

        if not p:
            continue

        # split long sentence
        if len(p) > 250:

            sub = re.split(r"[;,]| and | or ", p)

            for s in sub:

                s = s.strip()

                if s:
                    final.append(s)

        else:

            final.append(p)

    return final


def main():

    df = pd.read_csv(INPUT)

    rows = []

    for _, row in df.iterrows():

        job_id = row["id"]
        title = row["job_title"]
        desc = row["description"]

        sentences = split_sentences(desc)

        for i, s in enumerate(sentences):

            rows.append(
                {
                    "job_id": job_id,
                    "line_id": f"{job_id}_{i}",
                    "text": s,
                    "job_title": title,
                }
            )

    out = pd.DataFrame(rows)

    out.to_csv(OUTPUT, index=False)

    print("Saved", OUTPUT)
    print("Total lines:", len(out))


if __name__ == "__main__":
    main()