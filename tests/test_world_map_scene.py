import unittest

import pygame
import settings
from src.core.game_state import GameState
from src.scenes.world_map_scene import WorldMapScene


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None
        self.world_map_return_scene = None
        self.returned_from_world_map = False

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id
        self.world_map_return_scene = None

    def has_world_map_return_scene(self):
        return self.world_map_return_scene is not None

    def return_from_world_map(self):
        self.returned_from_world_map = True
        self.world_map_return_scene = None


class FakeInputManager:
    def __init__(self, pressed_action=None):
        self.pressed_action = pressed_action

    def was_pressed(self, action):
        return action == self.pressed_action


class FakeStartAssaultInputManager:
    def was_pressed(self, action):
        return action == settings.START_ASSAULT


class FakeMouseInputManager:
    def __init__(self, mouse_position, mouse_pressed=True):
        self.mouse_position = mouse_position
        self.mouse_pressed = mouse_pressed

    def was_pressed(self, action):
        return False

    def was_mouse_pressed(self, button=1):
        return button == 1 and self.mouse_pressed


class TestWorldMapScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def create_scene(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        scene = WorldMapScene(game_state)
        scene.manager = FakeSceneManager()
        return scene

    def test_world_map_scene_selects_current_region(self):
        scene = self.create_scene()

        self.assertEqual(scene.get_selected_region().id, scene.game_state.current_region_id)

    def test_move_right_selects_next_region(self):
        scene = self.create_scene()

        scene.update(0.1, FakeInputManager(settings.MOVE_RIGHT))

        self.assertEqual(scene.get_selected_region().id, "old_ruins")

    def test_move_left_selects_previous_region(self):
        scene = self.create_scene()

        scene.update(0.1, FakeInputManager(settings.MOVE_LEFT))

        self.assertEqual(scene.get_selected_region().id, "capital_fortress")

    def test_select_unlocked_region_changes_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(scene.game_state.current_region_id, "old_ruins")
        self.assertEqual(scene.manager.requested_scene_id, settings.REGION_SCENE)

    def test_click_unselected_region_selects_it(self):
        scene = self.create_scene()
        mouse_position = scene.region_positions["old_ruins"]

        scene.update(0.1, FakeMouseInputManager(mouse_position))

        self.assertEqual(scene.get_selected_region().id, "old_ruins")
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_click_selected_unlocked_region_enters_region(self):
        scene = self.create_scene()
        mouse_position = scene.region_positions[scene.get_selected_region().id]

        scene.update(0.1, FakeMouseInputManager(mouse_position))

        self.assertEqual(scene.manager.requested_scene_id, settings.REGION_SCENE)

    def test_select_locked_region_does_not_change_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("mountain_mines")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(scene.game_state.current_region_id, "border_forest")
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_start_assault_on_unlocked_region_requests_castle_assault_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("old_ruins")
        region = scene.game_state.get_region("old_ruins")
        region.assault_unlocked = True

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.CASTLE_ASSAULT_SCENE)

    def test_start_assault_sets_current_region(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("old_ruins")
        region = scene.game_state.get_region("old_ruins")
        region.assault_unlocked = True

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertEqual(scene.game_state.current_region_id, "old_ruins")

    def test_start_assault_clears_world_map_return_scene(self):
        scene = self.create_scene()
        scene.manager.world_map_return_scene = object()
        scene.selected_index = scene.region_ids.index("old_ruins")
        region = scene.game_state.get_region("old_ruins")
        region.assault_unlocked = True

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertIsNone(scene.manager.world_map_return_scene)

    def test_enter_region_clears_world_map_return_scene(self):
        scene = self.create_scene()
        scene.manager.world_map_return_scene = object()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertIsNone(scene.manager.world_map_return_scene)

    def test_start_assault_locked_by_influence_does_not_change_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertEqual(scene.game_state.current_region_id, "border_forest")
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_start_assault_on_locked_region_does_not_change_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("mountain_mines")
        region = scene.game_state.get_region("mountain_mines")
        region.assault_unlocked = True

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertEqual(scene.game_state.current_region_id, "border_forest")
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_draw_does_not_crash(self):
        scene = self.create_scene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)

    def test_world_map_scene_status_text_shows_influence(self):
        scene = self.create_scene()
        region = scene.game_state.get_region("old_ruins")
        region.player_influence = 25
        region.enemy_influence = 75

        status = scene.get_region_status_text(region)

        self.assertIn("player 25", status)
        self.assertIn("enemy 75", status)

    def test_world_map_scene_status_text_shows_assault_unlocked(self):
        scene = self.create_scene()
        region = scene.game_state.get_region("old_ruins")
        region.assault_unlocked = True

        status = scene.get_region_status_text(region)

        self.assertIn("assault unlocked", status)

    def test_world_map_scene_draw_after_influence_change_does_not_crash(self):
        scene = self.create_scene()
        region = scene.game_state.get_region("old_ruins")
        region.player_influence = 25
        region.enemy_influence = 75
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)

    def test_draw_hint_with_assault_unlocked_does_not_crash(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("old_ruins")
        region = scene.game_state.get_region("old_ruins")
        region.assault_unlocked = True
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw_hint(surface)

    def test_back_from_world_map_returns_to_gameplay_with_escape(self):
        scene = self.create_scene()
        scene.manager.world_map_return_scene = object()

        scene.update(0.1, FakeInputManager(settings.PAUSE))

        self.assertTrue(scene.manager.returned_from_world_map)

    def test_back_from_world_map_returns_to_gameplay_with_map_key(self):
        scene = self.create_scene()
        scene.manager.world_map_return_scene = object()

        scene.update(0.1, FakeInputManager(settings.OPEN_WORLD_MAP))

        self.assertTrue(scene.manager.returned_from_world_map)

    def test_liberated_region_is_drawn_as_player_controlled(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.mark_liberated("old_ruins")
        scene = WorldMapScene(game_state)
        region = game_state.get_region("old_ruins")

        self.assertEqual(scene.get_region_color(region), scene.PLAYER_COLOR)

    def test_liberated_region_status_text_shows_player_control(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.mark_liberated("old_ruins")
        scene = WorldMapScene(game_state)
        region = game_state.get_region("old_ruins")

        status = scene.get_region_status_text(region)

        self.assertIn("Control: player", status)
        self.assertIn("player 100", status)
        self.assertIn("enemy 0", status)

    def test_region_unlocked_after_liberation_is_drawn_as_enemy(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.mark_liberated("old_ruins")
        scene = WorldMapScene(game_state)
        region = game_state.get_region("mountain_mines")

        self.assertTrue(region.unlocked)
        self.assertEqual(scene.get_region_color(region), scene.ENEMY_COLOR)

    def test_region_unlocked_after_liberation_can_be_selected(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.mark_liberated("old_ruins")
        scene = WorldMapScene(game_state)
        scene.manager = FakeSceneManager()
        scene.selected_index = scene.region_ids.index("mountain_mines")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(game_state.current_region_id, "mountain_mines")
        self.assertEqual(scene.manager.requested_scene_id, settings.REGION_SCENE)

    def test_locked_region_still_does_not_open_after_partial_progression(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.mark_liberated("old_ruins")
        scene = WorldMapScene(game_state)
        scene.manager = FakeSceneManager()
        scene.selected_index = scene.region_ids.index("swamp_lands")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertNotEqual(game_state.current_region_id, "swamp_lands")
        self.assertIsNone(scene.manager.requested_scene_id)


if __name__ == "__main__":
    unittest.main()
