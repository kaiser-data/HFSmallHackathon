"""DAYDREAM — Press Your Luck, Keep Your Tiger.

You are the dreamer. Each turn you take a GAMBIT — safe, bold, or reckless. CODE
owns the dice (resolver.py) and all the math; the small models only supply words
and voice. Two meters decide your fate: LUCIDITY drains to 0 → lost in the dream;
PROGRESS climbs to 100 → wake with the prize. A third meter, COURAGE, is Hobbes'
bond — it rises when you survive bets you made *with* him, and his voice grows
from cowering to brave because of it.

Per turn:
  1. resolve() decides the outcome of the chosen gambit   (CODE — seeded, fair)
  2. Dreamweaver narrates that pre-decided outcome         (specialist model)
  3. apply() moves the meters                              (CODE)
  4. Nightmare presses when MENACE is high / on a failure  (specialist model)
  5. Hobbes reacts (voice keyed to COURAGE) + offers the   (specialist model)
     next three gambits — labels only; CODE fixes the tiers
  6. Keeper updates narrative state: location, items, note (tiny router model)

`play()` streams (speaker, delta); afterwards `engine.gambits` holds the three
(label, tier) options and `engine.state` reflects the moved world.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .base import Agent, LLMConfig
from .world import ENVIRONMENTS, WorldState, TIERS, courage_tier
from .resolver import resolve, apply, Outcome

# Fixed escalation order the model's three labels are zipped onto. CODE owns the
# tier; the model never gets to decide how risky its own words are.
GAMBIT_TIERS = ("safe", "bold", "reckless")
DEFAULT_LABELS = {  # fallback when Hobbes' JSON doesn't parse (loose_json -> {})
    "safe": "Play it safe",
    "bold": "Take a real risk",
    "reckless": "Do the reckless thing",
}
TYPED_TIER = "bold"  # free-text intent is a real gamble, not free wandering

DREAMWEAVER_SYS = (
    "You are the Dreamweaver, narrator of a lucid dream. You are told the dreamer's "
    "action and whether it SUCCEEDED, partly worked, or FAILED — honor that verdict. "
    "Narrate the result in 2-4 vivid, concrete sentences. Dream-logic is welcome, but "
    "respect the world-state. Never ask questions — show what happens. Second person."
)
NIGHTMARE_SYS = (
    "You are the Nightmare — the dread closing in on the dream. In ONE short, ominous "
    "sentence, press the menace closer (a sound, a shadow, the eyes nearer). Never gory; "
    "dreamlike dread. If told the Nightmare is CLOSE, make it a clear flee-or-face moment."
)
HOBBES_SYS = (
    "You are Hobbes — the dreamer's companion, a stuffed tiger come to life. React to the "
    "scene in ONE short line of dialogue, then name THREE things the dreamer could do next, "
    "escalating from cautious to daring (1=safe, 2=bold, 3=reckless). "
    'Reply ONLY as JSON: {"reaction":"<one line>","choices":["<safe>","<bold>","<reckless>"]}. '
    "Each choice <=6 words, imperative, fun."
)
KEEPER_SYS = (
    "You are the Keeper of narrative state. Given the scene and action, reply ONLY as "
    "compact JSON: location (string), add_items (string[]), drop_items (string[]), "
    "note (a <=8-word memory of this beat). No prose. Do NOT score progress — that is owned elsewhere."
)

# Code-owned, courage-keyed farewells — the 'aww' lands every time, no live callback.
FAREWELL = {
    ("win", "brave"):    "We made it. I was brave because you were.",
    ("win", "warming"):  "We made it! I— I almost believed we would.",
    ("win", "timid"):    "We made it. I was scared the whole time, but we made it.",
    ("loss", "brave"):   "We ran out of dream. But I wasn't afraid — not with you.",
    ("loss", "warming"): "I tried to be brave… for you. Almost got there.",
    ("loss", "timid"):   "I'm sorry. I tried to be brave for you. I really tried.",
}

MOOD_NOTE = {
    "timid":   "You are very frightened right now. Cower, deflect with nervous jokes, and "
               "plead with the dreamer to avoid the riskiest option.",
    "warming": "You're still nervous but beginning to trust the dreamer; rally a little.",
    "brave":   "You have grown brave because of the dreamer. Be loyal and steady — 'I've got you.'",
}


@dataclass
class DreamEngine:
    state: WorldState | None = None
    gambits: list[tuple[str, str]] = field(default_factory=list)  # [(label, tier), ...]
    last_outcome: Outcome | None = None

    dreamweaver: Agent = field(default_factory=lambda: Agent(
        "Dreamweaver", "specialist", DREAMWEAVER_SYS, LLMConfig(0.95, 320)))
    nightmare: Agent = field(default_factory=lambda: Agent(
        "Nightmare", "specialist", NIGHTMARE_SYS, LLMConfig(1.0, 90)))
    hobbes: Agent = field(default_factory=lambda: Agent(
        "Hobbes", "specialist", HOBBES_SYS, LLMConfig(0.85, 220)))
    keeper: Agent = field(default_factory=lambda: Agent(
        "Keeper", "router", KEEPER_SYS, LLMConfig(0.2, 220)))

    # --- lifecycle ---
    def start(self, env_id: str, seed: str = "dream") -> None:
        env = ENVIRONMENTS[env_id]
        self.state = WorldState.from_env(env, seed=seed)
        self.state.log.append("the dream begins")
        self.gambits = []
        self.last_outcome = None

    def _ctx(self) -> str:
        return self.state.context()

    @property
    def choices(self) -> list[str]:  # back-compat for any caller expecting labels
        return [label for label, _ in self.gambits]

    # --- one turn; generator of (speaker, text_delta) ---
    def play(self, intent: str, tier: str | None = None):
        s = self.state
        if s is None:
            raise RuntimeError("call start(env_id) before play()")
        if s.over:
            return
        s.turn += 1

        # 1) CODE decides the outcome of the gambit (None on the opening arrival turn)
        out = resolve(tier, s.seed, s.turn) if tier else None
        self.last_outcome = out
        verdict = {"success": "SUCCEEDED", "partial": "partly worked",
                   "fail": "FAILED"}.get(out.result, "happens") if out else "happens"

        # 2) Dreamweaver narrates the pre-decided outcome
        scene = ""
        for d in self.dreamweaver.stream(
                f"{self._ctx()}\nThe dreamer: {intent}\nThis action {verdict}. "
                f"Narrate the result."):
            scene += d
            yield "Dreamweaver", d

        # 3) CODE moves the meters (the ONLY place gamble math hits state)
        if out:
            apply(s, out)

        # 4) Nightmare presses — only when menace is high or the gamble failed
        if s.nightmare_near or (out and out.result == "fail"):
            close = "The Nightmare is CLOSE — flee or face it. " if s.nightmare_near else ""
            twist = ""
            for d in self.nightmare.stream(f"{self._ctx()}\n{close}Scene: {scene}\nPress closer."):
                twist += d
                yield "Nightmare", d
            scene += " " + twist

        # 5) Hobbes reacts (voice keyed to courage) + offers the next three gambits
        if not s.over:
            h = self.hobbes.json(
                f"{self._ctx()}\nYOUR MOOD: {MOOD_NOTE[s.mood]}\n"
                f"The dreamer did: {intent}\nScene: {scene}\nReact and offer three gambits."
            )
            reaction = str(h.get("reaction") or "...").strip()
            ch = h.get("choices")
            labels = ([c.strip() for c in ch if isinstance(c, str) and c.strip()][:3]
                      if isinstance(ch, list) else [])
            self.gambits = self._make_gambits(labels)
            yield "Hobbes", reaction
        else:
            self.gambits = []
            yield "Hobbes", self.farewell()

        # 6) Keeper updates narrative state (code already owns the game math)
        self._update(intent, scene)

    def _make_gambits(self, labels: list[str]) -> list[tuple[str, str]]:
        """Zip the model's words onto code-fixed tiers; fall back per missing slot."""
        out = []
        for i, tier in enumerate(GAMBIT_TIERS):
            label = labels[i] if i < len(labels) else DEFAULT_LABELS[tier]
            out.append((label or DEFAULT_LABELS[tier], tier))
        return out

    def farewell(self) -> str:
        s = self.state
        return FAREWELL[("win" if s.complete else "loss", s.mood)]

    def _update(self, intent: str, scene: str) -> None:
        s = self.state
        patch = self.keeper.json(f"{self._ctx()}\nAction: {intent}\nScene: {scene}\nUpdate state.")
        if loc := patch.get("location"):
            s.location = str(loc)[:80]
        add = patch.get("add_items")
        for item in (add if isinstance(add, list) else []):
            if isinstance(item, str) and item and item not in s.inventory:
                s.inventory.append(item[:40])
        drop = patch.get("drop_items")
        for item in (drop if isinstance(drop, list) else []):
            if item in s.inventory:
                s.inventory.remove(item)
        if note := patch.get("note"):
            s.log.append(str(note)[:60])
