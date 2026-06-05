import json
import tempfile
import unittest
from pathlib import Path

import settings
from src.core.game_state import GameState
from src.core.save_manager import SaveManager


class TestSaveManager(unittest.TestCase):
    def create_save_path(self, directory):
        return Path(directory) / "nested" / "save_1.json"

    def write_save_data(self, save_path, data):
        save_path.parent.mkdir(parents=True)
        save_path.write_text(json.dumps(data), encoding="utf-8")

    def test_has_save_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            save_manager = SaveManager(self.create_save_path(directory))

            self.assertFalse(save_manager.has_save())

    def test_save_creates_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

            save_manager.save(game_state)

            self.assertTrue(save_path.parent.is_dir())

    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

            save_manager.save(game_state)

            self.assertTrue(save_path.is_file())

    def test_load_returns_none_when_file_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            save_manager = SaveManager(self.create_save_path(directory))

            self.assertIsNone(save_manager.load())

    def test_load_restores_game_state(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
            game_state.set_current_region("old_ruins")
            game_state.mark_assault_unlocked("old_ruins")

            save_manager.save(game_state)
            save_data = save_manager.load()

            self.assertEqual(save_data.game_state.current_region_id, "old_ruins")
            self.assertTrue(save_data.game_state.get_region("old_ruins").assault_unlocked)

    def test_load_restores_region_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            save_manager = SaveManager(self.create_save_path(directory))
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
            region_runtime = {
                "old_ruins": {
                    "defeated_enemy_indexes": [0, 2],
                    "outpost_cleared": True,
                }
            }

            save_manager.save(game_state, region_runtime=region_runtime)
            save_data = save_manager.load()

            self.assertEqual(save_data.region_runtime, region_runtime)

    def test_delete_save_removes_file(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
            save_manager.save(game_state)

            save_manager.delete_save()

            self.assertFalse(save_path.exists())

    def test_load_invalid_json_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_path.parent.mkdir(parents=True)
            save_path.write_text("{broken", encoding="utf-8")
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_unsupported_version_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_path.parent.mkdir(parents=True)
            save_path.write_text(
                '{"version": 999, "game_state": {"regions": []}}',
                encoding="utf-8",
            )
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_top_level_list_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            self.write_save_data(save_path, [])
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_missing_game_state_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            self.write_save_data(save_path, {"version": SaveManager.SAVE_VERSION})
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_game_state_without_regions_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            self.write_save_data(
                save_path,
                {
                    "version": SaveManager.SAVE_VERSION,
                    "game_state": {},
                },
            )
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_region_runtime_must_be_dict(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            self.write_save_data(
                save_path,
                {
                    "version": SaveManager.SAVE_VERSION,
                    "game_state": {"regions": []},
                    "region_runtime": [],
                },
            )
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_load_malformed_region_data_raises_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            self.write_save_data(
                save_path,
                {
                    "version": SaveManager.SAVE_VERSION,
                    "game_state": {
                        "regions": [
                            {"id": "broken"},
                        ],
                    },
                    "region_runtime": {},
                },
            )
            save_manager = SaveManager(save_path)

            with self.assertRaises(ValueError):
                save_manager.load()

    def test_save_writes_utf8_without_ascii_escaping(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = self.create_save_path(directory)
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
            game_state.get_region("old_ruins").name = "Старые руины"

            save_manager.save(game_state)
            save_text = save_path.read_text(encoding="utf-8")

            self.assertIn("Старые руины", save_text)


if __name__ == "__main__":
    unittest.main()
