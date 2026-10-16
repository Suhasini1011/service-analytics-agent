import json

with open("data/theme_cache_v1.json") as f:
    old = json.load(f)
with open("data/theme_cache.json") as f:
    new = json.load(f)

changed = [(text, old[text], new[text]) for text in new if text in old and old[text] != new[text]]

print(f"{len(changed)} of {len(new)} descriptions changed theme\n")
for text, before, after in changed[:20]:
    print(f"{before} -> {after} | {text}")