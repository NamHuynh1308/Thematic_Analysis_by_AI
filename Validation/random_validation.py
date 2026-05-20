from __future__ import annotations

import random
import pandas as pd


INPUT = "jobs_split.csv"
OUTPUT = "validation_sample_100_jobs.csv"

N_JOBS = 100
RANDOM_SEED = 42


def main() -> None:
    random.seed(RANDOM_SEED)

    df = pd.read_csv(INPUT)

    if "job_id" not in df.columns or "line_id" not in df.columns or "text" not in df.columns:
        raise ValueError("jobs_split.csv must contain columns: job_id, line_id, text")

    job_ids = df["job_id"].dropna().unique().tolist()

    if N_JOBS > len(job_ids):
        raise ValueError(f"Requested {N_JOBS} jobs, but only found {len(job_ids)} unique job_id values.")

    sampled_jobs = random.sample(job_ids, N_JOBS)

    sample_df = df[df["job_id"].isin(sampled_jobs)].copy()

    sample_df = sample_df[["job_id", "line_id", "text"]].sort_values(["job_id", "line_id"])

    sample_df["code_human"] = ""
    sample_df["subtheme_human"] = ""
    sample_df["theme_human"] = ""
    sample_df["notes"] = ""

    sample_df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("Saved:", OUTPUT)
    print("Unique sampled jobs:", sample_df["job_id"].nunique())
    print("Total sampled lines:", len(sample_df))


if __name__ == "__main__":
    main()