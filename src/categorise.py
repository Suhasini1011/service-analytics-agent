import json
import os
import time
import pandas as pd
from llm import ask_llm
from clean import clean_tickets

CACHE_FILE = "data/theme_cache.json"
BATCH_SIZE = 25

THEMES = [
    "Access and permissions",
    "Login and authentication",
    "Errors and bugs",
    "Reports and data",
    "How-to and guidance",
    "Account and profile changes",
]

SYSTEM_PROMPT = f"""You are an IT service desk analyst.
Classify each numbered ticket description into exactly one theme from this list:
{json.dumps(THEMES)}
Judge by what the user actually needs, not by the words they use.
If none fit, use "Other".
Reply with JSON only, in exactly this format:
{{"results": [{{"id": 1, "theme": "Access and permissions"}}]}}"""


def classify_batch(descriptions):
    numbered = "\n".join(f"{i}. {text}" for i, text in enumerate(descriptions, start=1))
    reply = ask_llm(SYSTEM_PROMPT, numbered)

    json_text = reply[reply.find("{"): reply.rfind("}") + 1]
    data = json.loads(json_text)

    themes = {item["id"]: item["theme"] for item in data["results"]}

    results = []
    for i in range(1, len(descriptions) + 1):
        theme = themes.get(i, "Other")
        if theme not in THEMES:
            theme = "Other"
        results.append(theme)
    return results


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def add_themes(df):
    cache = load_cache()
    unique_texts = df["description"].dropna().unique()
    to_classify = [text for text in unique_texts if text not in cache]
    print(f"{len(unique_texts)} unique descriptions, {len(to_classify)} need the AI")

    for start in range(0, len(to_classify), BATCH_SIZE):
        batch = to_classify[start:start + BATCH_SIZE]
        for text, theme in zip(batch, classify_batch(batch)):
            cache[text] = theme
        save_cache(cache)
        print(f"  classified {start + len(batch)} of {len(to_classify)}")
        time.sleep(10)

    df = df.copy()
    df["theme"] = df["description"].map(cache).fillna("Unclassified")
    return df


if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    df, notes = clean_tickets(raw)

    df = add_themes(df)
    df.to_csv("data/tickets_with_themes.csv", index=False)

    print("\nTickets per theme:")
    print(df["theme"].value_counts())

    pd.set_option("display.width", 200)
    print("\nTheme (what the AI found) vs request type (what the user picked):")
    print(pd.crosstab(df["theme"], df["request_type"]))