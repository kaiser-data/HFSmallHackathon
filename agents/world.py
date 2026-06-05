"""Dream environments (Mission skins) + externalized world-state.

The world-state lives HERE, outside the models — small models can't hold a long
coherent context, so the fleet keeps the source of truth and feeds slices to each
agent. Add a new environment by appending to ENVIRONMENTS; the engine is generic.
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


@dataclass
class WorldState:
    env_id: str
    env_name: str
    emoji: str
    location: str
    mission: str
    inhabitant: str
    inventory: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)   # short memory of key beats
    progress: int = 0                                # soft 0..100
    turn: int = 0
    complete: bool = False

    @classmethod
    def from_env(cls, env: Environment) -> "WorldState":
        return cls(env_id=env.id, env_name=env.name, emoji=env.emoji,
                   location=env.start_location, mission=env.mission,
                   inhabitant=env.inhabitant)

    def context(self) -> str:
        """A compact slice of truth handed to each agent every turn."""
        recent = " | ".join(self.log[-4:]) if self.log else "(nothing yet)"
        carry = ", ".join(self.inventory) if self.inventory else "nothing"
        return (f"WORLD: {self.env_name}. LOCATION: {self.location}. "
                f"MISSION: {self.mission} (progress {self.progress}%). "
                f"CARRYING: {carry}. RECENT BEATS: {recent}.")
