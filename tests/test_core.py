import unittest

from agents.base import loose_json
from agents.dream import DreamEngine
from agents.resolver import Outcome, apply, resolve
from agents.world import WorldState


class LooseJsonTests(unittest.TestCase):
    def test_extracts_fenced_json_with_trailing_text(self):
        text = '```json\n{"reaction":"steady","choices":["go","run","leap"]}\n```\nDone.'
        self.assertEqual(loose_json(text)["reaction"], "steady")

    def test_uses_first_valid_object_not_greedy_span(self):
        text = 'bad {not json} then {"ok": true} and {"later": false}'
        self.assertEqual(loose_json(text), {"ok": True})

    def test_ignores_braces_inside_strings(self):
        text = 'prefix {"note":"the door says {open}","n":2} suffix'
        self.assertEqual(loose_json(text)["note"], "the door says {open}")


class ResolverTests(unittest.TestCase):
    def test_resolve_is_deterministic_by_seed_turn(self):
        self.assertEqual(resolve("bold", "abc123", 4), resolve("bold", "abc123", 4))
        self.assertNotEqual(resolve("bold", "abc123", 4).roll, resolve("bold", "abc123", 5).roll)

    def test_completion_wins_when_lucidity_reaches_zero_same_turn(self):
        state = WorldState("token_wood", "Thousand Token Wood", "x", "edge", "mission", "fox")
        state.progress = 90
        state.lucidity = 1
        out = Outcome("safe", "success", 99, 5, lucidity_cost=1,
                      progress_reward=10, courage_gain=0, menace_delta=0)
        apply(state, out)
        self.assertTrue(state.complete)
        self.assertFalse(state.lost)


class DreamEngineTests(unittest.TestCase):
    def test_keeper_bad_patch_does_not_break_update(self):
        class BadKeeper:
            def json(self, *_args, **_kwargs):
                return ["not", "a", "patch"]

        engine = DreamEngine()
        engine.start("token_wood", "seed")
        engine.keeper = BadKeeper()
        before = engine.state.location

        engine._update(engine._ctx(), "step", "scene")

        self.assertEqual(engine.state.location, before)

    def test_gambits_keep_code_owned_tiers_with_partial_labels(self):
        engine = DreamEngine()
        self.assertEqual(
            engine._make_gambits(["Tiptoe"]),
            [
                ("Tiptoe", "safe"),
                ("Take a real risk", "bold"),
                ("Do the reckless thing", "reckless"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
