import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from models import AppState, SmartGoal
from storage import StorageManager


class StorageManagerTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            manager = StorageManager(path)

            state = AppState()
            state.goals.append(SmartGoal.new(title="Ship Unreal prototype"))
            state.weekly_actions["Today"].append("Refactor rendering pipeline")
            state.timer_categories.append("Mentorship")

            manager.save(state)

            reloaded = StorageManager(path).load()

            self.assertEqual(len(reloaded.goals), 1)
            self.assertEqual(reloaded.goals[0].title, "Ship Unreal prototype")
            self.assertEqual(reloaded.weekly_actions["Today"], ["Refactor rendering pipeline"])
            self.assertIn("Mentorship", reloaded.timer_categories)

    def test_invalid_json_returns_fresh_state(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("{not: valid}", encoding="utf-8")

            loaded = StorageManager(path).load()

            self.assertIsInstance(loaded, AppState)
            self.assertEqual(len(loaded.goals), 0)
            self.assertGreaterEqual(len(loaded.timer_categories), 1)


if __name__ == "__main__":
    unittest.main()
