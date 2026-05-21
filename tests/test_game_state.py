import unittest

import settings
from src.core.game_state import GameState
from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL


class TestGameState(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

    def test_load_from_file_loads_five_regions(self):
        self.assertEqual(len(self.game_state.regions), 5)

    def test_start_region_exists_unlocked_and_liberated(self):
        region = self.game_state.get_region("border_forest")

        self.assertIsNotNone(region)
        self.assertTrue(region.unlocked)
        self.assertTrue(region.liberated)
        self.assertEqual(region.control_state, PLAYER_CONTROL)

    def test_current_region_is_first_unlocked_region_after_loading(self):
        self.assertEqual(self.game_state.current_region_id, "border_forest")

    def test_get_region_returns_none_for_unknown_id(self):
        self.assertIsNone(self.game_state.get_region("missing"))

    def test_set_current_region_works_for_unlocked_region(self):
        self.game_state.set_current_region("old_ruins")

        self.assertEqual(self.game_state.current_region_id, "old_ruins")

    def test_set_current_region_raises_for_locked_region(self):
        with self.assertRaises(ValueError):
            self.game_state.set_current_region("mountain_mines")

    def test_unlock_region_opens_locked_region_and_changes_control_to_enemy(self):
        region = self.game_state.get_region("mountain_mines")
        self.assertFalse(region.unlocked)
        self.assertEqual(region.control_state, LOCKED_CONTROL)

        self.game_state.unlock_region("mountain_mines")

        self.assertTrue(region.unlocked)
        self.assertEqual(region.control_state, ENEMY_CONTROL)

    def test_change_influence_clamps_values(self):
        self.game_state.change_influence("old_ruins", delta_player=150, delta_enemy=-150)
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 100)
        self.assertEqual(region.enemy_influence, 0)

    def test_mark_assault_unlocked(self):
        self.game_state.mark_assault_unlocked("old_ruins")
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.assault_unlocked)

    def test_mark_liberated_sets_player_control(self):
        self.game_state.mark_assault_unlocked("old_ruins")
        self.game_state.mark_liberated("old_ruins")
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.liberated)
        self.assertTrue(region.unlocked)
        self.assertEqual(region.control_state, PLAYER_CONTROL)
        self.assertEqual(region.player_influence, 100)
        self.assertEqual(region.enemy_influence, 0)
        self.assertFalse(region.assault_unlocked)

    def test_get_unlocked_regions_returns_only_unlocked_regions(self):
        unlocked_regions = self.game_state.get_unlocked_regions()
        region_ids = [region.id for region in unlocked_regions]

        self.assertEqual(region_ids, ["border_forest", "old_ruins"])

    def test_methods_raise_for_unknown_region(self):
        methods = [
            lambda: self.game_state.set_current_region("missing"),
            lambda: self.game_state.unlock_region("missing"),
            lambda: self.game_state.change_influence("missing", delta_player=10),
            lambda: self.game_state.mark_assault_unlocked("missing"),
            lambda: self.game_state.mark_liberated("missing"),
        ]

        for method in methods:
            with self.assertRaises(ValueError):
                method()


if __name__ == "__main__":
    unittest.main()
