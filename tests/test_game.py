import unittest
from unittest.mock import patch

import pygame
import settings
from src.core.game import Game


class TestGame(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
