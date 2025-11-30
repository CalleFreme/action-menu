import unittest

from journal_ai import extract_suggestions


class JournalAISuggestionsTests(unittest.TestCase):
    def test_extract_suggestions_classifies_sentences(self) -> None:
        text = (
            "I want to become the best CTO. Today I will ship the new API. "
            "Every day after standup I should review the team habits."
        )
        suggestions = extract_suggestions(text)
        kinds = [item.kind for item in suggestions]
        sentences = [item.text for item in suggestions]

        self.assertEqual(kinds, ["goal", "action", "habit"])
        self.assertIn("ship the new API", sentences[1])

    def test_extract_suggestions_handles_no_matches(self) -> None:
        text = "Just writing for fun without any trigger words."
        suggestions = extract_suggestions(text)
        self.assertEqual(suggestions, [])

    def test_expanded_keyword_set_finds_additional_matches(self) -> None:
        text = (
            "Plan to publish my own game engine soon. "
            "My nightly ritual is to stretch and review code. "
            "Schedule the art sync email this week. "
            "Feeling overwhelmed with the backlog."
        )
        suggestions = extract_suggestions(text)
        kinds = [item.kind for item in suggestions]
        self.assertEqual(kinds, ["goal", "habit", "action", "blockage"])


if __name__ == "__main__":
    unittest.main()
