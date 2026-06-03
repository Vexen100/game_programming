import unittest

import pygame
import settings
from src.scenes.pause_scene import PauseScene
from src.ui import texts


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None
        self.resumed = False
        self.opened_world_map_from_pause = False

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id

    def resume_scene(self):
        self.resumed = True

    def open_world_map_from_pause(self):
        self.opened_world_map_from_pause = True


class FakeInputManager:
    def __init__(self, pressed_action=None):
        self.pressed_action = pressed_action

    def was_pressed(self, action):
        return action == self.pressed_action


class FakeMouseInputManager:
    def __init__(self, mouse_position):
        self.mouse_position = mouse_position

    def was_pressed(self, action):
        return False

    def was_mouse_pressed(self, button=1):
        return button == 1


class TestPauseScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_pause_scene_creates(self):
        scene = PauseScene()

        self.assertEqual(scene.items[0], (texts.RESUME, "resume"))
        self.assertEqual(scene.selected_index, 0)

    def test_move_down_changes_selected_item(self):
        scene = PauseScene()

        scene.update(0.1, FakeInputManager(settings.MOVE_DOWN))

        self.assertEqual(scene.selected_index, 1)

    def test_move_up_changes_selected_item(self):
        scene = PauseScene()

        scene.update(0.1, FakeInputManager(settings.MOVE_UP))

        self.assertEqual(scene.selected_index, len(scene.items) - 1)

    def test_select_resume_calls_resume_scene(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertTrue(scene.manager.resumed)

    def test_click_resume_calls_resume_scene(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()
        mouse_position = scene.get_item_rect(0).center

        scene.update(0.1, FakeMouseInputManager(mouse_position))

        self.assertTrue(scene.manager.resumed)

    def test_click_outside_items_does_not_resume_scene(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 0

        scene.update(0.1, FakeMouseInputManager(mouse_position=(5, 5)))

        self.assertFalse(scene.manager.resumed)

    def test_click_outside_items_does_not_request_scene_change(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 1

        scene.update(0.1, FakeMouseInputManager(mouse_position=(5, 5)))

        self.assertIsNone(scene.manager.requested_scene_id)

    def test_pause_key_calls_resume_scene(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeInputManager(settings.PAUSE))

        self.assertTrue(scene.manager.resumed)

    def test_select_world_map_opens_world_map_from_pause(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 1

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertTrue(scene.manager.opened_world_map_from_pause)
        self.assertIsNone(scene.manager.requested_scene_id)

    def test_select_main_menu_requests_main_menu_scene(self):
        scene = PauseScene()
        scene.manager = FakeSceneManager()
        scene.selected_index = 2

        scene.update(0.1, FakeInputManager(settings.SELECT))

        self.assertEqual(scene.manager.requested_scene_id, settings.MAIN_MENU_SCENE)

    def test_pause_scene_without_manager_does_not_crash(self):
        scene = PauseScene()

        scene.update(0.1, FakeInputManager(settings.SELECT))
        scene.selected_index = 1
        scene.update(0.1, FakeInputManager(settings.SELECT))
        scene.selected_index = 2
        scene.update(0.1, FakeInputManager(settings.SELECT))
        scene.update(0.1, FakeInputManager(settings.PAUSE))

    def test_draw_does_not_crash(self):
        scene = PauseScene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)


if __name__ == "__main__":
    unittest.main()
