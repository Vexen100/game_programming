import unittest

import pygame

from src.components.components import Health, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def create_surface(self):
        return pygame.Surface((300, 200))

    def create_ecm_with_player(self):
        ecm = EntityComponentManager()
        player = ecm.create_entity(tag="player")
        return ecm, player

    def create_tile_map(self):
        matrix = [
            [WALL, WALL, WALL],
            [WALL, FLOOR, WALL],
            [WALL, WALL, WALL],
        ]
        return TileMap(matrix)

    def test_hud_draw(self):
        ecm, player = self.create_ecm_with_player()
        ecm.add_component(player, Health(current=100, maximum=100))

        HUD().draw(self.create_surface(), ecm, player, "Region")

    def test_hud_draw_without_health(self):
        ecm, player = self.create_ecm_with_player()

        HUD().draw(self.create_surface(), ecm, player, "Region")

    def test_debug_overlay_toggle(self):
        debug_overlay = DebugOverlay()

        self.assertFalse(debug_overlay.visible)
        debug_overlay.toggle()
        self.assertTrue(debug_overlay.visible)

    def test_debug_overlay_draw_when_hidden(self):
        ecm, player = self.create_ecm_with_player()
        debug_overlay = DebugOverlay()

        debug_overlay.draw(self.create_surface(), ecm, player, self.create_tile_map(), dt=1 / 60)

    def test_debug_overlay_draw_when_visible(self):
        ecm, player = self.create_ecm_with_player()
        ecm.add_component(player, Position(32, 32))
        debug_overlay = DebugOverlay()
        debug_overlay.toggle()

        debug_overlay.draw(self.create_surface(), ecm, player, self.create_tile_map(), dt=1 / 60)

    def test_debug_overlay_draw_without_position(self):
        ecm, player = self.create_ecm_with_player()
        debug_overlay = DebugOverlay()
        debug_overlay.toggle()

        debug_overlay.draw(self.create_surface(), ecm, player, self.create_tile_map(), dt=1 / 60)


if __name__ == "__main__":
    unittest.main()
