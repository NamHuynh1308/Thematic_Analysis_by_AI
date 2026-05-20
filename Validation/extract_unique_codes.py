import json

input_file = "validation_jobs_extracted.jsonl"
unique_codes = set()

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
            codes = record.get("codes", [])

            for code in codes:
                if isinstance(code, str) and code.strip():
                    unique_codes.add(code.strip())
        except json.JSONDecodeError:
            print("Skipping invalid JSON line")

# Convert to sorted list
unique_codes = sorted(unique_codes)

print(f"Total unique codes: {len(unique_codes)}")
for code in unique_codes:
    print(code)





#----------------------------------------------------------------------------------

import json

input_file = "validation_jobs_extracted.jsonl"
output_file = "unique_codes.txt"
unique_codes = set()

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
            codes = record.get("codes", [])

            for code in codes:
                if isinstance(code, str) and code.strip():
                    unique_codes.add(code.strip())
        except json.JSONDecodeError:
            print("Skipping invalid JSON line")

unique_codes = sorted(unique_codes)

with open(output_file, "w", encoding="utf-8") as f:
    for code in unique_codes:
        f.write(code + "\n")

print(f"Saved {len(unique_codes)} unique codes to {output_file}")







#--------------------------------------------------------------------------------------------------
import json

input_file = "subthemes.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

total_codes = 0

print("Codes per subtheme:\n")
for subtheme, codes in data.items():
    count = len(codes)
    total_codes += count
    print(f"{subtheme}: {count}")

print("\n----------------------")
print(f"Total subthemes: {len(data)}")
print(f"Total codes: {total_codes}")



#----------------------------------------------------------------------------------

