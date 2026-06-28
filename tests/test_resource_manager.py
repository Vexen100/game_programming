import os
import tempfile
import unittest
from pathlib import Path

import pygame
from PIL import Image

from src.core.resource_manager import ResourceManager
from src.world.tile_types import GRASS


class TestResourceManagerTiles(unittest.TestCase):
    """Проверяет загрузку surface tile PNG через ResourceManager."""

    @classmethod
    def setUpClass(cls):
        """Инициализирует PyGame для headless surface tests.

        Returns:
            None.
        """
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()

    def test_loads_existing_tile_png_from_temp_root(self):
        """Проверяет загрузку существующего tile PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "tiles" / "grass.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (40, 180, 70, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={GRASS: "tiles/grass.png"},
                entity_assets={},
            )

            surface = resource_manager.get_tile_surface(GRASS, 32)

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertEqual(surface.get_at((16, 16))[:3], (40, 180, 70))

    def test_falls_back_when_tile_png_is_missing(self):
        """Проверяет fallback placeholder при отсутствующем tile PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={GRASS: "tiles/missing.png"},
                entity_assets={},
            )

            surface = resource_manager.get_tile_surface(GRASS, 32)

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertFalse(resource_manager.has_image(f"tile_{GRASS}"))

    def test_resource_manager_loads_existing_entity_asset(self):
        """Проверяет загрузку existing entity PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (100, 50, 200, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={"player": "entities/player.png"},
            )

            surface = resource_manager.get_entity_surface(
                "player",
                32,
                32,
                (255, 0, 0),
            )

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertEqual(surface.get_at((16, 16))[:3], (100, 50, 200))

    def test_resource_manager_falls_back_for_missing_entity_asset(self):
        """Проверяет fallback для отсутствующего entity PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={"player": "entities/missing.png"},
            )

            surface = resource_manager.get_entity_surface(
                "player",
                32,
                32,
                (255, 0, 0),
            )

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertGreater(surface.get_at((16, 16)).a, 0)

    def test_resource_manager_supply_cache_sprite_missing_uses_fallback(self):
        """Проверяет fallback для отсутствующего sprite склада снабжения.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource_manager = ResourceManager(image_root=tmp)

            surface = resource_manager.get_entity_surface(
                "supply_cache_enemy",
                32,
                32,
                (165, 95, 35),
            )

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertGreater(surface.get_at((16, 16)).a, 0)

    def test_resource_manager_loads_existing_animation_frame(self):
        """Проверяет загрузку existing animation frame PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "walk_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (90, 180, 240, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )

            surface = resource_manager.get_animation_frame_surface(
                "player",
                "walk",
                "down",
                0,
                32,
                32,
                (255, 0, 0),
            )

            self.assertIsNotNone(surface)
            self.assertEqual(surface.get_size(), (32, 32))
            self.assertEqual(surface.get_at((16, 16))[:3], (90, 180, 240))

    def test_resource_manager_returns_none_for_missing_animation_frame(self):
        """Проверяет, что missing animation frame не создает placeholder.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )

            surface = resource_manager.get_animation_frame_surface(
                "player",
                "walk",
                "down",
                0,
                32,
                32,
                (255, 0, 0),
            )

            self.assertIsNone(surface)

    def test_resource_manager_loads_existing_attack_frame(self):
        """Проверяет загрузку existing attack animation frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "attack_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (240, 120, 40, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )

            surface = resource_manager.get_animation_frame_surface(
                "player",
                "attack",
                "down",
                0,
                32,
                32,
                (255, 0, 0),
            )

            self.assertIsNotNone(surface)
            self.assertEqual(surface.get_size(), (32, 32))
            self.assertEqual(surface.get_at((16, 16))[:3], (240, 120, 40))
