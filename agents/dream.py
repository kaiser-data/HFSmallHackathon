"""DAYDREAM — the dream-fleet engine.

You are the dreamer/commander. Each turn:
  1. Dreamweaver narrates the world's response to your intent  (specialist model)
  2. Mischief sometimes injects a surreal twist                (specialist model)
  3. Hobbes, your companion, reacts and ESCALATES the choice   (specialist model)
  4. The Keeper updates externalized world-state               (tiny router model)

`play()` streams (speaker, delta) for the UI; afterwards `engine.choices` holds
Hobbes' escalation options and `engine.state` reflects the updated world.
"""
from __future__ import annotations
import random
from dataclasses import dataclass, field

from .base import Agent, LLMConfig
from .world import ENVIRONMENTS, WorldState

MISCHIEF_CHANCE = 0.45

DREAMWEAVER_SYS = (
    "You are the Dreamweaver, narrator of a lucid dream. Respond to the dreamer's "
    "intent in 2-4 vivid, concrete sentences. Dream-logic is welcome: things may "
    "morph, but honor the world-state and recent beats you're given. Never ask the "
    "dreamer questions — just show what happens. Second person ('you')."
)
MISCHIEF_SYS = (
    "You are Mischief, the dream's prankster physics. In ONE short sentence, add a "
    "single surreal twist to the scene just described. Whimsical, never gory. "
    "Write it in parentheses."
)
HOBBES_SYS = (
    "You are Hobbes — the dreamer's loyal, funny, slightly cowardly companion (think "
    "a stuffed tiger come to life). Given the scene, react in ONE short line of "
    "dialogue, then offer 2-3 short, distinct things the dreamer could do next. "
    'Reply ONLY as JSON: {"reaction": "<one line>", "choices": ["...","...","..."]}. '
    "Choices are <=6 words, imperative, fun."
)
KEEPER_SYS = (
    "You are the Keeper of world-state. Given the scene and the dreamer's action, "
    "reply ONLY as compact JSON with keys: location (string), add_items (string[]), "
    "drop_items (string[]), progress_delta (int 0-30), mission_complete (bool), "
    "note (a <=8-word memory of this beat). No prose."
)


@dataclass
class DreamEngine:
    state: WorldState | None = None
    choices: list[str] = field(default_factory=list)

    dreamweaver: Agent = field(default_factory=lambda: Agent(
        "Dreamweaver", "specialist", DREAMWEAVER_SYS, LLMConfig(0.95, 320)))
    mischief: Agent = field(default_factory=lambda: Agent(
        "Mischief", "specialist", MISCHIEF_SYS, LLMConfig(1.05, 90)))
    hobbes: Agent = field(default_factory=lambda: Agent(
        "Hobbes", "specialist", HOBBES_SYS, LLMConfig(0.85, 220)))
    keeper: Agent = field(default_factory=lambda: Agent(
        "Keeper", "router", KEEPER_SYS, LLMConfig(0.2, 220)))

    # --- lifecycle ---
    def start(self, env_id: str) -> None:
        env = ENVIRONMENTS[env_id]
        self.state = WorldState.from_env(env)
        self.state.log.append("the dream begins")
        self.choices = []

    def _ctx(self) -> str:
        return self.state.context()

    # --- one turn of the dream; generator of (speaker, text_delta) ---
    def play(self, intent: str):
        s = self.state
        if s is None:
            raise RuntimeError("call start(env_id) before play()")
        s.turn += 1

        # 1) Dreamweaver
        scene = ""
        for d in self.dreamweaver.stream(f"{self._ctx()}\nThe dreamer: {intent}\nNarrate what happens."):
            scene += d
            yield "Dreamweaver", d

        # 2) Mischief (sometimes)
        if random.random() < MISCHIEF_CHANCE:
            twist = ""
            for d in self.mischief.stream(f"{self._ctx()}\nScene just now: {scene}\nAdd one twist."):
                twist += d
                yield "Mischief", d
            scene += " " + twist

        # 3) Hobbes reacts + escalates (structured, single chunk)
        h = self.hobbes.json(
            f"{self._ctx()}\nThe dreamer did: {intent}\nScene: {scene}\n"
            f"Local presence: {s.inhabitant}. React and offer choices."
        )
        reaction = (h.get("reaction") or "...").strip()
        self.choices = [c.strip() for c in (h.get("choices") or []) if c.strip()][:3]
        yield "Hobbes", reaction

        # 4) Keeper updates externalized state
        self._update(intent, scene)

    def _update(self, intent: str, scene: str) -> None:
        s = self.state
        patch = self.keeper.json(f"{self._ctx()}\nAction: {intent}\nScene: {scene}\nUpdate state.")
        if loc := patch.get("location"):
            s.location = str(loc)[:80]
        for item in patch.get("add_items", []) or []:
            if item and item not in s.inventory:
                s.inventory.append(str(item)[:40])
        for item in patch.get("drop_items", []) or []:
            if item in s.inventory:
                s.inventory.remove(item)
        try:
            s.progress = max(0, min(100, s.progress + int(patch.get("progress_delta", 0) or 0)))
        except (TypeError, ValueError):
            pass
        if note := patch.get("note"):
            s.log.append(str(note)[:60])
        if patch.get("mission_complete") or s.progress >= 100:
            s.complete = True
            s.progress = 100
