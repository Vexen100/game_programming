import unittest
from unittest.mock import patch

import pygame

from src.components.components import Dead, Enemy, Health, MeleeAttack, Position, Renderable
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.render_system import RenderSystem
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

    def test_hud_draw_with_attack_cooldown_and_prompts(self):
        ecm, player = self.create_ecm_with_player()
        ecm.add_component(player, Health(current=100, maximum=100))
        ecm.add_component(
            player,
            MeleeAttack(
                damage=10,
                attack_range=48,
                cooldown=0.4,
                cooldown_timer=0.2,
            ),
        )

        HUD().draw(
            self.create_surface(),
            ecm,
            player,
            "Region",
            contextual_prompts=["E: Clear outpost"],
        )

    def test_hud_draw_defeat_message(self):
        HUD().draw_defeat_message(self.create_surface())

    def test_render_system_skips_dead_enemy_health_bar(self):
        ecm = EntityComponentManager()
        enemy = ecm.create_entity(tag="enemy")
        ecm.add_component(enemy, Enemy())
        ecm.add_component(enemy, Position(32, 32))
        ecm.add_component(enemy, Renderable(width=16, height=16, color=(200, 40, 40)))
        ecm.add_component(enemy, Health(current=10, maximum=10))
        ecm.add_component(enemy, Dead())

        with patch("pygame.draw.rect") as mock_draw_rect:
            RenderSystem().draw_enemy_health_bars(ecm, self.create_surface())

        mock_draw_rect.assert_not_called()

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
