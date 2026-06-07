import pygame
import settings
from src.world.tile_types import (
    BLOCKING_TILES,
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


TILE_COLORS = {
    FLOOR: settings.FLOOR_COLOR,
    WALL: settings.WALL_COLOR,
    GRASS: settings.GRASS_COLOR,
    DIRT: settings.DIRT_COLOR,
    ROAD: settings.ROAD_COLOR,
    RUINS_FLOOR: settings.RUINS_FLOOR_COLOR,
    WATER: settings.WATER_COLOR,
    FOREST: settings.FOREST_COLOR,
    BRIDGE: settings.BRIDGE_COLOR,
    CASTLE_FLOOR: settings.CASTLE_FLOOR_COLOR,
    CASTLE_WALL: settings.CASTLE_WALL_COLOR,
    CRACKED_STONE_FLOOR: settings.CRACKED_STONE_FLOOR_COLOR,
    DARK_CORRIDOR_FLOOR: settings.DARK_CORRIDOR_FLOOR_COLOR,
}


class TileMap:
    """Хранит матрицу тайлов и рисует карту с учетом камеры.

    """
    def __init__(self, matrix: list[list[int]]) -> None:
        """Инициализирует `TileMap` и сохраняет начальные зависимости.

        Args:
            matrix: Двумерная матрица тайлов карты.

        Returns:
            None.
        """
        self.matrix = matrix
        self.tile_size = settings.TILE_SIZE
        self.height = len(matrix)
        self.width = len(matrix[0])

    def draw(self, screen: pygame.Surface, camera=None, resource_manager=None):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.
            resource_manager: Менеджер графических ресурсов и placeholder-изображений.

        Returns:
            None.
        """
        for row in range(self.height):
            for tile in range(self.width):
                x, y = self.coord_tile_to_pixels(tile, row)
                if camera is not None:
                    x, y = camera.apply(x, y)
                rect = (x, y, self.tile_size, self.tile_size)
                tile_id = self.matrix[row][tile]

                if resource_manager is not None:
                    surface = resource_manager.get_tile_surface(tile_id, self.tile_size)
                    if surface is not None:
                        screen.blit(surface, (x, y))
                        continue

                pygame.draw.rect(
                    screen,
                    TILE_COLORS.get(tile_id, settings.UNKNOWN_TILE_COLOR),
                    rect,
                )

    def coord_tile_to_pixels(self, tile_x, tile_y):
        """Переводит координаты тайла в пиксельную позицию.

        Args:
            tile_x: Координата тайла по оси X.
            tile_y: Координата тайла по оси Y.

        Returns:
            Результат выполнения `coord_tile_to_pixels`.
        """
        x = self.tile_size * tile_x
        y = self.tile_size * tile_y
        return x, y

    def coord_pixels_to_tile(self, x, y):
        """Переводит пиксельную позицию в координаты тайла.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Результат выполнения `coord_pixels_to_tile`.
        """
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        return tile_x, tile_y

    def is_tile_blocked(self, tile_x, tile_y):
        """Проверяет, заблокирован ли тайл для движения.

        Args:
            tile_x: Координата тайла по оси X.
            tile_y: Координата тайла по оси Y.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return True

        return self.matrix[tile_y][tile_x] in BLOCKING_TILES

    def is_point_blocked(self, x, y):
        """Проверяет, находится ли точка внутри непроходимого тайла.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        tile_x, tile_y = self.coord_pixels_to_tile(x, y)
        return self.is_tile_blocked(tile_x, tile_y)

    def is_blocked(self, x, y):
        """Проверяет, заблокирована ли точка на карте.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.is_point_blocked(x, y)

    def is_rect_blocked(self, x, y, width, height):
        """Проверяет, пересекает ли прямоугольник непроходимые тайлы.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        left_tile = int(x // self.tile_size)
        right_tile = int((x + width - 1) // self.tile_size)
        top_tile = int(y // self.tile_size)
        bottom_tile = int((y + height - 1) // self.tile_size)

        for tile_y in range(top_tile, bottom_tile + 1):
            for tile_x in range(left_tile, right_tile + 1):
                if self.is_tile_blocked(tile_x, tile_y):
                    return True

        return False
