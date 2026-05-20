# LLM-Assisted Thematic Analysis Pipeline

This project implements an LLM-assisted thematic analysis pipeline for job postings.
The pipeline extracts teachable skills from job descriptions, groups them into subthemes,
and then into broader themes, producing a fully traceable dataset.

Pipeline:

jobs_cleaned.csv
→ job_split.py
→ jobs_split.csv
→ step1.py (LLM coding)
→ step1_codes.jsonl
→ step2.py (codes → subthemes)
→ step2_subthemes.json
→ step3.py (subthemes → themes)
→ step3_themes.json
→ step4.py (build final dataset of sentence, code, subtheme, theme)
→ final_dataset.csv


--------------------------------------------------------------------------------------------------
FILES


prompts/
    coding_prompt.txt
        Prompt for sentence → skill codes

    code_subtheme_prompt.txt
        Prompt for codes → subthemes

    subtheme_theme_prompt.txt
        Prompt for subthemes → themes


job_split.py
    Splits job descriptions into sentences.

jobs_cleaned.csv
    Original cleaned dataset.

jobs_split.csv
    Sentence-level dataset produced by job_split.py.


step1.py
    Calls OpenAI API to assign skill codes to each sentence.
    Output: step1_codes.jsonl


step2.py
    Groups codes into subthemes using LLM.
    Output: step2_subthemes.json


step3.py
    Groups subthemes into themes using LLM.
    Output: step3_themes.json


step4.py
    Combines all results into final traceable dataset.
    Output: final_dataset.csv


step1_codes.jsonl
    Streaming output from step1.py


----------------------------------------------------------------------------------------------
Commands to run


1. Split job descriptions

    python job_split.py


2. Run coding step

    python step1.py \
        --input jobs_split.csv \
        --prompt prompts/coding_prompt.txt \
        --output step1_codes.jsonl


3. Build subthemes

    python step2.py \
        --input step1_codes.jsonl \
        --prompt prompts/code_subtheme_prompt.txt \
        --output step2_subthemes.json


4. Build themes

    python step3.py \
        --input step2_subthemes.json \
        --prompt prompts/subtheme_theme_prompt.txt \
        --output step3_themes.json


5. Build final dataset

    python step4.py \
        --jobs jobs_split.csv \
        --codes step1_codes.jsonl \
        --subthemes step2_subthemes.json \
        --themes step3_themes.json \
        --output final_dataset.csv


-----------------------------------------------------------------------------------------------
Findings

-Step 1 takes the longest time to complete due to API call and depends on dataset sizes.