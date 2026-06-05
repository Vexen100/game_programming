import unittest

import settings
from src.core.game_state import GameState
from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL, RegionState


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

    def test_region_state_from_dict_reads_unlocks_on_liberation(self):
        region = RegionState.from_dict(
            {
                "id": "old_ruins",
                "name": "Old Ruins",
                "unlocked": True,
                "control_state": ENEMY_CONTROL,
                "player_influence": 0,
                "enemy_influence": 100,
                "assault_unlocked": False,
                "liberated": False,
                "unlocks_on_liberation": ["mountain_mines"],
            }
        )

        self.assertEqual(region.unlocks_on_liberation, ["mountain_mines"])

    def test_region_state_from_dict_uses_empty_unlocks_default(self):
        region = RegionState.from_dict(
            {
                "id": "old_ruins",
                "name": "Old Ruins",
                "unlocked": True,
                "control_state": ENEMY_CONTROL,
                "player_influence": 0,
                "enemy_influence": 100,
                "assault_unlocked": False,
                "liberated": False,
            }
        )

        self.assertEqual(region.unlocks_on_liberation, [])

    def test_game_state_to_dict_contains_current_region_and_regions(self):
        self.game_state.set_current_region("old_ruins")

        data = self.game_state.to_dict()

        self.assertEqual(data["current_region_id"], "old_ruins")
        self.assertEqual(len(data["regions"]), 5)

    def test_game_state_from_dict_restores_region_data(self):
        data = {
            "current_region_id": "old_ruins",
            "regions": [
                {
                    "id": "old_ruins",
                    "name": "Old Ruins",
                    "unlocked": True,
                    "control_state": ENEMY_CONTROL,
                    "player_influence": 25,
                    "enemy_influence": 75,
                    "assault_unlocked": True,
                    "liberated": False,
                    "unlocks_on_liberation": ["mountain_mines"],
                }
            ],
        }

        game_state = GameState.from_dict(data)
        region = game_state.get_region("old_ruins")

        self.assertEqual(game_state.current_region_id, "old_ruins")
        self.assertTrue(region.unlocked)
        self.assertEqual(region.control_state, ENEMY_CONTROL)
        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)
        self.assertTrue(region.assault_unlocked)
        self.assertFalse(region.liberated)
        self.assertEqual(region.unlocks_on_liberation, ["mountain_mines"])

    def test_game_state_serialization_roundtrip_preserves_data(self):
        self.game_state.set_current_region("old_ruins")
        self.game_state.mark_assault_unlocked("old_ruins")
        self.game_state.mark_liberated("old_ruins")

        restored_state = GameState.from_dict(self.game_state.to_dict())

        self.assertEqual(restored_state.current_region_id, "old_ruins")
        self.assertTrue(restored_state.get_region("old_ruins").liberated)
        self.assertTrue(restored_state.get_region("mountain_mines").unlocked)

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

    def test_mark_liberated_unlocks_next_region(self):
        self.game_state.mark_liberated("old_ruins")
        region = self.game_state.get_region("mountain_mines")

        self.assertTrue(region.unlocked)

    def test_unlocked_after_liberation_region_becomes_enemy_controlled(self):
        self.game_state.mark_liberated("old_ruins")
        region = self.game_state.get_region("mountain_mines")

        self.assertEqual(region.control_state, ENEMY_CONTROL)

    def test_mark_liberated_mountain_mines_unlocks_swamp_lands(self):
        self.game_state.unlock_region("mountain_mines")
        self.game_state.mark_liberated("mountain_mines")
        region = self.game_state.get_region("swamp_lands")

        self.assertTrue(region.unlocked)
        self.assertEqual(region.control_state, ENEMY_CONTROL)

    def test_mark_liberated_swamp_lands_unlocks_capital_fortress(self):
        self.game_state.unlock_region("swamp_lands")
        self.game_state.mark_liberated("swamp_lands")
        region = self.game_state.get_region("capital_fortress")

        self.assertTrue(region.unlocked)
        self.assertEqual(region.control_state, ENEMY_CONTROL)

    def test_mark_liberated_capital_fortress_does_not_crash(self):
        self.game_state.unlock_region("capital_fortress")

        self.game_state.mark_liberated("capital_fortress")
        region = self.game_state.get_region("capital_fortress")

        self.assertTrue(region.liberated)

    def test_mark_liberated_raises_for_unknown_unlock_region(self):
        region = RegionState(
            id="test_region",
            name="Test Region",
            unlocked=True,
            control_state=ENEMY_CONTROL,
            player_influence=0,
            enemy_influence=100,
            assault_unlocked=False,
            liberated=False,
            unlocks_on_liberation=["missing"],
        )
        game_state = GameState([region])

        with self.assertRaises(ValueError):
            game_state.mark_liberated("test_region")

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
