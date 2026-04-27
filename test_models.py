import os
from openai import OpenAI

client = OpenAI()

models_to_test = ["gpt-5.5", "gpt-5.5-pro", "gpt-5.5-pro-chat", "o1-pro", "o3-mini", "chatgpt-5.5-pro"]

for m in models_to_test:
    try:
        response = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": "hi"}],
            max_completion_tokens=100
        )
        print(f"{m}: SUCCESS")
    except Exception as e:
        print(f"{m}: FAILED - {e}")
