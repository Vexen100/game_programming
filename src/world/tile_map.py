import pygame
import settings
from src.world.tile_types import FLOOR, WALL


class TileMap:
    def __init__(self, matrix: list[list[int]]) -> None:
        self.matrix = matrix
        self.tile_size = settings.TILE_SIZE
        self.height = len(matrix)
        self.width = len(matrix[0])

    def draw(self, screen: pygame.Surface, camera=None):
        """Рисует тайлы карты (по сути рисует саму карту)"""
        for row in range(self.height):
            for tile in range(self.width):
                x, y = self.coord_tile_to_pixels(tile, row)
                if camera is not None:
                    x, y = camera.apply(x, y)
                rect = (x, y, self.tile_size, self.tile_size)
                if self.matrix[row][tile] == FLOOR:
                    pygame.draw.rect(screen, settings.FLOOR_COLOR, rect)
                elif self.matrix[row][tile] == WALL:
                    pygame.draw.rect(screen, settings.WALL_COLOR, rect)

    def coord_tile_to_pixels(self, tile_x, tile_y):
        """Преобразует индекс тайла в матрице карты в пиксельные координаты"""
        x = self.tile_size * tile_x
        y = self.tile_size * tile_y
        return x, y

    def coord_pixels_to_tile(self, x, y):
        """Преобразует пиксельные координаты в индекс тайла в матрице карты"""
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        return tile_x, tile_y

    def is_tile_blocked(self, tile_x, tile_y):
        """Проверяет, заблокирован ли тайл по координатам тайла"""
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return True

        return self.matrix[tile_y][tile_x] == WALL

    def is_point_blocked(self, x, y):
        """Проверяет, заблокирована ли точка по пиксельным координатам"""
        tile_x, tile_y = self.coord_pixels_to_tile(x, y)
        return self.is_tile_blocked(tile_x, tile_y)

    def is_blocked(self, x, y):
        """Совместимость: проверяет точку по пиксельным координатам"""
        return self.is_point_blocked(x, y)

    def is_rect_blocked(self, x, y, width, height):
        """Проверяет, заблокирован ли прямоугольник по пиксельным координатам"""
        left_tile = int(x // self.tile_size)
        right_tile = int((x + width - 1) // self.tile_size)
        top_tile = int(y // self.tile_size)
        bottom_tile = int((y + height - 1) // self.tile_size)

        for tile_y in range(top_tile, bottom_tile + 1):
            for tile_x in range(left_tile, right_tile + 1):
                if self.is_tile_blocked(tile_x, tile_y):
                    return True

        return False
