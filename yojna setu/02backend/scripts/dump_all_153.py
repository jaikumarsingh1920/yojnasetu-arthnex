import json

with open('scripts/te_rem_153.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('scripts/all_153_keys_dump.txt', 'w', encoding='utf-8') as out:
    for k, v in sorted(data.items()):
        out.write(f"{k} ::: {v['en']} ::: {v['hi']}\n")

print(f"Wrote {len(data)} keys to scripts/all_153_keys_dump.txt")
