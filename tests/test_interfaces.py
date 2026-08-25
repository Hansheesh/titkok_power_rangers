import unittest

from src.interfaces import Candidate, IntentResult, Retriever, Reranker, SessionState


class InterfaceTests(unittest.TestCase):
    def test_shared_types_construct(self):
        candidate = Candidate("A", 1.0)
        intent = IntentResult("buying", 0.9, ("test",))
        state = SessionState("s", {})
        self.assertEqual(candidate.parent_asin, "A")
        self.assertEqual(intent.name, "buying")
        self.assertEqual(state.session_id, "s")


if __name__ == "__main__":
    unittest.main()
