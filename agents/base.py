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
import random
from dataclasses import dataclass, field
from typing import Iterator

from .registry import get_client

MOCK = bool(os.environ.get("DAYDREAM_MOCK"))


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
    """Best-effort extract the first {...} object from a small model's reply."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


@dataclass
class Agent:
    name: str            # display name, e.g. "Hobbes"
    role: str            # registry key: "specialist" | "router"
    system: str          # persona / instructions
    cfg: LLMConfig = field(default_factory=LLMConfig)

    def _messages(self, user: str, history: list[dict] | None) -> list[dict]:
        return [{"role": "system", "content": self.system}, *(history or []),
                {"role": "user", "content": user}]

    def stream(self, user: str, history: list[dict] | None = None) -> Iterator[str]:
        if MOCK:
            for tok in _mock_line(self.name, user).split(" "):
                yield tok + " "
            return
        client, model = get_client(self.role)
        s = client.chat.completions.create(
            model=model, messages=self._messages(user, history),
            temperature=self.cfg.temperature, max_tokens=self.cfg.max_tokens,
            top_p=self.cfg.top_p, stream=True,
        )
        for chunk in s:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def say(self, user: str, history: list[dict] | None = None) -> str:
        return "".join(self.stream(user, history))

    def json(self, user: str, history: list[dict] | None = None) -> dict:
        """Non-streaming structured call; tolerant of small-model JSON wobble."""
        if MOCK:
            return loose_json(_mock_line(self.name, user)) or {}
        client, model = get_client(self.role)
        r = client.chat.completions.create(
            model=model, messages=self._messages(user, history),
            temperature=min(self.cfg.temperature, 0.4), max_tokens=self.cfg.max_tokens,
        )
        return loose_json(r.choices[0].message.content or "")
