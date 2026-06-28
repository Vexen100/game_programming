import os
import unittest

import pygame

from src.components.components import DamagePopup, HitFlash, Position, TemporaryVisualEffect
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.visual_effect_system import VisualEffectSystem


class TestVisualEffectSystem(unittest.TestCase):
    """Проверяет runtime-only визуальные эффекты боя."""

    @classmethod
    def setUpClass(cls):
        """Готовит PyGame для headless draw-тестов.

        Returns:
            None.
        """
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        pygame.font.init()

    def test_hit_flash_expires_after_duration(self):
        """Проверяет удаление HitFlash после истечения таймера.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, HitFlash(duration=0.1, timer=0.1))

        VisualEffectSystem().update(ecm, dt=0.2)

        self.assertFalse(ecm.has_component(entity, HitFlash))

    def test_damage_popup_expires(self):
        """Проверяет удаление damage popup entity после истечения таймера.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        visual_effects = VisualEffectSystem()
        popup_id = visual_effects.spawn_damage_popup(ecm, 20, 20, 5)

        visual_effects.update(ecm, dt=1)

        self.assertNotIn(popup_id, ecm.alive_entities)

    def test_slash_effect_expires(self):
        """Проверяет удаление slash effect entity после истечения таймера.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        visual_effects = VisualEffectSystem()
        effect_id = visual_effects.spawn_slash_effect(
            ecm,
            {"x": 10, "y": 10, "width": 20, "height": 12},
            "right",
        )

        visual_effects.update(ecm, dt=1)

        self.assertNotIn(effect_id, ecm.alive_entities)

    def test_visual_effect_system_draw_does_not_crash(self):
        """Проверяет отрисовку popup и slash effect без падения.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        visual_effects = VisualEffectSystem()
        visual_effects.spawn_damage_popup(ecm, 20, 20, 7)
        visual_effects.spawn_slash_effect(
            ecm,
            {"x": 10, "y": 10, "width": 20, "height": 12},
            "right",
        )
        screen = pygame.Surface((96, 64), pygame.SRCALPHA)

        visual_effects.draw(ecm, screen)

        self.assertEqual(len(ecm.get_entities_with(Position, DamagePopup)), 1)
        self.assertEqual(len(ecm.get_entities_with(Position, TemporaryVisualEffect)), 1)
