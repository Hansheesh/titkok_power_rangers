from pathlib import Path
import unittest

from src.agent import Agent


FIXTURE = Path(__file__).parent / "fixtures" / "catalog.jsonl"


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = Agent(FIXTURE)
        self.profile = {
            "preference_tags": ["outdoor", "hiking"],
            "summary": "Often prefers practical outdoor products.",
        }

    def test_required_output_shape(self):
        self.agent.reset("s1", self.profile)
        response = self.agent.respond(
            "s1",
            "I'm looking for Women Shoes Hiking Boots. "
            "A key requirement is: waterproof upper.",
            1,
            10,
        )
        self.assertIsInstance(response["message"], str)
        self.assertLessEqual(len(response["recommendations"]), 10)
        self.assertIn("usage", response)

    def test_specific_constraint_ranks_target_first(self):
        self.agent.reset("s2", self.profile)
        response = self.agent.respond(
            "s2",
            "I'm looking for Women Shoes Hiking Boots. "
            "A key requirement is: waterproof upper.",
            1,
            10,
        )
        self.assertEqual(response["recommendations"][0]["parent_asin"], "BLUE_BOOT")

    def test_override_changes_active_ranking(self):
        self.agent.reset("s3", self.profile)
        first = self.agent.respond(
            "s3",
            "I'm looking for Women Shoes. red color",
            1,
            10,
        )
        self.assertEqual(first["recommendations"][0]["parent_asin"], "RED_SHOE")

        second = self.agent.respond(
            "s3",
            "Actually, ignore my earlier preference. "
            "What I need is: waterproof upper.",
            2,
            10,
        )
        self.assertEqual(second["recommendations"][0]["parent_asin"], "BLUE_BOOT")

    def test_never_asks_after_turn_10(self):
        self.agent.reset("s4", self.profile)
        response = self.agent.respond(
            "s4",
            "I'm looking for hiking boots, but I'm still exploring.",
            10,
            10,
        )
        self.assertIsNone(response["ask_attribute"])


if __name__ == "__main__":
    unittest.main()
