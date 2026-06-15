"""Minimal agent abstraction for a fleet of small models.

A small framework for small models — no LangChain. An Agent is a persona bound
to a backend role; it can stream prose (for the dream) or return structured JSON
(for Hobbes' choices and the world-state Keeper).

Set DAYDREAM_MOCK=1 to run the whole app with no inference backend — agents emit
templated placeholder text so the UI is fully playable offline during dev.
"""
from __future__ import annotations
import os
import re
import json
import time
import random
from dataclasses import dataclass, field
from typing import Iterator

from .registry import get_client

MOCK = bool(os.environ.get("DAYDREAM_MOCK"))
# A scaled-down Modal endpoint answers its first requests with a FAST 503
# ("loading model"), not a slow block — so the retry WINDOW must span the whole
# cold start (~48s cached, longer on a true cold boot), or we degrade to the
# "dream wavers" fallback right when we should be patiently waiting. 6×15s ≈ 90s
# of recovery, matching the UI's "first turn ~90s" promise. Tune via env.
RETRIES = int(os.environ.get("DAYDREAM_RETRIES", "6"))
RETRY_WAIT = float(os.environ.get("DAYDREAM_RETRY_WAIT", "15"))

# Both 2026 small models reason by default, which pollutes prose with "Thinking
# Process:" text and adds seconds per turn. Two levers, applied to every call:
#   - chat_template_kwargs enable_thinking=False -> disables Qwen3.5 thinking
#     (vLLM honors it; llama.cpp tolerates it harmlessly)
#   - "/no_think" in the system prompt -> disables MiniCPM thinking
#     (Qwen ignores the token)
NO_THINK = "/no_think"
EXTRA_BODY = {"chat_template_kwargs": {"enable_thinking": False}}


@dataclass
class LLMConfig:
    temperature: float = 0.8
    max_tokens: int = 300
    top_p: float = 0.95


def _mock_line(name: str, user: str) -> str:
    banks = {
        "Dreamweaver": [
            "The air thickens to syrup; the path ahead folds like wet paper and opens onto somewhere new.",
            "A sound you can almost see ripples across the ground, and the world leans in to listen.",
        ],
        "Mischief": ["(A door appears where there was none, breathing softly.)",
                     "(Your shadow waves at you. It is not your shadow.)"],
        "Hobbes": ['{"reaction": "Okay, I have a bad feeling AND a good feeling.", '
                   '"choices": ["Open the breathing door", "Follow the hum deeper", "Ask Hobbes to scout"]}'],
        "Keeper": ['{"location":"a stranger clearing","add_items":["a humming pebble"],'
                   '"progress_delta":15,"mission_complete":false,"note":"crept deeper in"}'],
    }
    return random.choice(banks.get(name, ["..."]))


def loose_json(text: str) -> dict:
    """Best-effort extract the first valid JSON object from a model reply.

    Small models often wrap JSON in prose or fences, and a greedy ``{.*}`` match
    breaks as soon as the reply contains more than one object. Use the JSON
    decoder directly from each candidate ``{`` so braces inside strings and
    trailing chatter are handled by the parser instead of regex.
    """
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text or ""):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return {}


@dataclass
class Agent:
    name: str            # display name, e.g. "Hobbes"
    role: str            # registry key: "specialist" | "router"
    system: str          # persona / instructions
    cfg: LLMConfig = field(default_factory=LLMConfig)

    def _messages(self, user: str, history: list[dict] | None) -> list[dict]:
        return [{"role": "system", "content": f"{self.system} {NO_THINK}"}, *(history or []),
                {"role": "user", "content": user}]

    def stream(self, user: str, history: list[dict] | None = None) -> Iterator[str]:
        if MOCK:
            for tok in _mock_line(self.name, user).split(" "):
                yield tok + " "
            return
        client, model = get_client(self.role)
        # Open the stream with cold-start retries; once streaming we don't restart
        # mid-sentence — a stream that breaks just ends the (already-narrated) beat.
        last_err: Exception | None = None
        for attempt in range(RETRIES):
            try:
                s = client.chat.completions.create(
                    model=model, messages=self._messages(user, history),
                    temperature=self.cfg.temperature, max_tokens=self.cfg.max_tokens,
                    top_p=self.cfg.top_p, stream=True, extra_body=EXTRA_BODY,
                )
                for chunk in s:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                return
            except Exception as e:  # transient: cold endpoint, timeout, blip
                last_err = e
                if attempt < RETRIES - 1:
                    time.sleep(RETRY_WAIT)
        # Degraded but never crashing: keep the dream moving with a soft beat.
        yield "The dream wavers for a moment, then steadies."
        _ = last_err

    def say(self, user: str, history: list[dict] | None = None) -> str:
        return "".join(self.stream(user, history))

    def json(self, user: str, history: list[dict] | None = None) -> dict:
        """Non-streaming structured call; tolerant of small-model JSON wobble.

        Returns {} on any failure (cold endpoint, timeout, unparseable) — every
        caller already treats {} as "no update / use defaults", so the turn
        survives a wobbly small model rather than crashing.
        """
        if MOCK:
            return loose_json(_mock_line(self.name, user)) or {}
        client, model = get_client(self.role)
        for attempt in range(RETRIES):
            try:
                r = client.chat.completions.create(
                    model=model, messages=self._messages(user, history),
                    temperature=min(self.cfg.temperature, 0.4), max_tokens=self.cfg.max_tokens,
                    extra_body=EXTRA_BODY,
                )
                msg = r.choices[0].message
                # Reasoning models (e.g. MiniCPM5) split thinking into
                # reasoning_content; the JSON we want is in content. Fall back to
                # reasoning_content only if content is empty.
                text = msg.content or getattr(msg, "reasoning_content", "") or ""
                return loose_json(text)
            except Exception:
                if attempt < RETRIES - 1:
                    time.sleep(RETRY_WAIT)
        return {}
