"""One streamed Gemini call, for the Gemini writer and its revision (Session 407).

Why streamed: a non-streamed call returns ONE thought summary, written after the thinking, which
Google cuts off at about 3,300 characters, and which is often just a copy of a draft (Ps 29's
essay "thinking" was the opening of an earlier essay draft, ending mid-word). Streamed, the same
call returns a summary at each stage of the thinking (a probe: 14 summaries, 6,200 chars, real
reasoning: "Evaluating Interpretations", "Defining the Thesis" ...).

The reply is rebuilt for replay as the next turn's model Content: the thought summaries as they
came, and the answer's text fragments joined into one part that keeps the thought signature
(streamed, it arrives on an empty final text part). That is the shape a non-streamed reply has,
and a probe confirmed the API accepts it as the next turn after a JSON round trip."""
from dataclasses import dataclass
from typing import Any, List


@dataclass
class StreamedReply:
    text: str        # the answer (non-thought text), joined
    thinking: str    # every thought summary, in order, blank-line separated
    content: Any     # google.genai types.Content (role "model"), merged for replay
    usage: Any       # the last usage_metadata the stream reported (None if none came)
    finish: str      # the last finish reason, e.g. "STOP", "MAX_TOKENS"; "none" if none came


def merge_parts(parts: List[Any]) -> List[Any]:
    """Adjacent answer-text fragments become one Part that keeps any thought signature among them;
    thought parts and anything that is not plain text pass through unchanged."""
    from google.genai import types

    def plain_text(p) -> bool:
        return not p.thought and p.text is not None and not p.function_call

    merged: List[Any] = []
    for p in parts:
        if merged and plain_text(p) and plain_text(merged[-1]):
            prev = merged[-1]
            merged[-1] = types.Part(text=prev.text + p.text,
                                    thought_signature=prev.thought_signature or p.thought_signature)
        else:
            merged.append(p)
    return merged


def stream_generate(client, model: str, contents, config) -> StreamedReply:
    """Run `generate_content_stream` to the end and assemble the reply. Raises whatever the
    stream raises; the caller owns retries and billing."""
    from google.genai import types

    parts: List[Any] = []
    usage, finish = None, None
    for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
        if chunk.usage_metadata is not None:
            usage = chunk.usage_metadata
        for cand in (chunk.candidates or [])[:1]:
            if cand.finish_reason is not None:
                finish = cand.finish_reason
            parts.extend((cand.content.parts if cand.content else None) or [])
    merged = merge_parts(parts)
    text = "".join(p.text for p in merged if p.text and not p.thought)
    thinking = "\n\n".join(p.text.strip() for p in merged if p.text and p.thought and p.text.strip())
    return StreamedReply(text=text, thinking=thinking, content=types.Content(role="model", parts=merged),
                         usage=usage, finish=str(finish or "none").split(".")[-1])
