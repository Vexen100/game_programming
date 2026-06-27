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
