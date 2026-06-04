"""Minimal agent abstraction: a persona + a backend role + a streaming call.

Kept deliberately small — small models, small framework. No LangChain.
Supports plain chat and (optional) tool calling against OpenAI-compatible servers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterator, Callable, Any

from .registry import get_client


@dataclass
class LLMConfig:
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.95


@dataclass
class Agent:
    name: str                       # display name, e.g. "The Skeptic"
    role: str                       # registry key: "specialist" | "router"
    system: str                     # persona / instructions
    cfg: LLMConfig = field(default_factory=LLMConfig)
    tools: list[dict] | None = None
    tool_impls: dict[str, Callable[..., Any]] = field(default_factory=dict)

    def _messages(self, history: list[dict], user: str | None) -> list[dict]:
        msgs = [{"role": "system", "content": self.system}, *history]
        if user is not None:
            msgs.append({"role": "user", "content": user})
        return msgs

    def stream(self, user: str | None = None, history: list[dict] | None = None) -> Iterator[str]:
        """Yield response text deltas. Used to animate the Gradio UI."""
        client, model = get_client(self.role)
        stream = client.chat.completions.create(
            model=model,
            messages=self._messages(history or [], user),
            temperature=self.cfg.temperature,
            max_tokens=self.cfg.max_tokens,
            top_p=self.cfg.top_p,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def say(self, user: str | None = None, history: list[dict] | None = None) -> str:
        return "".join(self.stream(user=user, history=history))
