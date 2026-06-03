import unittest
from unittest.mock import patch

import pygame
import settings
from src.components.components import NPC, Outpost
from src.core.event_bus import EventBus
from src.core.game import Game
from src.core.game_state import GameState
from src.core.scene_manager import SceneManager
from src.scenes.world_map_scene import WorldMapScene


class TestGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def create_game_shell(self):
        game = object.__new__(Game)
        game.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game.event_bus = EventBus()
        game.region_scene_cache = {}
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


if __name__ == "__main__":
    unittest.main()
