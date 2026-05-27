#!/usr/bin/env python3
"""
Generate theme-level co-occurrence, subtheme-level co-occurrence, and candidate profile tables
from a traceable coded job posting dataset.

Expected input columns:
job_id, line_id, sentence, code, subtheme, theme

Counting unit:
Job posting. A theme/subtheme/profile is counted once per job, even if it appears in many lines.
"""

import argparse
import itertools
import re
from pathlib import Path

import pandas as pd


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    required = ["job_id", "line_id", "sentence", "code", "subtheme", "theme"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    for c in ["line_id", "sentence", "code", "subtheme", "theme"]:
        df[c] = df[c].fillna("").astype(str).str.strip()
    return df


def generate_theme_cooccurrence(df: pd.DataFrame, total_jobs: int) -> pd.DataFrame:
    job_themes = (
        df[df["theme"].ne("")]
        .groupby("job_id")["theme"]
        .apply(lambda s: sorted(set(s)))
        .to_dict()
    )

    rows = []
    for job_id, themes in job_themes.items():
        for theme_a, theme_b in itertools.combinations(themes, 2):
            rows.append((theme_a, theme_b, job_id))

    pair_rows = pd.DataFrame(rows, columns=["Theme A", "Theme B", "job_id"])
    out = (
        pair_rows.groupby(["Theme A", "Theme B"])["job_id"]
        .nunique()
        .reset_index(name="Number of Job Postings")
    )
    out["% Jobs"] = (out["Number of Job Postings"] / total_jobs * 100).round(1)
    out["Theme Pair"] = out["Theme A"] + " + " + out["Theme B"]
    out = out[
        ["Theme Pair", "Theme A", "Theme B", "Number of Job Postings", "% Jobs"]
    ].sort_values(["Number of Job Postings", "Theme Pair"], ascending=[False, True])
    return out


def generate_subtheme_cooccurrence(df: pd.DataFrame, total_jobs: int) -> pd.DataFrame:
    valid = df[df["subtheme"].ne("") & df["theme"].ne("")].copy()

    # Usually each subtheme belongs to one theme. This handles edge cases by choosing the most common parent theme.
    subtheme_parent = (
        valid.groupby(["subtheme", "theme"])["job_id"]
        .nunique()
        .reset_index(name="n")
        .sort_values(["subtheme", "n"], ascending=[True, False])
        .drop_duplicates("subtheme")
        .set_index("subtheme")["theme"]
        .to_dict()
    )

    job_subthemes = (
        valid.groupby("job_id")["subtheme"]
        .apply(lambda s: sorted(set(s)))
        .to_dict()
    )

    rows = []
    for job_id, subthemes in job_subthemes.items():
        for subtheme_a, subtheme_b in itertools.combinations(subthemes, 2):
            rows.append((subtheme_a, subtheme_b, job_id))

    pair_rows = pd.DataFrame(rows, columns=["Subtheme A", "Subtheme B", "job_id"])
    out = (
        pair_rows.groupby(["Subtheme A", "Subtheme B"])["job_id"]
        .nunique()
        .reset_index(name="Number of Job Postings")
    )
    out["% Jobs"] = (out["Number of Job Postings"] / total_jobs * 100).round(1)
    out["Parent Theme A"] = out["Subtheme A"].map(subtheme_parent)
    out["Parent Theme B"] = out["Subtheme B"].map(subtheme_parent)
    out["Subtheme Pair"] = out["Subtheme A"] + " + " + out["Subtheme B"]
    out["Parent Themes"] = out["Parent Theme A"] + " + " + out["Parent Theme B"]
    out = out[
        [
            "Subtheme Pair",
            "Parent Themes",
            "Subtheme A",
            "Subtheme B",
            "Parent Theme A",
            "Parent Theme B",
            "Number of Job Postings",
            "% Jobs",
        ]
    ].sort_values(["Number of Job Postings", "Subtheme Pair"], ascending=[False, True])
    return out


def generate_candidate_profiles(df: pd.DataFrame, total_jobs: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = df[df["subtheme"].ne("") & df["theme"].ne("")].copy()
    all_jobs = set(df["job_id"].unique())

    job_theme_sets = (
        df[df["theme"].ne("")].groupby("job_id")["theme"].apply(lambda s: set(s)).to_dict()
    )
    job_subtheme_sets = valid.groupby("job_id")["subtheme"].apply(lambda s: set(s)).to_dict()
    job_sentences = df.groupby("job_id")["sentence"].apply(lambda s: " ".join(map(str, s))).to_dict()

    profile_definitions = {
        "Product-Oriented Software Engineer": {
            "main_themes": [
                "Product, Project, and Professional Skills",
                "Software Engineering and Architecture",
            ],
            "theme_any": [],
            "sub_any_groups": [
                [
                    "Business and Product Skills",
                    "Project Management and Agile Practices",
                    "Documentation and Communication",
                ],
                [
                    "Software Architecture and System Design",
                    "Software Development Process and Practices",
                ],
            ],
            "operational_definition": "Jobs combining product/stakeholder or project-facing expectations with software design or development-process expectations.",
        },
        "Cloud-Native Delivery Engineer": {
            "main_themes": [
                "Cloud, DevOps, and Security",
                "Software Engineering and Architecture",
            ],
            "theme_any": [],
            "sub_any_groups": [
                [
                    "Cloud Platforms and Services",
                    "DevOps and CI/CD",
                    "Containers and Orchestration",
                ],
                [
                    "Software Development Process and Practices",
                    "Testing and Quality Assurance",
                    "Software Architecture and System Design",
                    "Monitoring, Observability, and SRE",
                ],
            ],
            "operational_definition": "Jobs combining cloud/DevOps technologies with delivery, testing, architecture, or reliability expectations.",
        },
        "AI/Data-Adjacent Developer": {
            "main_themes": ["Data, AI, and Analytics"],
            "theme_any": [
                "Application and Web Development",
                "Software Engineering and Architecture",
            ],
            "sub_any_groups": [
                [
                    "AI/ML and LLMs",
                    "Data Platforms and Databases",
                    "Analytics and Business Intelligence",
                    "Data Engineering and Big Data",
                ],
                [
                    "Programming Languages and Paradigms",
                    "Backend and API Development",
                    "Software Development Process and Practices",
                ],
            ],
            "operational_definition": "Jobs combining data/AI expectations with programming, backend, or general software-engineering expectations.",
        },
        "Enterprise Systems Engineer": {
            "main_themes": ["Application and Web Development"],
            "theme_any": [],
            "sub_any_groups": [
                [
                    "E-commerce, CRM, ERP, and Enterprise Platforms",
                    "Microsoft .NET Development",
                ],
                [
                    "Data Platforms and Databases",
                    "Security, Authentication, and Compliance",
                    "Systems, Networking, and Administration",
                    "Domain and Industry Knowledge",
                ],
            ],
            "operational_definition": "Jobs where enterprise platforms or .NET expectations appear with data, security, systems, or domain expectations.",
        },
        "Early-Career Generalist": {
            "main_themes": ["Product, Project, and Professional Skills"],
            "theme_any": [],
            "sub_any_groups": [
                [
                    "Education, Degrees, and Certifications",
                    "General Professional Skills and Soft Skills",
                ],
                [
                    "Programming Languages and Paradigms",
                    "Backend and API Development",
                    "Frontend Web Development",
                    "Testing and Quality Assurance",
                    "Software Development Process and Practices",
                ],
            ],
            "regex_any": r"\b(entry[- ]?level|junior|new grad|recent graduate|internship|intern\b|0\+?\s*years?|1\+?\s*years?|bachelor|bs\b|b\.s\.|degree)\b",
            "operational_definition": "Jobs with early-career, degree, or broad professional-skill signals combined with general software-development expectations.",
        },
    }

    def has_any(values: set[str], options: list[str]) -> bool:
        return bool(values.intersection(options))

    def regex_matches(pattern: str) -> set:
        compiled = re.compile(pattern, re.IGNORECASE)
        return {job_id for job_id, text in job_sentences.items() if compiled.search(text)}

    profile_rows = []
    evidence_rows = []

    for profile_name, definition in profile_definitions.items():
        jobs = set(all_jobs)

        for required_theme in definition.get("main_themes", []):
            jobs = {j for j in jobs if required_theme in job_theme_sets.get(j, set())}

        if definition.get("theme_any"):
            jobs = {j for j in jobs if has_any(job_theme_sets.get(j, set()), definition["theme_any"])}

        for subtheme_group in definition.get("sub_any_groups", []):
            jobs = {j for j in jobs if has_any(job_subtheme_sets.get(j, set()), subtheme_group)}

        if definition.get("regex_any"):
            jobs = jobs.intersection(regex_matches(definition["regex_any"]))

        profile_df = df[df["job_id"].isin(jobs)].copy()

        # Use the operational definition to keep profile summaries specific rather than dominated
        # by broad codes such as collaboration/problem solving.
        required_subthemes = sorted({
            st
            for group in definition.get("sub_any_groups", [])
            for st in group
        })
        targeted_profile_df = profile_df[profile_df["subtheme"].isin(required_subthemes)].copy()
        if targeted_profile_df.empty:
            targeted_profile_df = profile_df.copy()

        top_themes = (
            profile_df[profile_df["theme"].ne("")]
            .groupby("theme")["job_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(4)
            .index.tolist()
        )
        top_subthemes = (
            targeted_profile_df[targeted_profile_df["subtheme"].ne("")]
            .groupby("subtheme")["job_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(8)
            .index.tolist()
        )
        top_codes = (
            targeted_profile_df[targeted_profile_df["code"].ne("")]
            .groupby("code")["job_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(8)
            .index.tolist()
        )

        # Choose a representative sentence from rows that directly match the profile definition.
        candidates = targeted_profile_df[targeted_profile_df["sentence"].ne("")].copy()
        top_codes_lower = [c.lower() for c in top_codes]
        top_subthemes_lower = [s.lower() for s in top_subthemes]
        definition_keywords = " ".join(required_subthemes).lower().replace(",", " ").split()

        def evidence_score(row) -> float:
            code = row["code"].lower()
            subtheme = row["subtheme"].lower()
            sentence = row["sentence"].lower()
            return (
                4 * (subtheme in top_subthemes_lower)
                + 3 * (code in top_codes_lower)
                + sum(1 for c in top_codes_lower[:6] if c in sentence)
                + sum(0.25 for kw in definition_keywords if len(kw) > 4 and kw in sentence)
                + min(len(sentence), 250) / 1000
            )

        if not candidates.empty:
            candidates["evidence_score"] = candidates.apply(evidence_score, axis=1)
            evidence = candidates.sort_values("evidence_score", ascending=False).iloc[0]
            evidence_sentence = evidence["sentence"]
            evidence_job_id = evidence["job_id"]
            evidence_line_id = evidence["line_id"]
        else:
            evidence_sentence, evidence_job_id, evidence_line_id = "", "", ""

        profile_rows.append(
            {
                "Profile Name": profile_name,
                "Main Themes": "; ".join(top_themes),
                "Main Subthemes": "; ".join(top_subthemes[:6]),
                "Representative Codes": "; ".join(top_codes[:6]),
                "Job Count": len(jobs),
                "% Jobs": round(len(jobs) / total_jobs * 100, 1),
                "Job Count / % Jobs": f"{len(jobs):,} / {len(jobs) / total_jobs * 100:.1f}%",
                "Example Evidence": evidence_sentence,
                "Evidence Job ID": evidence_job_id,
                "Evidence Line ID": evidence_line_id,
                "Operational Definition": definition["operational_definition"],
            }
        )

        # Save evidence samples for manual audit/traceability.
        for job_id in sorted(jobs)[:25]:
            job_rows = df[(df["job_id"] == job_id) & df["sentence"].ne("")]
            if job_rows.empty:
                continue
            evidence_rows.append(
                {
                    "Profile Name": profile_name,
                    "job_id": job_id,
                    "Matched Themes": "; ".join(sorted(job_theme_sets.get(job_id, set()))),
                    "Matched Subthemes": "; ".join(sorted(job_subtheme_sets.get(job_id, set()))),
                    "Example Sentence": job_rows.iloc[0]["sentence"],
                }
            )

    profile_table = pd.DataFrame(profile_rows).sort_values("Job Count", ascending=False)
    evidence_table = pd.DataFrame(evidence_rows)
    return profile_table, evidence_table


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="final_traceable_dataset.csv")
    parser.add_argument("--output-dir", default="cooccurrence_profile_outputs")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = clean_text_columns(pd.read_csv(input_path))
    total_jobs = df["job_id"].nunique()

    theme_table = generate_theme_cooccurrence(df, total_jobs)
    subtheme_table = generate_subtheme_cooccurrence(df, total_jobs)
    profile_table, profile_evidence = generate_candidate_profiles(df, total_jobs)

    theme_table.to_csv(output_dir / "theme_level_cooccurrence.csv", index=False)
    subtheme_table.to_csv(output_dir / "subtheme_level_cooccurrence.csv", index=False)
    subtheme_table[subtheme_table["Parent Theme A"] != subtheme_table["Parent Theme B"]].to_csv(
        output_dir / "subtheme_level_cooccurrence_cross_theme_only.csv", index=False
    )
    profile_table.to_csv(output_dir / "candidate_profile_table.csv", index=False)
    profile_evidence.to_csv(output_dir / "candidate_profile_evidence_samples.csv", index=False)

    print(f"Total unique jobs: {total_jobs:,}")
    print("\nTop theme-level co-occurrences:")
    print(theme_table[["Theme Pair", "Number of Job Postings", "% Jobs"]].head(10).to_string(index=False))
    print("\nTop subtheme-level co-occurrences:")
    print(subtheme_table[["Subtheme Pair", "Parent Themes", "Number of Job Postings", "% Jobs"]].head(10).to_string(index=False))
    print("\nCandidate profiles:")
    print(profile_table[["Profile Name", "Job Count / % Jobs", "Main Subthemes"]].to_string(index=False))


if __name__ == "__main__":
    main()
