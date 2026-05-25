import unittest

import pygame
import settings
from src.core.input_manager import InputManager


class TestInputManager(unittest.TestCase):
    def test_toggle_fullscreen_action_uses_f11(self):
        input_manager = InputManager()
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)

        input_manager.update_events(event)

        self.assertTrue(input_manager.was_pressed(settings.TOGGLE_FULLSCREEN))

    def test_mouse_button_down_updates_position_and_pressed_button(self):
        input_manager = InputManager()
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=(120, 80),
            button=1,
        )

        input_manager.update_events(event)

        self.assertEqual(input_manager.mouse_position, (120, 80))
        self.assertTrue(input_manager.was_mouse_pressed(1))

    def test_mouse_motion_updates_position(self):
        input_manager = InputManager()
        event = pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(45, 90),
        )

        input_manager.update_events(event)

        self.assertEqual(input_manager.mouse_position, (45, 90))

    def test_clear_resets_mouse_pressed_buttons(self):
        input_manager = InputManager()
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=(120, 80),
            button=1,
        )

        input_manager.update_events(event)
        input_manager.clear()

        self.assertFalse(input_manager.was_mouse_pressed(1))

    def test_arrow_key_can_drive_move_action(self):
        input_manager = InputManager()
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)

        input_manager.update_events(event)

        self.assertTrue(input_manager.is_pressed(settings.MOVE_UP))


if __name__ == "__main__":
    unittest.main()
