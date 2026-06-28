from pathlib import Path

import pygame
import settings
from src.world.tile_map import TILE_COLORS
from src.world.tile_types import (
    BRIDGE,
    CASTLE_FLOOR,
    CASTLE_WALL,
    CRACKED_STONE_FLOOR,
    DARK_CORRIDOR_FLOOR,
    DIRT,
    FLOOR,
    FOREST,
    GRASS,
    ROAD,
    RUINS_FLOOR,
    WALL,
    WATER,
)


DEFAULT_TILE_ASSETS = {
    FLOOR: "tiles/ruins_floor.png",
    WALL: "tiles/wall.png",
    GRASS: "tiles/grass.png",
    DIRT: "tiles/dirt.png",
    ROAD: "tiles/road.png",
    RUINS_FLOOR: "tiles/ruins_floor.png",
    WATER: "tiles/water.png",
    FOREST: "tiles/forest.png",
    BRIDGE: "tiles/bridge.png",
    CASTLE_FLOOR: "castle/castle_floor.png",
    CASTLE_WALL: "castle/castle_wall.png",
    CRACKED_STONE_FLOOR: "castle/cracked_stone_floor.png",
    DARK_CORRIDOR_FLOOR: "castle/dark_corridor_floor.png",
}


DEFAULT_ENTITY_ASSETS = {
    "player": "entities/player.png",
    "enemy": "entities/enemy.png",
    "outpost_enemy": "entities/outpost_enemy.png",
    "npc_active": "entities/npc_active.png",
    "supply_cache_enemy": "entities/supply_cache_enemy.png",
    "capture_point_enemy": "entities/capture_point_enemy.png",
}


class ResourceManager:
    """Загружает изображения тайлов и сущностей с безопасными placeholder-ами.

    """

    def __init__(
        self,
        image_root="assets/images",
        tile_assets=None,
        entity_assets=None,
    ):
        """Инициализирует `ResourceManager` и сохраняет начальные зависимости.

        Args:
            image_root: Корневой каталог изображений проекта.
            tile_assets: Словарь соответствия tile id и путей к изображениям тайлов.
            entity_assets: Словарь соответствия ключей сущностей и путей к изображениям.

        Returns:
            None.
        """
        self.image_root = Path(image_root)
        self.tile_assets = dict(DEFAULT_TILE_ASSETS if tile_assets is None else tile_assets)
        self.entity_assets = dict(
            DEFAULT_ENTITY_ASSETS if entity_assets is None else entity_assets
        )
        self.images = {}
        self.generated_surfaces = {}

    def load_image(self, key, relative_path, size=None, fallback_color=None):
        """Загружает изображение.

        Args:
            key: Ключ словаря, ресурса или игровой сущности.
            relative_path: Путь к изображению относительно корня ассетов.
            size: Размер изображения, кадра, тайла или объекта.
            fallback_color: Цвет fallback-прямоугольника, если изображения нет.

        Returns:
            Результат выполнения `load_image`.
        """
        cache_key = (key, size)

        if cache_key in self.images:
            return self.images[cache_key]

        image_path = self.image_root / relative_path

        if not image_path.is_file():
            width, height = size or (settings.TILE_SIZE, settings.TILE_SIZE)
            return self.get_or_create_placeholder(
                key,
                width,
                height,
                fallback_color or settings.UNKNOWN_TILE_COLOR,
            )

        image = pygame.image.load(str(image_path))

        if size is not None:
            image = pygame.transform.scale(image, size)

        self.images[cache_key] = image
        return image

    def get_image(self, key):
        """Возвращает изображение.

        Args:
            key: Ключ словаря, ресурса или игровой сущности.

        Returns:
            Найденное или вычисленное значение: изображение.
        """
        for image_key, image in self.images.items():
            if image_key[0] == key:
                return image

        return None

    def has_image(self, key):
        """Проверяет, загружено ли изображение.

        Args:
            key: Ключ словаря, ресурса или игровой сущности.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.get_image(key) is not None

    def get_or_create_placeholder(self, key, width, height, color):
        """Возвращает placeholder или создает его при первом запросе.

        Args:
            key: Ключ словаря, ресурса или игровой сущности.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.
            color: Цвет `цвет` в формате PyGame.

        Returns:
            Поверхность placeholder-изображения нужного размера.
        """
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
        """Возвращает тайл поверхность.

        Args:
            tile_id: Идентификатор типа тайла.
            tile_size: Значение `тайл size`, используемое в логике метода.

        Returns:
            Найденное или вычисленное значение: тайл поверхность.
        """
        color = TILE_COLORS.get(tile_id, settings.UNKNOWN_TILE_COLOR)
        relative_path = self.tile_assets.get(tile_id)

        if relative_path is not None:
            return self.load_image(
                f"tile_{tile_id}",
                relative_path,
                size=(tile_size, tile_size),
                fallback_color=color,
            )

        return self.get_or_create_placeholder(f"tile_{tile_id}", tile_size, tile_size, color)

    def get_entity_surface(self, asset_key, width, height, fallback_color):
        """Возвращает сущность поверхность.

        Args:
            asset_key: Ключ графического ассета сущности.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.
            fallback_color: Цвет fallback-прямоугольника, если изображения нет.

        Returns:
            Найденное или вычисленное значение: сущность поверхность.
        """
        relative_path = self.entity_assets.get(asset_key)

        if relative_path is not None:
            return self.load_image(
                asset_key,
                relative_path,
                size=(width, height),
                fallback_color=fallback_color,
            )

        image = self.get_image(asset_key)
        if image is not None:
            if image.get_width() == width and image.get_height() == height:
                return image

            return pygame.transform.scale(image, (width, height))

        return self.get_or_create_placeholder(asset_key, width, height, fallback_color)

    def get_animation_frame_surface(
        self,
        animation_key,
        state,
        direction,
        frame_index,
        width,
        height,
        fallback_color,
    ):
        """Возвращает кадр runtime-анимации, если файл существует.

        Args:
            animation_key: Логический ключ группы кадров.
            state: Состояние анимации, например `idle`, `walk` или `attack`.
            direction: Направление анимации.
            frame_index: Индекс кадра.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.
            fallback_color: Цвет fallback-прямоугольника, если кадра нет.

        Returns:
            Surface кадра или `None`, если файл отсутствует.
        """
        relative_path = (
            f"entities/{animation_key}/{state}_{direction}_{frame_index}.png"
        )
        cache_key = (
            f"animation_{animation_key}_{state}_{direction}_{frame_index}",
            (width, height),
        )

        if cache_key in self.images:
            return self.images[cache_key]

        image_path = self.image_root / relative_path

        if not image_path.is_file():
            return None

        image = pygame.image.load(str(image_path))
        image = pygame.transform.scale(image, (width, height))
        self.images[cache_key] = image
        return image

    def has_animation_frame(self, animation_key, state, direction, frame_index):
        """Проверяет, существует ли файл кадра анимации.

        Args:
            animation_key: Логический ключ группы кадров.
            state: Состояние анимации, например `idle`, `walk` или `attack`.
            direction: Направление анимации.
            frame_index: Индекс кадра.

        Returns:
            `True`, если файл кадра существует, иначе `False`.
        """
        relative_path = (
            f"entities/{animation_key}/{state}_{direction}_{frame_index}.png"
        )
        return (self.image_root / relative_path).is_file()

    def get_border_color(self, color):
        """Возвращает рамка цвет.

        Args:
            color: Цвет `цвет` в формате PyGame.

        Returns:
            Найденное или вычисленное значение: рамка цвет.
        """
        red, green, blue = color[:3]
        return (
            max(0, red - 35),
            max(0, green - 35),
            max(0, blue - 35),
            255,
        )
