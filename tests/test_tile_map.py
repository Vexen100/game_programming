import os
import tempfile
import unittest
from pathlib import Path

import pygame
from PIL import Image

from src.core.resource_manager import ResourceManager
from src.world.tile_map import TileMap
from src.world.tile_types import GRASS


class TestTileMapTileAssets(unittest.TestCase):
    """Проверяет отрисовку TileMap через реальные tile PNG."""

    @classmethod
    def setUpClass(cls):
        """Инициализирует PyGame для headless draw tests.

        Returns:
            None.
        """
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()

    def test_draw_uses_real_tile_surface_when_available(self):
        """Проверяет, что TileMap.draw берет surface из ResourceManager.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "tiles" / "grass.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (32, 32), (12, 200, 34, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={GRASS: "tiles/grass.png"},
                entity_assets={},
            )
            tile_map = TileMap([[GRASS]])
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            tile_map.draw(screen, resource_manager=resource_manager)

            self.assertEqual(screen.get_at((8, 8))[:3], (12, 200, 34))
