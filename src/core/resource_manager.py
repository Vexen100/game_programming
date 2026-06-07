from pathlib import Path

import pygame
import settings
from src.world.tile_map import TILE_COLORS


class ResourceManager:
    """Кэширует изображения и generated placeholders без обязательных внешних assets"""

    def __init__(self, image_root="assets/images"):
        self.image_root = Path(image_root)
        self.images = {}
        self.generated_surfaces = {}

    def load_image(self, key, relative_path, size=None):
        cache_key = (key, size)

        if cache_key in self.images:
            return self.images[cache_key]

        image_path = self.image_root / relative_path

        if not image_path.is_file():
            width, height = size or (settings.TILE_SIZE, settings.TILE_SIZE)
            return self.get_or_create_placeholder(key, width, height, settings.UNKNOWN_TILE_COLOR)

        image = pygame.image.load(str(image_path))

        if size is not None:
            image = pygame.transform.scale(image, size)

        self.images[cache_key] = image
        return image

    def get_image(self, key):
        for image_key, image in self.images.items():
            if image_key[0] == key:
                return image

        return None

    def has_image(self, key):
        return self.get_image(key) is not None

    def get_or_create_placeholder(self, key, width, height, color):
        cache_key = (key, width, height, color)

        if cache_key in self.generated_surfaces:
            return self.generated_surfaces[cache_key]

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(color)

        border_color = self.get_border_color(color)
        pygame.draw.rect(surface, border_color, surface.get_rect(), 1)
        pygame.draw.line(surface, border_color, (0, 0), (width - 1, height - 1))

        self.generated_surfaces[cache_key] = surface
        return surface

    def get_tile_surface(self, tile_id, tile_size):
        color = TILE_COLORS.get(tile_id, settings.UNKNOWN_TILE_COLOR)
        return self.get_or_create_placeholder(
            f"tile_{tile_id}",
            tile_size,
            tile_size,
            color,
        )

    def get_entity_surface(self, asset_key, width, height, fallback_color):
        image = self.get_image(asset_key)

        if image is not None:
            if image.get_width() == width and image.get_height() == height:
                return image

            return pygame.transform.scale(image, (width, height))

        return self.get_or_create_placeholder(asset_key, width, height, fallback_color)

    def get_border_color(self, color):
        red, green, blue = color[:3]
        return (
            max(0, red - 35),
            max(0, green - 35),
            max(0, blue - 35),
            255,
        )
