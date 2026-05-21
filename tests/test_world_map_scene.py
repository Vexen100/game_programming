import unittest

import pygame
import settings
from src.core.game_state import GameState
from src.scenes.world_map_scene import WorldMapScene


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id


class FakeInputManager:
    def __init__(self, pressed_action=None):
        self.pressed_action = pressed_action

    def was_pressed(self, action):
        return action == self.pressed_action


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

    def test_select_locked_region_does_not_change_scene(self):
        scene = self.create_scene()
        scene.selected_index = scene.region_ids.index("mountain_mines")

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(scene.game_state.current_region_id, "border_forest")
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_draw_does_not_crash(self):
        scene = self.create_scene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)


if __name__ == "__main__":
    unittest.main()
