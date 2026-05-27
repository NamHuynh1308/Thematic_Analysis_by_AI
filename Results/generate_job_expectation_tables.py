import pandas as pd
import os

INPUT_PATH = "final_traceable_dataset.csv"
OUTDIR = "job_expectation_outputs"
os.makedirs(OUTDIR, exist_ok=True)

df = pd.read_csv(INPUT_PATH)

# Expected columns:
# job_id, line_id, sentence, code, subtheme, theme
for col in ["job_id", "line_id", "sentence", "code", "subtheme", "theme"]:
    if col not in df.columns:
        raise ValueError(f"Missing required column: {col}")

df["code"] = df["code"].fillna("")
df["subtheme"] = df["subtheme"].fillna("")
df["theme"] = df["theme"].fillna("")
df["sentence"] = df["sentence"].fillna("")

N_JOBS = df["job_id"].nunique()

# For most expectation categories, count primarily from the coded layer.
# For credential categories, especially years of experience, sentence-level regex is also useful.
df["code_sub"] = (df["code"] + " " + df["subtheme"]).str.lower()
df["code_sub_sentence"] = (df["code"] + " " + df["subtheme"] + " " + df["sentence"]).str.lower()

def summarize_categories(df, categories, label_col):
    rows = []
    evidence_rows = []

    for category, cfg in categories.items():
        pattern = cfg["pattern"]
        text_col = cfg.get("count_text", "code_sub")
        rep_pattern = cfg.get("rep_pattern", pattern)

        mask = df[text_col].str.contains(pattern, regex=True, case=False, na=False)
        tmp = df[mask & (df["code"].str.strip() != "")].copy()

        jobs = tmp["job_id"].nunique()
        pct = jobs / N_JOBS * 100

        # Representative codes: prefer codes that directly match the category.
        rep_src = tmp[tmp["code"].str.contains(rep_pattern, regex=True, case=False, na=False)]
        if rep_src.empty:
            rep_src = tmp

        code_counts = rep_src.groupby("code")["job_id"].nunique().sort_values(ascending=False)
        reps = []
        seen = set()
        for code, _ in code_counts.items():
            code = str(code).strip()
            key = code.lower()
            if code and key not in seen:
                reps.append(code)
                seen.add(key)
            if len(reps) >= 5:
                break

        # Evidence: choose a short/medium sentence from a row close to the representative code.
        candidates = tmp[tmp["sentence"].str.len().between(35, 220)].copy()
        if not candidates.empty:
            direct = candidates[candidates["code"].str.contains(rep_pattern, regex=True, case=False, na=False)]
            if not direct.empty:
                candidates = direct
        if candidates.empty:
            candidates = tmp.copy()

        if not candidates.empty:
            top_codes = {c.lower(): i for i, c in enumerate(reps)}
            candidates["code_rank"] = candidates["code"].str.lower().map(top_codes).fillna(999)
            candidates = candidates.sort_values(["code_rank", "job_id", "line_id"])
            example = candidates.iloc[0]
            sentence = example["sentence"]
            example_code = example["code"]
            job_id = example["job_id"]
            line_id = example["line_id"]
        else:
            sentence = ""
            example_code = ""
            job_id = ""
            line_id = ""

        rows.append({
            label_col: category,
            "Jobs": jobs,
            "Pct Jobs": round(pct, 1),
            "Count / % Jobs": f"{jobs:,} / {pct:.1f}%",
            "Representative Codes": ", ".join(reps),
            "Example Evidence": f"“{sentence}”"
        })

        evidence_rows.append({
            "category": category,
            "job_id": job_id,
            "line_id": line_id,
            "code": example_code,
            "sentence": sentence
        })

    return pd.DataFrame(rows).sort_values("Jobs", ascending=False), pd.DataFrame(evidence_rows)

skill_categories = {
    "Programming": {
        "pattern": r"\b(?:programming|programming languages|software development|application development|java programming|python programming|c# programming|c\+\+ programming|javascript programming|typescript|react|node\.js|frontend|backend|full[- ]stack|object-oriented|functional programming)\b"
    },
    "Testing / Quality Assurance": {
        "pattern": r"\b(?:testing|quality assurance|qa|unit testing|integration testing|test automation|automated testing|selenium|pytest|junit)\b"
    },
    "Architecture / System Design": {
        "pattern": r"\b(?:architecture|system design|software design|design patterns|scalability|scalable systems|distributed systems|microservices|performance optimization|application design)\b"
    },
    "Backend / API Development": {
        "pattern": r"\b(?:backend|api|rest|graphql|server-side|microservices|database design)\b"
    },
    "Frontend / UI Development": {
        "pattern": r"\b(?:front[- ]?end|react|angular|vue|javascript frameworks|html|css|ui/ux|accessibility|web applications)\b"
    },
    "Data / AI / Analytics": {
        "pattern": r"\b(?:data analysis|analytics|machine learning|artificial intelligence|ai/ml|llm|data engineering|big data|tensorflow|pytorch|modeling|business intelligence|sql)\b"
    },
    "Security / Compliance": {
        "pattern": r"\b(?:security|authentication|authorization|compliance|privacy|secure coding|encryption|cybersecurity|vulnerability|iam)\b"
    },
    "Problem Solving / Analytical Thinking": {
        "pattern": r"\b(?:problem solving|analytical skills|critical thinking|troubleshooting|debugging|root cause|attention to detail)\b"
    },
    "Communication": {
        "pattern": r"\b(?:communication skills|written communication|verbal communication|stakeholder communication|technical documentation|documentation|presentation|communicat)\b"
    },
    "Collaboration / Teamwork": {
        "pattern": r"\b(?:collaboration|teamwork|team collaboration|cross-functional|pair programming|working with teams)\b"
    },
    "Leadership / Mentoring": {
        "pattern": r"\b(?:leadership|mentoring|technical leadership|team leadership|coaching|guide junior|mentor)\b"
    },
    "Product / Business Understanding": {
        "pattern": r"\b(?:business|product|requirements analysis|domain|customer|stakeholder|user experience|business analysis)\b"
    },
}

tooling_categories = {
    "Cloud platforms": {
        "pattern": r"\b(?:aws|amazon web services|azure|gcp|google cloud|cloud platform|cloud computing|cloud services)\b"
    },
    "Version control": {
        "pattern": r"\b(?:git|github|gitlab|bitbucket|version control|source control)\b"
    },
    "CI/CD": {
        "pattern": r"\b(?:ci/cd|continuous integration|continuous deployment|jenkins|github actions|gitlab ci|buildkite|argo|argocd)\b"
    },
    "Containers / Orchestration": {
        "pattern": r"\b(?:docker|kubernetes|container|containerization|orchestration|helm)\b"
    },
    "Databases": {
        "pattern": r"\b(?:sql|postgresql|postgres|mysql|mongodb|database|oracle|redis|nosql|dynamodb|snowflake)\b"
    },
    "AI / Data tools": {
        "pattern": r"\b(?:tensorflow|pytorch|keras|scikit|machine learning|llm|artificial intelligence|data analysis|spark|hadoop|databricks|tableau|power bi|business intelligence)\b"
    },
    "Frontend frameworks / web stack": {
        "pattern": r"\b(?:react|angular|vue|javascript frameworks|node\.js|typescript|html|css|web applications)\b"
    },
    "Testing tools / QA automation": {
        "pattern": r"\b(?:selenium|junit|pytest|test automation|automated testing|unit testing|integration testing|qa|quality assurance)\b"
    },
    "Monitoring / Observability": {
        "pattern": r"\b(?:grafana|prometheus|datadog|observability|monitoring|logging|sre|splunk|new relic)\b"
    },
    "Infrastructure as Code / Automation": {
        "pattern": r"\b(?:terraform|ansible|infrastructure as code|iac|automation|scripting|shell scripting|bash|powershell)\b"
    },
    "Security / Identity tools": {
        "pattern": r"\b(?:iam|oauth|sso|authentication|authorization|cybersecurity|security|encryption|vulnerability)\b"
    },
}

credential_categories = {
    "Degree requirement": {
        "pattern": r"\b(?:bachelor'?s degree|bs in|b\.s\.|master'?s degree|ms in|m\.s\.|computer science degree|advanced degree|degree in computer science)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:degree|bachelor|master|computer science degree|advanced degree)\b"
    },
    "Years of experience": {
        "pattern": r"\b(?:\d+\+?\s*(?:-|to\s*)?\d*\+?\s*years?|years of (?:professional |relevant |software|engineering|development|hands-on )?experience|minimum .* years|at least .* years)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:experience|software development experience|professional experience|work experience|internship experience|project experience)\b"
    },
    "Certifications": {
        "pattern": r"\b(?:certification|certifications|aws certified|security\+|cissp|pmp|scrum master|azure certification|cloud certification)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:certification|certifications|certified|security\+|cissp|pmp|scrum master)\b"
    },
    "Domain experience": {
        "pattern": r"\b(?:domain and industry knowledge|domain expertise|domain experience|industry knowledge|healthcare|finance|financial|defense|government|e-commerce|banking|insurance|capital market|automotive|aerospace|retail|telecom|public sector|medical|saas|fintech)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:domain|industry|healthcare|finance|financial|defense|government|e-commerce|banking|insurance|capital market|automotive|aerospace|retail|telecom|saas|fintech)\b"
    },
    "Portfolio / project experience": {
        "pattern": r"\b(?:project experience|portfolio|shipped products|shipping features|prior project|production experience|built .* product|delivered .* project|hands-on .* project|internship experience|open source|github portfolio)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:project experience|portfolio|open source|internship experience|production experience)\b"
    },
}

work_practice_categories = {
    "Agile work": {
        "pattern": r"\b(?:agile|scrum|sprint|kanban|jira|stand[- ]?up|project management and agile practices|sprint planning)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:agile|scrum|sprint|kanban|jira|project management)\b"
    },
    "Collaboration": {
        "pattern": r"\b(?:collaboration|teamwork|cross-functional|team collaboration|cross-functional teamwork|pair programming|work with.*team)\b",
        "rep_pattern": r"\b(?:collaboration|teamwork|cross-functional|team collaboration)\b"
    },
    "Ownership": {
        "pattern": r"\b(?:ownership|end-to-end|take initiative|initiative|accountability|independent work|self-directed|autonomy|responsibility)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:ownership|initiative|independent work|accountability|autonomy|responsibility)\b"
    },
    "Communication": {
        "pattern": r"\b(?:stakeholder communication|communication skills|written communication|verbal communication|technical documentation|presentation|communicat|documentation)\b",
        "rep_pattern": r"\b(?:communication|documentation|presentation)\b"
    },
    "Delivery responsibility": {
        "pattern": r"\b(?:production systems|production|shipping features|ship|delivery|deployment|release|operate|maintenance|on-call|software maintenance|project delivery|end-to-end delivery)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:delivery|deployment|release|maintenance|on-call|production|project delivery)\b"
    },
    "Adaptability / Learning": {
        "pattern": r"\b(?:adaptability|continuous learning|learn new|fast-paced|learning mindset|growth mindset|flexibility|adapt|continuous improvement|process improvement)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:adaptability|continuous learning|flexibility|continuous improvement|process improvement)\b"
    },
    "Stakeholder / Customer orientation": {
        "pattern": r"\b(?:stakeholder|customer|client|user needs|requirements analysis|business requirement|product requirements|customer focus)\b",
        "count_text": "code_sub_sentence",
        "rep_pattern": r"\b(?:stakeholder|customer|client|requirements analysis|business requirement)\b"
    },
}

skill_table, skill_evidence = summarize_categories(df, skill_categories, "Skill Category")
tooling_table, tooling_evidence = summarize_categories(df, tooling_categories, "Tooling Category")
credential_table, credential_evidence = summarize_categories(df, credential_categories, "Credential Type")
work_table, work_evidence = summarize_categories(df, work_practice_categories, "Work-Practice Category")

# Optional: replace representative codes with cleaner representative tool names for tooling table.
tool_representatives = {
    "Cloud platforms": "AWS, Azure, GCP / Google Cloud",
    "Version control": "Git, GitHub, GitLab, Bitbucket",
    "CI/CD": "Jenkins, GitHub Actions, GitLab CI, Buildkite, ArgoCD",
    "Containers / Orchestration": "Docker, Kubernetes, Helm",
    "Databases": "SQL, PostgreSQL, MySQL, MongoDB, Redis, DynamoDB, Snowflake",
    "AI / Data tools": "TensorFlow, PyTorch, Spark, Hadoop, Databricks, Tableau, Power BI",
    "Frontend frameworks / web stack": "React, Angular, Vue, TypeScript, HTML, CSS, Node.js",
    "Testing tools / QA automation": "Selenium, JUnit, pytest, unit testing, integration testing",
    "Monitoring / Observability": "Grafana, Prometheus, Datadog, Splunk, New Relic",
    "Infrastructure as Code / Automation": "Terraform, Ansible, Bash, PowerShell",
    "Security / Identity tools": "IAM, OAuth, SSO, authentication, encryption",
}
tooling_table["Representative Tools"] = tooling_table["Tooling Category"].map(tool_representatives).fillna(tooling_table["Representative Codes"])

skill_table.to_csv(os.path.join(OUTDIR, "skill_expectations.csv"), index=False)
tooling_table.to_csv(os.path.join(OUTDIR, "tooling_expectations.csv"), index=False)
credential_table.to_csv(os.path.join(OUTDIR, "credential_expectations.csv"), index=False)
work_table.to_csv(os.path.join(OUTDIR, "work_practice_expectations.csv"), index=False)

pd.concat([
    skill_evidence.assign(section="Skill Expectations"),
    tooling_evidence.assign(section="Tooling Expectations"),
    credential_evidence.assign(section="Credential Expectations"),
    work_evidence.assign(section="Work-Practice Expectations"),
]).to_csv(os.path.join(OUTDIR, "example_evidence_trace.csv"), index=False)

print(f"Total jobs: {N_JOBS:,}")
print(f"Coded rows: {(df['code'].str.strip() != '').sum():,}")
print(f"Saved outputs to: {OUTDIR}/")