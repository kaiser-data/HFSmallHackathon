"""Deep per-world story arcs — the plot the dream evolves through.

Each world has a real arc: a premise with a hidden emotional truth, a richer goal,
a midpoint twist, and five BEATS keyed to PROGRESS bands (0/25/50/75/100). The
engine feeds the *current* beat to the Dreamweaver each turn, so narration (and the
images derived from it) follow a genuine rising-action → twist → cost → climax arc
instead of disconnected moments. The through-line: every world's scary surface
hides something tender.

`beat_for(world_id, progress)` returns the active beat; `arc_of(world_id)` the arc.
"""
from __future__ import annotations

ARCS: dict[str, dict] = {
    "candy_desert": {
        "premise": "The hum beneath the sugar isn't a monster — it's a lullaby, sung by "
        "something enormous and asleep that the gummy bear's village agreed, generations ago, "
        "to keep dreaming. What's secretly at stake: let a sad, vast thing keep sleeping safe, "
        "or wake it because it has been crying in its sleep all along.",
        "goal": "Reach the buried heart of the desert and decide whether to finish the lullaby "
        "or answer the crying with a single true word.",
        "twist": "The hum is not humming AT you — it is something underground sobbing in its "
        "sleep, and the gummy bear has been muffling it, not guarding against it, out of fear.",
        "beats": {
            0: "You wake on warm sugar-glass under two moons; the hum rises through your feet like a heartbeat, and a nervous gummy bear begs you, too quickly, please not to dig.",
            25: "Every step toward the sound makes the sugar go translucent, showing a shape vast and curled far below; the bear admits the villagers pour songs into the dunes to keep it under.",
            50: "Pressing closer, the hum breaks into words — it is weeping, not warning; the bear confesses it spent its life silencing a grieving thing it was too frightened to comfort.",
            75: "To reach the sleeper you must walk onto sugar so thin it won't hold a coward, trading the easy retreat for the chance to actually answer the cry below.",
            100: "At the buried heart you speak to the sleeper instead of burying it; the weeping settles into a true lullaby you sing together, the desert blooms into soft light, and the gummy bear weeps with a hundred years of relief.",
        },
        "hobbes_note": "Hobbes, who hates loud unknown noises, learns the scariest sound was something lonely asking for company — and he's the one who first tugs you toward it.",
    },
    "sunken_city": {
        "premise": "The bells strain because the city drowned mid-song, and the one note that "
        "completes its final hymn was the voice of the bellringer's drowned love — a note he "
        "alone remembers and has refused to ring for a century. The city is frozen in an "
        "unfinished goodbye, and you are the breath that can finally finish the song.",
        "goal": "Carry the lost final note up through the leaning towers and ring it true, so "
        "the city can complete the hymn it drowned singing.",
        "twist": "The song isn't lost — the old eel has known it all along; he stopped being "
        "the bellringer because the last note is the name of someone he couldn't bear to say.",
        "beats": {
            0: "You sink into blue water you can breathe; drowned bell-towers lean toward you straining to ring, and a tired old eel coils on the cathedral steps, pretending he's forgotten why.",
            25: "The bells only answer a true voice; every false or fearful note makes the water colder and the towers lean further, as if losing hope.",
            50: "The eel tells the truth: he was the bellringer, the missing note is a name, and he silenced the whole city rather than say a goodbye he wasn't ready for.",
            75: "To ring the true note you must let the eel pass his grief and his memory of her through you — carrying a sorrow that isn't yours, swimming up while it weighs you down.",
            100: "At the highest tower you ring the lost note and it is her name; the hymn completes, the hundred-year goodbye is spoken, and the eel, lighter, rings the closing peal himself as the water fills with light.",
        },
        "hobbes_note": "Hobbes fears going under and being forgotten in the dark — so finishing a song that refuses to forget anyone is the bravery he needs.",
    },
    "noir_alley": {
        "premise": "Nobody stole the moon — the city gave it away, trading its one honest light "
        "for endless dazzling signs, and the cat informant brokered the deal and has lived "
        "guilty in its glow since. The case isn't a heist; it's a debt to confess.",
        "goal": "Trace the moon's pawn-ticket back to the one who signed it away and buy the "
        "moon back with something truer than money.",
        "twist": "There was no thief — the city pawned its own moon for the neon, and your "
        "riddling cat informant is the broker who wrote the ticket and regrets it every dim night.",
        "beats": {
            0: "You're under a flickering OPEN sign in a moonless drizzle when a trench-coated cat slides up, talking in riddles and prices, happy to sell every lead but the true one.",
            25: "Every clue costs something real, and the neon lies on purpose; follow the bright signs and they loop you back, because the city profits from the dark.",
            50: "The trail dead-ends at a pawnshop ledger in the cat's own paw-writing: the moon wasn't taken, it was sold, and the informant brokered the city's worst bargain.",
            75: "To redeem the ticket you can't pay in coin — you must offer something the neon can't fake, a true and unprofitable thing of your own, and let the dazzling signs go dark.",
            100: "You buy the moon back with that honest price; the lying signs gutter out one by one, real moonlight floods the wet street silver, and the cat — no riddle, no fee — simply thanks you.",
        },
        "hobbes_note": "Hobbes can't tell brave from reckless under all that flashy neon — so a world that rewards one plain honest light over a thousand dazzling lies teaches him which courage is real.",
    },
    "red_planet": {
        "premise": "The tall thing on the dunes isn't hunting you — it's the last of its kind, "
        "alone so long its hunger is loneliness wearing a frightening shape. The polite hungry "
        "zorch insists it just wants to talk because that is, heartbreakingly, the literal truth.",
        "goal": "Get the tin rocket flying again — and choose, before liftoff, whether to leave "
        "the tall watcher alone forever or give it the one conversation it's waited an age for.",
        "twist": "The tall thing isn't coming to eat you; it's the planet's last lonely soul, and "
        "'hungry' was only ever its word for a hunger to be spoken to.",
        "beats": {
            0: "Your tin rocket ticks as it cools on ochre dunes; a tall silhouette watches from the horizon, and a polite, hungry zorch sidles up insisting, sincerely, it only wants to talk.",
            25: "Every part you scavenge to fix the rocket draws the tall thing closer, and the faster you rush to flee, the more desperate its approach becomes.",
            50: "The tall thing isn't pursuing prey: it's the last living soul on a dead world, and its terrible hunger is the ache of an age with no one to talk to.",
            75: "The rocket's almost ready, but its final missing part is in the tall thing's own hands — to leave you must walk toward the very thing you've been fleeing, and risk staying to listen.",
            100: "You meet the watcher, and the conversation it waited an age for finally happens; whether you take it skyward or let it go in peace, the rust wind softens and liftoff feels like a promise kept, not an escape.",
        },
        "hobbes_note": "Hobbes grew brave by surviving things that wanted to eat him — here he must unlearn that flinch and find the harder courage of walking toward a scary thing to keep it company.",
    },
    "token_wood": {
        "premise": "The wood is a sentence the world has tried to finish for a thousand years and "
        "can't, because the little fox made of footnotes keeps annotating every word so it never "
        "has to commit to an ending — terrified that when the thought finishes, it (a footnote to "
        "that thought) finishes too.",
        "goal": "Reach the clearing and place the single last word that lets the thousand-year "
        "sentence finally mean something — and end.",
        "twist": "The wood can't finish its thought because the fox keeps editing it out of fear: "
        "the sentence's ending is also the fox's own — to complete the thought is to let it go.",
        "beats": {
            0: "You step into the wood's whispering edge where every leaf is a word; a small fox made of footnotes trots up narrating its own arrival, eager to guide and quick to qualify.",
            25: "Step on the wrong word and the sentence rewrites around you, paths and meanings shifting — and you notice the fox keeps 'helpfully' revising the trail so it never quite arrives.",
            50: "You see it plainly: the wood isn't lost, it's being stalled — the fox edits every near-ending away because an ending would unwrite it too.",
            75: "To finish the sentence you must convince the fox to let itself be concluded, and choose the final word yourself — committing to one true meaning even though the wood will fall silent.",
            100: "In the clearing you place the last word; the thousand-year thought completes and means something at last, the restless leaves settle, and the fox — unafraid now — reads the finished line aloud and gracefully becomes its quiet final period.",
        },
        "hobbes_note": "Hobbes, always braced for the next risky turn, learns the gentlest courage: that letting a good thing end on purpose is braver than clinging on, qualifier after qualifier, forever.",
    },
}


def arc_of(world_id: str) -> dict | None:
    return ARCS.get(world_id)


def beat_for(world_id: str, progress: int) -> str:
    """The active story beat for the current progress %, so narration follows the arc."""
    arc = ARCS.get(world_id)
    if not arc:
        return ""
    beats = arc["beats"]
    # pick the highest threshold <= progress (0,25,50,75,100)
    key = max((t for t in beats if t <= progress), default=0)
    return beats[key]
