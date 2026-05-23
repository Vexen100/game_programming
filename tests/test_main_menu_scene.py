import unittest

import pygame
import settings
from src.scenes.main_menu_scene import MainMenuScene


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


class TestMainMenuScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_main_menu_scene_creates(self):
        scene = MainMenuScene()

        self.assertEqual(scene.items[0], ("Start Game", "start"))
        self.assertEqual(scene.selected_index, 0)

    def test_move_down_changes_selected_item(self):
        scene = MainMenuScene()

        scene.update(0.1, FakeInputManager(settings.MOVE_DOWN))

        self.assertEqual(scene.selected_index, 1)

    def test_move_up_changes_selected_item(self):
        scene = MainMenuScene()

        scene.update(0.1, FakeInputManager(settings.MOVE_UP))

        self.assertEqual(scene.selected_index, len(scene.items) - 1)

    def test_select_start_game_requests_world_map_scene(self):
        scene = MainMenuScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_select_continue_does_not_request_scene(self):
        scene = MainMenuScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 1

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertIsNone(scene.manager.requested_scene_id)

    def test_select_settings_does_not_request_scene(self):
        scene = MainMenuScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 2

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertIsNone(scene.manager.requested_scene_id)

    def test_start_game_without_manager_does_not_crash(self):
        scene = MainMenuScene()

        scene.update(0.1, FakeInputManager(settings.SELECT))

    def test_draw_does_not_crash(self):
        scene = MainMenuScene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)


if __name__ == "__main__":
    unittest.main()
