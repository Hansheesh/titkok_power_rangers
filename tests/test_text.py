import unittest

from src.text import extract_budget_max, is_override, terms


class TextTests(unittest.TestCase):
    def test_override_detection(self):
        self.assertTrue(is_override("Actually, ignore my earlier preference. What I need is: leather."))

    def test_budget_extraction(self):
        self.assertEqual(extract_budget_max("I need something under $60"), 60.0)
        self.assertIsNone(extract_budget_max("budget around $60"))

    def test_terms_remove_dialogue_boilerplate(self):
        result = terms("I'm looking for hiking boots, but I'm still exploring.")
        self.assertIn("hiking", result)
        self.assertIn("boots", result)
        self.assertNotIn("looking", result)


if __name__ == "__main__":
    unittest.main()
