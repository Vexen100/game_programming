import pygame
import settings
from src.components.components import Health, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.scenes.base_scene import BaseScene
from src.systems.collision_system import CollisionSystem
from src.systems.movement_system import MovementSystem
from src.systems.player_input_system import PlayerInputSystem
from src.systems.render_system import RenderSystem
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
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
        self.enemy_id = self.entity_factory.create_enemy(
            x=settings.TILE_SIZE * 6,
            y=settings.TILE_SIZE * 6,
        )
        self.check_enemy()
        self.player_input_system = PlayerInputSystem()
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem()
        self.render_system = RenderSystem()
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None

    def check_ecs_player(self):
        """Проверяет, что ECS-игрок создан с базовыми компонентами"""
        position = self.ecm.get_component(self.ecs_player_id, Position)
        health = self.ecm.get_component(self.ecs_player_id, Health)

        if position is None:
            raise RuntimeError("ECS player was created without Position component")

        if health is None:
            raise RuntimeError("ECS player was created without Health component")

    def check_enemy(self):
        """Проверяет, что ECS-враг создан с базовыми компонентами"""
        position = self.ecm.get_component(self.enemy_id, Position)
        health = self.ecm.get_component(self.enemy_id, Health)

        if position is None:
            raise RuntimeError("ECS enemy was created without Position component")

        if health is None:
            raise RuntimeError("ECS enemy was created without Health component")

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
        self.current_dt = dt

        if input_manager.was_pressed(settings.DEBUG):
            self.debug_overlay.toggle()

        self.player_input_system.update(self.ecm, input_manager)
        previous_positions = self.movement_system.update(self.ecm, dt)
        self.collision_system.update(self.ecm, self.tile_map, previous_positions)

    def draw(self, screen: pygame.Surface):
        self.tile_map.draw(screen)
        self.render_system.draw(self.ecm, screen)
        self.hud.draw(screen, self.ecm, self.ecs_player_id, "Region")
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
