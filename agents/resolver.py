"""The Outcome Oracle's spine — CODE-owned, deterministic, model-free.

The duel's verdict: the model must NEVER decide whether a gamble succeeds, or the
roguelike isn't fair and the "why small models" story is decorative. So pass/fail
and every reward magnitude are computed here from a seeded RNG + the TIER_TABLE.
The router model only writes the *flavor sentence* for an outcome already decided.

Deterministic by (seed, turn): the same dream seed always replays the same dice,
which is what makes the Dream Journal card's "beat my run: seed abc123" honest.
"""
from __future__ import annotations
import random
from dataclasses import dataclass

from .world import TIER_TABLE, WorldState, COURAGE_MAX


@dataclass
class Outcome:
    tier: str
    result: str            # "success" | "partial" | "fail"
    roll: int              # 1..100, shown as the visible die
    fail_threshold: int    # roll <= this = fail; shown on the HUD
    lucidity_cost: int
    progress_reward: int
    courage_gain: int
    menace_delta: int

    @property
    def won_roll(self) -> bool:
        return self.result != "fail"


def _rng(seed: str, turn: int) -> random.Random:
    """Stable per-(seed, turn) stream — no global Math.random/Date dependence."""
    return random.Random(f"{seed}:{turn}")


def resolve(tier: str, seed: str, turn: int) -> Outcome:
    """Roll one gambit. Pure: identical (tier, seed, turn) -> identical Outcome."""
    spec = TIER_TABLE.get(tier, TIER_TABLE["safe"])
    rng = _rng(seed, turn)
    roll = rng.randint(1, 100)
    fail_threshold = int(spec["fail_chance"] * 100)

    if roll <= fail_threshold:
        result = "fail"
    elif roll <= fail_threshold + 20:        # a 20-pt band above the line = grazed it
        result = "partial"
    else:
        result = "success"

    # Reward math, all code-owned. KEY DESIGN: the story ALWAYS proceeds toward the
    # goal — every gambit gives *some* progress, so the dream never stalls. The dice
    # decides the COST, not whether anything happens:
    #   success → big leap forward, the Nightmare eases, Hobbes grows braver
    #   partial → solid step forward, small cost
    #   fail    → you still stumble forward, BUT the Nightmare surges (extra lucidity
    #             drain + menace) — that's the real, legible risk of a bold bet.
    reward = int(spec["progress_reward"])
    cost = int(spec["lucidity_cost"])
    if result == "fail":
        return Outcome(tier, result, roll, fail_threshold,
                       lucidity_cost=cost + 1,                 # the dream destabilizes
                       progress_reward=max(3, reward // 3),    # still inch forward
                       courage_gain=0,
                       menace_delta=int(spec["menace_delta"]) + 2)  # Nightmare surges
    if result == "partial":
        return Outcome(tier, result, roll, fail_threshold,
                       lucidity_cost=cost,
                       progress_reward=(reward * 2) // 3,
                       courage_gain=0,
                       menace_delta=int(spec["menace_delta"]))
    return Outcome(tier, result, roll, fail_threshold,
                   lucidity_cost=cost,
                   progress_reward=reward,
                   courage_gain=int(spec["courage_gain"]),
                   menace_delta=max(0, int(spec["menace_delta"]) - 1))  # a win eases pressure


def apply(state: WorldState, out: Outcome) -> None:
    """Mutate world-state by an Outcome — the ONLY place gamble math touches state.

    One clean tension: PROGRESS climbs to 100 (wake with the prize) while LUCIDITY
    drains to 0 (lost in the dream). Every gambit advances progress; bolder gambits
    leap further but cost more lucidity, and a fail costs extra. Menace is the
    Nightmare's narrative pressure (drives the Nightmare beat), not a hidden drain —
    so the only way to lose stays legible: run out of lucidity.
    """
    state.lucidity = max(0, state.lucidity - out.lucidity_cost)
    state.progress = min(100, state.progress + out.progress_reward)
    state.courage = min(COURAGE_MAX, state.courage + out.courage_gain)
    state.menace = max(0, state.menace + out.menace_delta)
    state.peak_menace = max(state.peak_menace, state.menace)

    if out.result == "fail":
        state.scars.append(f"a {out.tier} bet gone wrong (turn {state.turn})")

    if state.progress >= 100:
        # Reaching the prize on the same beat that drains you = out just in time.
        state.complete = True
        state.progress = 100
    elif state.lucidity <= 0:
        state.lost = True
