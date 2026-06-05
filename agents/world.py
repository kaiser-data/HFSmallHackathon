"""Dream environments (Mission skins) + externalized world-state.

The world-state lives HERE, outside the models — small models can't hold a long
coherent context, so the fleet keeps the source of truth and feeds slices to each
agent. Add a new environment by appending to ENVIRONMENTS; the engine is generic.

DAYDREAM — Press Your Luck, Keep Your Tiger:
the state also owns the *game* — LUCIDITY (a draining clock), COURAGE (Hobbes'
bond meter), MENACE (the Nightmare's pressure), and a code-owned TIER_TABLE that
fixes the risk/reward math. Models never decide outcomes; code does.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Environment:
    id: str
    name: str
    emoji: str
    opening: str          # scene the dreamer wakes into
    mission: str          # the soft goal (ignorable — wandering is fine)
    start_location: str
    inhabitant: str       # one-line persona seed for the local NPC voice


ENVIRONMENTS: dict[str, Environment] = {
    "candy_desert": Environment(
        "candy_desert", "The Candy Desert", "🏜",
        "Two pale moons hang over endless dunes of crystalline sugar. Something hums beneath the sand.",
        "Find what is humming under the dunes — or don't, and just wander.",
        "a ridge of warm sugar-glass",
        "a nervous gummy bear who knows too much and trusts too little",
    ),
    "sunken_city": Environment(
        "sunken_city", "The Sunken City", "🌊",
        "You breathe water like air. Drowned bell-towers lean in the blue dark, trying to ring.",
        "Find the song the bells are reaching for.",
        "the steps of a flooded cathedral",
        "an old eel who used to be the city's bellringer",
    ),
    "noir_alley": Environment(
        "noir_alley", "Rain Street", "🕵️",
        "Neon bleeds into wet asphalt. Somebody stole the moon, and the whole city's gone dim.",
        "Find out who took the moon.",
        "under a flickering sign that says OPEN, lying",
        "a trench-coated cat informant who speaks only in riddles and prices",
    ),
    "red_planet": Environment(
        "red_planet", "The Red Planet", "🚀",
        "Rust-colored wind. Your tin rocket ticks as it cools. Something tall watches from the dunes.",
        "Get the rocket flying again before the tall thing reaches you.",
        "beside a cooling tin rocket",
        "a polite but very hungry zorch that insists it just wants to talk",
    ),
    "token_wood": Environment(
        "token_wood", "Thousand Token Wood", "🌲",
        "A wood where every leaf is a word. Step wrong and the sentence changes around you.",
        "Reach the clearing where the wood is trying to finish a thought.",
        "at the wood's whispering edge",
        "a small fox made of footnotes who narrates itself",
    ),
}


# --- The game's spine: CODE owns this, never the model ---------------------
# Each gambit tier fixes its own risk/reward. resolver.py reads these; the
# personality models only ever pick the *words* on the buttons, never the math.
# Tuned for a tense-but-winnable ~3-min arc (8-12 turns). Each tier is a real
# choice: safe is the patient grind (10/turn clears 100 well within a run),
# reckless is a genuine gamble for speed — risky, not a death sentence.
TIER_TABLE: dict[str, dict[str, int | float]] = {
    "safe":     {"lucidity_cost": 1, "progress_reward": 10, "courage_gain": 0,
                 "fail_chance": 0.05, "menace_delta": 0},
    "bold":     {"lucidity_cost": 2, "progress_reward": 22, "courage_gain": 1,
                 "fail_chance": 0.25, "menace_delta": 1},
    "reckless": {"lucidity_cost": 3, "progress_reward": 40, "courage_gain": 2,
                 "fail_chance": 0.40, "menace_delta": 1},
}
TIERS = ("safe", "bold", "reckless")

LUCIDITY_START = 16
MENACE_THRESHOLD = 5     # at/above this, the Nightmare forces a Flee-or-Face beat
COURAGE_MAX = 6


def courage_tier(courage: int) -> str:
    """Maps the COURAGE meter to Hobbes' mood — drives his system-prompt slice."""
    if courage <= 1:
        return "timid"      # cowering, joke-deflecting, begs you off the red button
    if courage <= 3:
        return "warming"    # nervous but rallying
    return "brave"          # loyal, steady: "do it, I've got you"


@dataclass
class WorldState:
    env_id: str
    env_name: str
    emoji: str
    location: str
    mission: str
    inhabitant: str
    seed: str = "dream"
    inventory: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)   # short memory of key beats
    scars: list[str] = field(default_factory=list)  # failed-gamble marks (card flavor)
    progress: int = 0                                # soft 0..100 -> WAKE WITH THE PRIZE
    lucidity: int = LUCIDITY_START                   # 0 -> LOST IN THE DREAM
    courage: int = 0                                 # Hobbes' bond, 0..COURAGE_MAX
    menace: int = 0                                  # the Nightmare's pressure
    peak_menace: int = 0                             # high-water mark (card flavor)
    turn: int = 0
    complete: bool = False                           # won
    lost: bool = False                               # lucidity ran out

    @classmethod
    def from_env(cls, env: Environment, seed: str = "dream") -> "WorldState":
        return cls(env_id=env.id, env_name=env.name, emoji=env.emoji,
                   location=env.start_location, mission=env.mission,
                   inhabitant=env.inhabitant, seed=seed)

    # --- derived ---
    @property
    def over(self) -> bool:
        return self.complete or self.lost

    @property
    def mood(self) -> str:
        return courage_tier(self.courage)

    @property
    def nightmare_near(self) -> bool:
        return self.menace >= MENACE_THRESHOLD

    def context(self) -> str:
        """A compact slice of truth handed to each agent every turn."""
        recent = " | ".join(self.log[-4:]) if self.log else "(nothing yet)"
        carry = ", ".join(self.inventory) if self.inventory else "nothing"
        return (f"WORLD: {self.env_name}. LOCATION: {self.location}. "
                f"MISSION: {self.mission} (progress {self.progress}%). "
                f"LUCIDITY: {self.lucidity}/{LUCIDITY_START}. "
                f"HOBBES_COURAGE: {self.courage} ({self.mood}). "
                f"MENACE: {self.menace}{' (NIGHTMARE CLOSE)' if self.nightmare_near else ''}. "
                f"CARRYING: {carry}. RECENT BEATS: {recent}.")
