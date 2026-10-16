import json
import os
import time
import pandas as pd
from llm import ask_llm
from clean import clean_tickets

CACHE_FILE = "data/theme_cache.json"
BATCH_SIZE = 25

THEMES = {
    "Access and permissions": "Needs access, a role or permissions granted, restored or changed, including 'not authorised' errors caused by missing permissions.",
    "Login and authentication": "Cannot sign in: passwords, lockouts, credentials or sign-in loops, on any device.",
    "Errors and bugs": "Something is broken or failing, such as error messages or failed exports and downloads, and the cause is not missing permissions or signing in.",
    "Reports and data": "Requests for a new report, dashboard or data to be added. Not errors with existing reports.",
    "How-to and guidance": "Asks how to do something or where to find something, including finding their own records.",
    "Account and profile changes": "Requests to update the user's own details, such as cost centre, team or manager.",
}

THEME_LIST = "\n".join(f"- {name}: {meaning}" for name, meaning in THEMES.items())

SYSTEM_PROMPT = f"""You are an IT service desk analyst.
Classify each numbered ticket description into exactly one of these themes:
{THEME_LIST}
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