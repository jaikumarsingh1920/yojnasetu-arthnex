import json

with open('scripts/te_rem_153.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total keys: {len(data)}")
for k, v in sorted(data.items()):
    print(f"Key: {k}")
    print(f"  EN: {v['en']}")
    print(f"  HI: {v['hi']}")
