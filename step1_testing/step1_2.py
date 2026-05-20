from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
from openai import OpenAI
from tqdm import tqdm


MODEL = "gpt-4o-mini"
BATCH_SIZE = 100
MAX_RETRY = 5
SLEEP_BETWEEN = 0.0


def load_prompt(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_chunk_text(df_chunk: pd.DataFrame) -> str:
    lines = []
    for _, r in df_chunk.iterrows():
        line_id = str(r["line_id"]).strip()
        text = str(r["text"]).replace("\n", " ").strip()
        lines.append(f"{line_id}\t{text}")
    return "\n".join(lines)


def call_llm(client, prompt, chunk_text):

    full_prompt = prompt + "\n\nInput:\n" + chunk_text

    raw = ""

    for i in range(MAX_RETRY):

        try:

            resp = client.responses.create(
                model=MODEL,
                input=full_prompt,
                temperature=0,
            )

            raw = resp.output_text.strip()

            return json.loads(raw)

        except Exception as e:

            print(f"JSON/API error retry {i+1}/{MAX_RETRY}:", e)

            try:
                print(raw[:500])
            except:
                pass

            time.sleep(2)

    print("⚠️ Skipping bad batch")

    return None


def load_done_line_ids(output_path: Path) -> set[str]:
    done = set()

    if not output_path.exists():
        return done

    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "line_id" in obj:
                    done.add(str(obj["line_id"]))
            except Exception:
                continue

    return done


def normalize_items(items: list[dict], chunk: pd.DataFrame) -> list[dict]:
    chunk_lookup = {
        str(r["line_id"]).strip(): str(r["text"]).replace("\n", " ").strip()
        for _, r in chunk.iterrows()
    }

    item_map = {}
    for it in items:
        lid = str(it.get("line_id", "")).strip()
        if not lid:
            continue

        sentence = str(it.get("sentence", chunk_lookup.get(lid, ""))).strip()
        codes = it.get("codes", [])

        if not isinstance(codes, list):
            codes = []

        item_map[lid] = {
            "line_id": lid,
            "sentence": sentence,
            "codes": codes,
        }

    normalized = []
    for lid, sentence in chunk_lookup.items():
        if lid in item_map:
            normalized.append(item_map[lid])
        else:
            normalized.append({
                "line_id": lid,
                "sentence": sentence,
                "codes": [],
            })

    return normalized


def append_batch_to_jsonl(items: list[dict], output_path: Path) -> None:
    with open(output_path, "a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    prompt_path = Path(args.prompt)
    output_path = Path(args.output)

    df = pd.read_csv(input_path)

    print("Columns:", df.columns.tolist())

    assert "line_id" in df.columns, "Missing column: line_id"
    assert "text" in df.columns, "Missing column: text"

    df["line_id"] = df["line_id"].astype(str)
    df["text"] = df["text"].astype(str)

    prompt = load_prompt(prompt_path)
    client = OpenAI()

    done_line_ids = load_done_line_ids(output_path)
    if done_line_ids:
        print(f"Resume mode: found {len(done_line_ids)} completed line_ids in {output_path.name}")
        df = df[~df["line_id"].isin(done_line_ids)].copy()

    n = len(df)
    if n == 0:
        print("Nothing left to process.")
        return

    total_batches = (n + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Remaining lines to process: {n}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Total batches: {total_batches}")

    for batch_num, start in enumerate(
        tqdm(range(0, n, BATCH_SIZE), total=total_batches, desc="Coding"),
        start=1,
    ):
        chunk = df.iloc[start:start + BATCH_SIZE].copy()
        chunk_text = build_chunk_text(chunk)

        data = call_llm(client, prompt, chunk_text)

        if data is None: # pass bad patch
            continue

        items = data.get("items", [])

        normalized_items = normalize_items(items, chunk)
        append_batch_to_jsonl(normalized_items, output_path)

        print(
            f"\nSaved batch {batch_num}/{total_batches} | "
            f"rows: {len(normalized_items)} | "
            f"first line_id: {normalized_items[0]['line_id']}"
        )
        for preview in normalized_items[:3]:
            print(json.dumps(preview, ensure_ascii=False))

        if SLEEP_BETWEEN > 0:
            time.sleep(SLEEP_BETWEEN)

    print(f"\nDone. Results saved to: {output_path}")


if __name__ == "__main__":
    main()