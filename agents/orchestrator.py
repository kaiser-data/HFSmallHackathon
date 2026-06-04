"""The Council orchestrator (Pitch A).

A tiny router agent decides who speaks, specialist personas debate, and a chair
synthesizes a verdict. Designed to STREAM so the Gradio UI can animate turns.

Reusable for other pitches: swap the persona list + the synthesis prompt.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator

from .base import Agent, LLMConfig


def default_council() -> "Council":
    voices = [
        Agent("The Optimist", "specialist",
               "You are The Optimist on a whimsical advice council. In <=3 sentences, "
               "argue the hopeful, adventurous case. Be warm, concrete, a little funny."),
        Agent("The Skeptic", "specialist",
               "You are The Skeptic. In <=3 sentences, name the realest risk and the "
               "hidden cost. Dry wit, never cruel."),
        Agent("The Pragmatist", "specialist",
               "You are The Pragmatist. In <=3 sentences, give the smallest concrete "
               "next step the person could actually take this week."),
    ]
    chair = Agent("The Chair", "router",
                  "You chair a tiny advice council. Given the question and the three "
                  "members' takes, deliver a short, decisive, delightful verdict (<=4 "
                  "sentences) that honors the best point from each. End with a one-line "
                  "'Verdict:' the asker can screenshot.",
                  cfg=LLMConfig(temperature=0.6, max_tokens=400))
    return Council(voices=voices, chair=chair)


@dataclass
class Council:
    voices: list[Agent]
    chair: Agent

    def deliberate(self, question: str) -> Iterator[tuple[str, str]]:
        """Yield (speaker_name, text_delta) tuples across the whole session."""
        takes: list[str] = []
        for agent in self.voices:
            collected = ""
            for delta in agent.stream(user=f"The question: {question}"):
                collected += delta
                yield agent.name, delta
            takes.append(f"{agent.name}: {collected.strip()}")

        transcript = "\n".join(takes)
        chair_prompt = (
            f"Question: {question}\n\nThe council said:\n{transcript}\n\n"
            "Now deliver the verdict."
        )
        for delta in self.chair.stream(user=chair_prompt):
            yield self.chair.name, delta
