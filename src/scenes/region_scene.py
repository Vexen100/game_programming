import pygame
import settings
from src.components.components import Health, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
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
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        self.ecs_player_id = self.entity_factory.create_player(x=100, y=100)
        self.check_ecs_player()
        self.player = Player(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        self.manager = None

    def check_ecs_player(self):
        """Проверяет, что ECS-игрок создан с базовыми компонентами"""
        position = self.ecm.get_component(self.ecs_player_id, Position)
        health = self.ecm.get_component(self.ecs_player_id, Health)

        if position is None:
            raise RuntimeError("ECS player was created without Position component")

        if health is None:
            raise RuntimeError("ECS player was created without Health component")

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
