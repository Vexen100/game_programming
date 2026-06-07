import tempfile
import unittest
from pathlib import Path

import pygame

import settings
from src.core.resource_manager import ResourceManager
from src.world.tile_types import GRASS


class TestResourceManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_creates_placeholder_surface(self):
        resource_manager = ResourceManager()

        surface = resource_manager.get_or_create_placeholder(
            "player",
            28,
            28,
            (50, 120, 255),
        )

        self.assertIsInstance(surface, pygame.Surface)
        self.assertEqual(surface.get_size(), (28, 28))

    def test_caches_placeholder_surface(self):
        resource_manager = ResourceManager()

        first_surface = resource_manager.get_or_create_placeholder(
            "enemy",
            28,
            28,
            (200, 50, 50),
        )
        second_surface = resource_manager.get_or_create_placeholder(
            "enemy",
            28,
            28,
            (200, 50, 50),
        )

        self.assertIs(second_surface, first_surface)

    def test_missing_image_returns_placeholder_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as directory:
            resource_manager = ResourceManager(image_root=directory)

            surface = resource_manager.load_image(
                "missing",
                "missing.png",
                size=(16, 16),
            )

            self.assertIsInstance(surface, pygame.Surface)
            self.assertEqual(surface.get_size(), (16, 16))

    def test_tile_surfaces_are_cached(self):
        resource_manager = ResourceManager()

        first_surface = resource_manager.get_tile_surface(GRASS, settings.TILE_SIZE)
        second_surface = resource_manager.get_tile_surface(GRASS, settings.TILE_SIZE)

        self.assertIs(second_surface, first_surface)

    def test_entity_surfaces_differ_by_key_and_color(self):
        resource_manager = ResourceManager()

        player_surface = resource_manager.get_entity_surface(
            "player",
            28,
            28,
            (50, 120, 255),
        )
        enemy_surface = resource_manager.get_entity_surface(
            "enemy",
            28,
            28,
            (200, 50, 50),
        )

        self.assertIsNot(player_surface, enemy_surface)
        self.assertNotEqual(player_surface.get_at((1, 1)), enemy_surface.get_at((1, 1)))

    def test_load_image_caches_loaded_image_if_file_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "test.png"
            source_surface = pygame.Surface((4, 4))
            source_surface.fill((10, 20, 30))
            pygame.image.save(source_surface, image_path)
            resource_manager = ResourceManager(image_root=directory)

            first_surface = resource_manager.load_image("test", "test.png", size=(8, 8))
            second_surface = resource_manager.load_image("test", "test.png", size=(8, 8))

            self.assertIs(second_surface, first_surface)
            self.assertEqual(first_surface.get_size(), (8, 8))


if __name__ == "__main__":
    unittest.main()
