import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_name": "GROQ_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_name": "GEMINI_API_KEY",
    },
}


def ask_llm(system_prompt, user_prompt):
    provider = os.getenv("LLM_PROVIDER", "groq")
    settings = PROVIDERS[provider]

    client = OpenAI(
        api_key=os.getenv(settings["key_name"]),
        base_url=settings["base_url"],
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        temperature=0,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content