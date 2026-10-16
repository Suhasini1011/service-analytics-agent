from llm import ask_llm

reply = ask_llm(
    "You are a helpful IT service desk analyst.",
    "In one sentence, what is ticket aging?",
)
print(reply)