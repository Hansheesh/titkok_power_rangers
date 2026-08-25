import unittest

from src.state import SessionState


class StateTests(unittest.TestCase):
    def test_override_discards_stale_free_text_but_keeps_category(self):
        state = SessionState("s1", {})
        state.update("I'm looking for Women's Shoes. I prefer red.")
        state.update("For that, what matters is: lightweight.")
        state.update(
            "Actually, ignore my earlier preference. What I need is: waterproof upper."
        )

        query = state.query_text().lower()
        self.assertIn("women's shoes", query)
        self.assertIn("waterproof", query)
        self.assertNotIn("lightweight", query)

    def test_override_can_be_disabled_for_ablation(self):
        state = SessionState("s1", {})
        state.update("I'm looking for Women's Shoes. red color")
        state.update(
            "Actually, ignore my earlier preference. What I need is: waterproof upper.",
            enable_override_reset=False,
        )
        query = state.query_text().lower()
        self.assertIn("red", query)
        self.assertIn("waterproof", query)

    def test_no_preference_marks_last_question_unavailable(self):
        state = SessionState("s1", {})
        state.record_question("material")
        state.update("I don't have an additional preference for material.")
        self.assertIn("material", state.unavailable_attributes)


if __name__ == "__main__":
    unittest.main()
