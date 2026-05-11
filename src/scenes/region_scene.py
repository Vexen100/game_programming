import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.entities.player import Player
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class RegionScene(BaseScene):
    """
    Стандартная сцена региона. Поле, где бегает игрок и происходит сама игра.
    """

    def __init__(self) -> None:
        self.tile_map = TileMap(self.create_test_map())
        self.player = Player(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        self.manager = None

    def create_test_map(self):
        """Создаёт простую тестовую карту региона"""
        width = settings.SCREEN_WIDTH // settings.TILE_SIZE
        height = settings.SCREEN_HEIGHT // settings.TILE_SIZE + 1
        matrix = []

        for row in range(height):
            map_row = []
            for tile in range(width):
                is_border = row == 0 or tile == 0 or row == height - 1 or tile == width - 1
                is_inner_wall = (
                    (tile == 10 and 4 <= row <= 14)
                    or (row == 8 and 15 <= tile <= 25)
                    or (tile == 28 and 3 <= row <= 10)
                    or (row == 15 and 18 <= tile <= 30)
                )
                if is_border or is_inner_wall:
                    map_row.append(WALL)
                else:
                    map_row.append(FLOOR)
            matrix.append(map_row)

        return matrix

    def handle_events(self, events):
        pass

    def update(self, dt, input_manager):
        self.player.update(dt, input_manager)

    def draw(self, screen: pygame.Surface):
        self.tile_map.draw(screen)
        self.player.draw(screen)
