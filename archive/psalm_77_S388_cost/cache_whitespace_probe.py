"""Tiny Opus 5.5 probe: does a cached block's prefix depend on whether it is the LAST block?"""
import sys
import time
import uuid

sys.path.insert(0, ".")  # run from the repo root
from dotenv import load_dotenv

load_dotenv(".env")
import anthropic

from src.utils.model_effort import adaptive_thinking

c = anthropic.Anthropic()
M = "claude-opus-5-5"
tag = uuid.uuid4().hex[:8]  # a fresh prefix, so no earlier entry interferes
body = f"Probe {tag}. " + " ".join(f"Line {i}: the quick brown fox number {i} jumps over lazy dog {i*7}."
                                   for i in range(700))
spent = 0.0


def req(blocks, label):
    global spent
    kw = {"model": M, "max_tokens": 0, "thinking": adaptive_thinking(M), "output_config": {"effort": "high"},
          "messages": [{"role": "user", "content": blocks}]}
    u = c.messages.create(**kw).usage
    cost = (u.input_tokens * 4 + (u.cache_creation_input_tokens or 0) * 5 + (u.cache_read_input_tokens or 0) * 0.2) / 1e6
    spent += cost
    print(f"{label:55s} in={u.input_tokens:>6} write={u.cache_creation_input_tokens:>6} "
          f"read={u.cache_read_input_tokens:>6}  ${cost:.4f}")
    time.sleep(2)


cc = {"type": "ephemeral"}
# 1. head ENDS WITH WHITESPACE: followed by a block, then alone
h = body + "\n\n"
req([{"type": "text", "text": h, "cache_control": cc}, {"type": "text", "text": "TAIL"}], "A1 head+'\\n\\n' then tail (writes)")
req([{"type": "text", "text": h, "cache_control": cc}], "A2 same head alone (read = whitespace kept)")
req([{"type": "text", "text": h, "cache_control": cc}, {"type": "text", "text": "OTHER"}], "A3 same head + different tail (read?)")
# 2. head WITHOUT trailing whitespace
h2 = "X" + body
req([{"type": "text", "text": h2, "cache_control": cc}, {"type": "text", "text": "\n\nTAIL"}], "B1 rstripped head then tail (writes)")
req([{"type": "text", "text": h2, "cache_control": cc}], "B2 same head alone (read?)")
print(f"total ${spent:.4f}")
