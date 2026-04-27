import os
from openai import OpenAI

client = OpenAI()

with open("test_api_out.txt", "w", encoding="utf-8") as f:
    try:
        response = client.responses.create(
            model="gpt-5.5-pro",
            input=[{"role": "user", "content": "hi"}],
        )
        f.write(f"RESPONSES SUCCESS: {response}\n")
    except Exception as e:
        f.write(f"RESPONSES FAILED: {e}\n")

    import inspect
    try:
        f.write(f"Help: {inspect.signature(client.responses.create)}\n")
    except Exception as e:
        pass
