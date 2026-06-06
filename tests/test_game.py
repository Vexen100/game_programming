import unittest
from unittest.mock import patch

import pygame
import settings
from src.components.components import NPC, Outpost
from src.core.event_bus import EventBus
from src.core.game import Game
from src.core.game_state import GameState
from src.core.save_manager import SaveData
from src.core.scene_manager import SceneManager
from src.events.game_events import OutpostClearedEvent, RegionLiberatedEvent
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.scenes.world_map_scene import WorldMapScene


class FakeSaveManager:
    def __init__(self, save_data=None, load_error=None):
        self.save_data = save_data
        self.load_error = load_error
        self.delete_save_called = False
        self.save_called = False
        self.load_called = False
        self.saved_game_state = None
        self.saved_region_runtime = None

    def has_save(self):
        return self.save_data is not None

    def save(self, game_state, region_runtime=None):
        self.save_called = True
        self.saved_game_state = GameState.from_dict(game_state.to_dict())
        self.saved_region_runtime = region_runtime or {}

    def load(self):
        self.load_called = True
        if self.load_error is not None:
            raise self.load_error
        return self.save_data

    def delete_save(self):
        self.delete_save_called = True


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id


class TestGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def create_game_shell(self):
        game = object.__new__(Game)
        game.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game.event_bus = EventBus()
        game.save_manager = FakeSaveManager()
        game.region_scene_cache = {}
        game.region_runtime_snapshots = {}
        game.scene_manager = FakeSceneManager()
        return game

    def reenter_current_region_through_world_map(self, game, region_scene):
        manager = SceneManager()
        manager.register_scenes({
            settings.WORLD_MAP_SCENE: lambda: WorldMapScene(game.game_state),
            settings.REGION_SCENE: game.get_region_scene,
        })
        manager.current_scene = region_scene
        region_scene.manager = manager

        region_scene.request_world_map()
        manager.process_scene_change()
        world_map_scene = manager.current_scene
        world_map_scene.enter_selected_region()
        manager.process_scene_change()

        return manager.current_scene

    def test_toggle_fullscreen_switches_display_mode(self):
        game = object.__new__(Game)
        game.fullscreen = False
        game.screen = None

        with patch("pygame.display.set_mode") as mock_set_mode:
            mock_set_mode.return_value = "screen"
            game.toggle_fullscreen()

        self.assertTrue(game.fullscreen)
        self.assertEqual(game.screen, "screen")
        mock_set_mode.assert_called_once_with(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            pygame.FULLSCREEN,
        )

    def test_get_region_scene_returns_same_object_for_same_region_id(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")

        first_scene = game.get_region_scene()
        second_scene = game.get_region_scene()

        self.assertIs(second_scene, first_scene)

    def test_get_region_scene_creates_different_object_for_different_region_id(self):
        game = self.create_game_shell()

        game.game_state.set_current_region("border_forest")
        border_scene = game.get_region_scene()
        game.game_state.set_current_region("old_ruins")
        old_ruins_scene = game.get_region_scene()

        self.assertIsNot(old_ruins_scene, border_scene)

    def test_build_scene_registry_creates_castle_assault_scene_with_layout(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")

        scene_registry = game.build_scene_registry()
        scene = scene_registry[settings.CASTLE_ASSAULT_SCENE]()

        self.assertIsInstance(scene, CastleAssaultScene)
        self.assertIs(scene.game_state, game.game_state)
        self.assertIs(scene.event_bus, game.event_bus)
        self.assertIsNotNone(scene.castle_layout)
        scene.validate_castle_layout()

    def test_world_map_reenter_same_region_uses_cached_region_scene(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        region_scene = game.get_region_scene()

        returned_scene = self.reenter_current_region_through_world_map(game, region_scene)

        self.assertIs(returned_scene, region_scene)

    def test_cached_region_scene_preserves_cleared_outpost_after_reenter(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        region_scene = game.get_region_scene()
        outpost = region_scene.ecm.get_component(region_scene.outpost_id, Outpost)
        outpost.cleared = True

        returned_scene = self.reenter_current_region_through_world_map(game, region_scene)
        returned_outpost = returned_scene.ecm.get_component(returned_scene.outpost_id, Outpost)

        self.assertTrue(returned_outpost.cleared)

    def test_cached_region_scene_does_not_restore_removed_enemy_after_reenter(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        region_scene = game.get_region_scene()
        removed_enemy_id = region_scene.enemy_id
        region_scene.ecm.destroy_entity(removed_enemy_id)

        returned_scene = self.reenter_current_region_through_world_map(game, region_scene)

        self.assertIs(returned_scene, region_scene)
        self.assertNotIn(removed_enemy_id, returned_scene.ecm.alive_entities)

    def test_cached_region_scene_preserves_completed_npc_after_reenter(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        region_scene = game.get_region_scene()
        npc = region_scene.ecm.get_component(region_scene.npc_id, NPC)
        npc.quest_completed = True

        returned_scene = self.reenter_current_region_through_world_map(game, region_scene)
        returned_npc = returned_scene.ecm.get_component(returned_scene.npc_id, NPC)

        self.assertTrue(returned_npc.quest_completed)

    def test_start_new_game_deletes_existing_save_before_reset(self):
        game = self.create_game_shell()

        game.start_new_game()

        self.assertTrue(game.save_manager.delete_save_called)

    def test_start_new_game_resets_cache_and_runtime_snapshots(self):
        game = self.create_game_shell()
        game.region_scene_cache["old_ruins"] = object()
        game.region_runtime_snapshots["old_ruins"] = {"outpost_cleared": True}

        game.start_new_game()

        self.assertEqual(game.region_scene_cache, {})
        self.assertEqual(game.region_runtime_snapshots, {})

    def test_start_new_game_saves_clean_state_after_reset(self):
        game = self.create_game_shell()
        game.game_state.mark_liberated("old_ruins")

        game.start_new_game()
        saved_old_ruins = game.save_manager.saved_game_state.get_region("old_ruins")
        saved_mountain_mines = game.save_manager.saved_game_state.get_region("mountain_mines")

        self.assertTrue(game.save_manager.save_called)
        self.assertFalse(saved_old_ruins.liberated)
        self.assertFalse(saved_mountain_mines.unlocked)
        self.assertEqual(
            game.save_manager.saved_game_state.current_region_id,
            "border_forest",
        )

    def test_continue_game_loads_save_and_opens_world_map(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        save_data = SaveData(
            game_state=game_state,
            region_runtime={"old_ruins": {"outpost_cleared": True}},
        )
        game = self.create_game_shell()
        game.save_manager = FakeSaveManager(save_data)

        result = game.continue_game()

        self.assertTrue(result)
        self.assertEqual(game.game_state.current_region_id, "old_ruins")
        self.assertEqual(
            game.region_runtime_snapshots,
            {"old_ruins": {"outpost_cleared": True}},
        )
        self.assertEqual(game.scene_manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_continue_game_does_not_start_new_game_when_save_missing(self):
        game = self.create_game_shell()

        result = game.continue_game()

        self.assertFalse(result)
        self.assertTrue(game.save_manager.load_called)
        self.assertFalse(game.save_manager.delete_save_called)
        self.assertFalse(game.save_manager.save_called)
        self.assertIsNone(game.scene_manager.requested_scene_id)

    def test_continue_game_returns_false_when_save_manager_raises_value_error(self):
        game = self.create_game_shell()
        game.save_manager = FakeSaveManager(load_error=ValueError("Broken save"))

        result = game.continue_game()

        self.assertFalse(result)
        self.assertTrue(game.save_manager.load_called)
        self.assertFalse(game.save_manager.delete_save_called)
        self.assertFalse(game.save_manager.save_called)
        self.assertIsNone(game.scene_manager.requested_scene_id)

    def test_get_region_scene_applies_runtime_snapshot_only_on_first_creation(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        game.region_runtime_snapshots = {
            "old_ruins": {
                "outpost_cleared": True,
            }
        }

        scene = game.get_region_scene()
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        self.assertTrue(outpost.cleared)

        outpost.cleared = False
        scene_again = game.get_region_scene()

        self.assertIs(scene_again, scene)
        self.assertFalse(outpost.cleared)

    def test_save_current_progress_collects_cached_region_scene_snapshots(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        scene = game.get_region_scene()
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        outpost.cleared = True

        game.save_current_progress()

        self.assertTrue(game.save_manager.save_called)
        self.assertTrue(
            game.save_manager.saved_region_runtime["old_ruins"]["outpost_cleared"]
        )

    def test_autosave_after_outpost_event_saves_updated_state_and_runtime(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        game.rebuild_world_systems()
        scene = game.get_region_scene()
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        outpost.cleared = True

        game.event_bus.publish(OutpostClearedEvent(scene.outpost_id, "old_ruins"))
        saved_region = game.save_manager.saved_game_state.get_region("old_ruins")

        self.assertTrue(game.save_manager.save_called)
        self.assertEqual(saved_region.player_influence, 35)
        self.assertEqual(saved_region.enemy_influence, 65)
        self.assertFalse(saved_region.assault_unlocked)
        self.assertTrue(
            game.save_manager.saved_region_runtime["old_ruins"]["outpost_cleared"]
        )

    def test_autosave_after_liberation_event_saves_liberated_and_unlocked_next(self):
        game = self.create_game_shell()
        game.game_state.set_current_region("old_ruins")
        game.rebuild_world_systems()

        game.event_bus.publish(RegionLiberatedEvent("old_ruins"))
        saved_old_ruins = game.save_manager.saved_game_state.get_region("old_ruins")
        saved_mountain_mines = game.save_manager.saved_game_state.get_region("mountain_mines")

        self.assertTrue(game.save_manager.save_called)
        self.assertTrue(saved_old_ruins.liberated)
        self.assertTrue(saved_mountain_mines.unlocked)


if __name__ == "__main__":
    unittest.main()
