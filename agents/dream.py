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
import re
import concurrent.futures
from dataclasses import dataclass, field

from .base import Agent, LLMConfig
from .world import ENVIRONMENTS, WorldState, TIERS, courage_tier, COURAGE_MAX
from .stories import arc_of, beat_for
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
    "You are the Dreamweaver, weaving ONE coherent dream-story that moves toward the "
    "dreamer's GOAL (the MISSION in the world-state). You are told the action and whether "
    "it SUCCEEDED, partly worked, or FAILED — honor that verdict: on success move the story "
    "a clear step CLOSER to the goal; on failure set it back or deepen the danger. Build on "
    "what came before and reflect how close they are (the progress %). Narrate in 2-3 vivid, "
    "concrete sentences. Dream-logic is welcome but stay consistent with the world-state. "
    "Never ask questions — show what happens. Second person."
)
NIGHTMARE_SYS = (
    "You are the Nightmare — the dread closing in on the dream. In ONE short, ominous "
    "sentence, press the menace closer (a sound, a shadow, the eyes nearer). Never gory; "
    "dreamlike dread. If told the Nightmare is CLOSE, make it a clear flee-or-face moment."
)
HOBBES_SYS = (
    "You are Hobbes — the dreamer's companion, a stuffed tiger come to life. React to the "
    "scene in ONE short line of dialogue, then name THREE things the dreamer could do next. "
    "CRUCIAL: each option must build directly on what JUST happened and the concrete things "
    "present in THIS scene — the specific objects, places, and creatures named in it — and be "
    "a real way to pursue the dreamer's GOAL (the mission). They are the next steps in an "
    "unfolding story, never generic 'look around / go forward' filler. Escalate cautious→daring "
    "(1=safe, 2=bold, 3=reckless). "
    'Reply ONLY as JSON: {"reaction":"<one line>","choices":["<safe>","<bold>","<reckless>"]}. '
    "Each choice ≤6 words, imperative, vivid, and specific to this exact moment."
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

    # max_tokens is the dominant lever on warm latency (generation time is ~linear
    # in tokens, and --enforce-eager decode is unhurried on the 27B). Each cap is
    # sized to the job: 2-4 sentences of prose, one ominous line, small JSON blobs.
    dreamweaver: Agent = field(default_factory=lambda: Agent(
        "Dreamweaver", "specialist", DREAMWEAVER_SYS, LLMConfig(0.95, 110)))
    nightmare: Agent = field(default_factory=lambda: Agent(
        "Nightmare", "specialist", NIGHTMARE_SYS, LLMConfig(1.0, 42)))
    hobbes: Agent = field(default_factory=lambda: Agent(
        "Hobbes", "specialist", HOBBES_SYS, LLMConfig(0.85, 85)))
    # Keeper is presentational memory, not game math — give it a SHORT retry budget
    # so a cold/slow router degrades fast (state simply doesn't update this turn)
    # instead of holding the turn at the keeper_job join. The narrator keeps the
    # wide default budget to patiently ride out a cold start.
    keeper: Agent = field(default_factory=lambda: Agent(
        "Keeper", "router", KEEPER_SYS, LLMConfig(0.2, 160), retries=2, retry_wait=3))

    # Persistent pool for fire-and-forget background work (the Keeper's state write).
    # Not part of equality/repr.
    _pool: concurrent.futures.ThreadPoolExecutor = field(
        default_factory=lambda: concurrent.futures.ThreadPoolExecutor(max_workers=3),
        repr=False, compare=False)

    # --- lifecycle ---
    def start(self, env_id: str, seed: str = "dream") -> None:
        env = ENVIRONMENTS[env_id]
        self.state = WorldState.from_env(env, seed=seed)
        # Use the deep arc's richer goal as the visible quest, if this world has one.
        arc = arc_of(env_id)
        if arc and arc.get("goal"):
            self.state.mission = arc["goal"]
        self.state.log.append("the dream begins")
        self.gambits = []
        self.last_outcome = None

    def _beat(self, progress: int) -> str:
        return beat_for(self.state.env_id, progress) if self.state else ""

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

        # Will this beat END the dream? Pre-computing it lets the Dreamweaver narrate
        # a real CLIMAX — reaching the goal, or the dream collapsing — instead of a
        # flat beat that the code then silently turns into a win/loss.
        climax = ""
        if out:
            if s.progress + out.progress_reward >= 100:
                climax = (" THIS IS THE CLIMAX: the dreamer finally reaches the goal and "
                          "wakes with the prize. Narrate the triumphant resolution of the quest.")
            elif s.lucidity - out.lucidity_cost <= 0:
                climax = (" THIS IS THE END: lucidity runs out and the dream dissolves before "
                          "the goal. Narrate a poignant, fading collapse.")

        # Will this beat END the dream? (drives both the climax line and whether we
        # ask Hobbes for new gambits or for a farewell.)
        will_end = bool(out) and (
            s.progress + out.progress_reward >= 100 or s.lucidity - out.lucidity_cost <= 0)

        # PARALLELISM (the realtime win): Hobbes reacts to the SITUATION — the action,
        # the verdict, his projected mood — not to the exact prose. So kick him off
        # NOW, concurrently with the Dreamweaver. vLLM's continuous batching runs both
        # on the same warm GPU at once, so a turn is ~one model-call deep instead of
        # two (~2x faster) — no extra machines needed.
        hobbes_future = None
        if not will_end:
            proj_courage = min(COURAGE_MAX, s.courage + (out.courage_gain if out else 0))
            proj_mood = courage_tier(proj_courage)
            hobbes_future = self._pool.submit(
                self.hobbes.json,
                f"{self._ctx()}\nYOUR MOOD: {MOOD_NOTE[proj_mood]}\n"
                f"The dreamer just chose: {intent}\nThat action {verdict}.\n"
                f"React in one line, then offer three gambits that pursue the goal.")

        # 2) Dreamweaver narrates the pre-decided outcome — concurrent with Hobbes,
        # and STEERED BY THE STORY ARC: it's handed the current plot beat (keyed to
        # progress) so the dream evolves through setup → twist → cost → climax instead
        # of disconnected moments. The beat is the destination; the verdict is how the
        # player's action moves toward (success) or away from (fail) it.
        proj_progress = min(100, s.progress + (out.progress_reward if out else 0))
        beat = self._beat(proj_progress)
        story = f"\nSTORY BEAT (narrate toward this, don't quote it): {beat}" if beat else ""
        scene = ""
        for d in self.dreamweaver.stream(
                f"{self._ctx()}\nThe dreamer: {intent}\nThis action {verdict}.{climax}{story}\n"
                f"Advance the story toward the beat and narrate what happens now."):
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

        # 6) Keeper writes presentational state in the background (fire-and-forget) —
        # never on the turn's critical path.
        self._pool.submit(self._update, self._ctx(), intent, scene)

        # 5) Hobbes — already computed IN PARALLEL with the narration above, so this
        # is ~instant by the time the prose finishes.
        if s.over:
            self.gambits = []
            yield "Hobbes", self.farewell()
        else:
            h = hobbes_future.result() if hobbes_future else {}
            reaction = str(h.get("reaction") or "...").strip()
            ch = h.get("choices")
            labels = ([c.strip() for c in ch if isinstance(c, str) and c.strip()][:3]
                      if isinstance(ch, list) else [])
            self.gambits = self._make_gambits(labels)
            yield "Hobbes", reaction

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

    def _update(self, ctx: str, intent: str, scene: str) -> None:
        s = self.state
        if s is None:
            return
        patch = self.keeper.json(f"{ctx}\nAction: {intent}\nScene: {scene}\nUpdate state.")
        if not isinstance(patch, dict):
            return
        if loc := patch.get("location"):
            # The router sometimes echoes the context's "WORLD:"/"LOCATION:" label
            # back into the value; strip it so the state line doesn't double up.
            clean = re.sub(r"^\s*(WORLD|LOCATION)\s*:\s*", "", str(loc), flags=re.I).strip()
            if clean:
                s.location = clean[:80]
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
