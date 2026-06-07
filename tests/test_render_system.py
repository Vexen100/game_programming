import unittest

import pygame

from src.components.components import Position, Renderable, Sprite
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.render_system import RenderSystem


class FakeResourceManager:
    def __init__(self):
        self.calls = []

    def get_entity_surface(self, asset_key, width, height, fallback_color):
        self.calls.append((asset_key, width, height, fallback_color))
        surface = pygame.Surface((width, height))
        surface.fill((10, 20, 30))
        return surface


class TestRenderSystem(unittest.TestCase):
    def create_entity(self, ecm, with_sprite=True):
        entity = ecm.create_entity()
        ecm.add_component(entity, Position(4, 5))
        ecm.add_component(entity, Renderable(12, 10, (200, 50, 50)))

        if with_sprite:
            ecm.add_component(entity, Sprite("enemy"))

        return entity

    def test_render_system_draws_without_resource_manager(self):
        ecm = EntityComponentManager()
        self.create_entity(ecm)
        screen = pygame.Surface((32, 32))

        RenderSystem().draw(ecm, screen)

        self.assertEqual(screen.get_at((5, 6))[:3], (200, 50, 50))

    def test_render_system_draws_with_sprite_resource_manager(self):
        ecm = EntityComponentManager()
        self.create_entity(ecm)
        resource_manager = FakeResourceManager()
        screen = pygame.Surface((32, 32))

        RenderSystem(resource_manager).draw(ecm, screen)

        self.assertEqual(screen.get_at((5, 6))[:3], (10, 20, 30))
        self.assertEqual(resource_manager.calls, [("enemy", 12, 10, (200, 50, 50))])

    def test_render_system_falls_back_to_renderable_without_sprite(self):
        ecm = EntityComponentManager()
        self.create_entity(ecm, with_sprite=False)
        resource_manager = FakeResourceManager()
        screen = pygame.Surface((32, 32))

        RenderSystem(resource_manager).draw(ecm, screen)

        self.assertEqual(screen.get_at((5, 6))[:3], (200, 50, 50))
        self.assertEqual(resource_manager.calls, [])


if __name__ == "__main__":
    unittest.main()
