import pygame
import settings
from src.components.components import Health, Outpost, PlayerDefeated, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.scenes.base_scene import BaseScene
from src.systems.cleanup_system import CleanupSystem
from src.systems.collision_system import CollisionSystem
from src.systems.enemy_attack_system import EnemyAttackSystem
from src.systems.enemy_chase_system import EnemyChaseSystem
from src.systems.enemy_death_system import EnemyDeathSystem
from src.systems.melee_attack_system import MeleeAttackSystem
from src.systems.movement_system import MovementSystem
from src.systems.outpost_system import OutpostSystem
from src.systems.player_attack_input_system import PlayerAttackInputSystem
from src.systems.player_death_system import PlayerDeathSystem
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

    def __init__(self, game_state=None, event_bus=None) -> None:
        self.game_state = game_state
        self.event_bus = event_bus
        self.player_input_system = PlayerInputSystem()
        self.player_attack_input_system = PlayerAttackInputSystem()
        self.enemy_chase_system = EnemyChaseSystem()
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem()
        self.melee_attack_system = MeleeAttackSystem()
        self.enemy_death_system = EnemyDeathSystem(self.event_bus)
        self.outpost_system = OutpostSystem(self.event_bus)
        self.enemy_attack_system = EnemyAttackSystem()
        self.player_death_system = PlayerDeathSystem()
        self.cleanup_system = CleanupSystem()
        self.render_system = RenderSystem()
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None
        self.restart_region()

    def check_entity_components(self, entity_id, entity_name, *component_types):
        """Проверяет, что сущность создана с нужными компонентами"""
        for component_type in component_types:
            component = self.ecm.get_component(entity_id, component_type)
            if component is None:
                raise RuntimeError(
                    f"{entity_name} was created without {component_type.__name__} component"
                )

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

    def is_player_defeated(self):
        return self.ecm.has_component(self.ecs_player_id, PlayerDefeated)

    def request_world_map(self):
        if self.manager is not None:
            self.manager.request_change(settings.WORLD_MAP_SCENE)

    def get_region_title(self):
        if self.game_state is None:
            return "Region"

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return "Region"

        return region.name

    def get_current_region_id(self):
        if self.game_state is None:
            return None

        return self.game_state.current_region_id

    def restart_region(self):
        self.tile_map = TileMap(self.create_test_map())
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)

        self.ecs_player_id = self.entity_factory.create_player(x=100, y=100)
        self.check_entity_components(self.ecs_player_id, "ECS player", Position, Health)

        self.enemy_id = self.entity_factory.create_enemy(
            x=settings.TILE_SIZE * 6,
            y=settings.TILE_SIZE * 6,
        )
        self.check_entity_components(self.enemy_id, "ECS enemy", Position, Health)

        self.outpost_id = self.entity_factory.create_outpost(
            x=settings.TILE_SIZE * 8,
            y=settings.TILE_SIZE * 6,
        )
        self.check_entity_components(self.outpost_id, "ECS outpost", Position, Outpost)

    def update(self, dt, input_manager):
        self.current_dt = dt

        if input_manager.was_pressed(settings.DEBUG):
            self.debug_overlay.toggle()

        if input_manager.was_pressed(settings.OPEN_WORLD_MAP):
            self.request_world_map()
            return

        if self.is_player_defeated():
            if input_manager.was_pressed(settings.RESTART):
                self.restart_region()
            return

        self.player_input_system.update(self.ecm, input_manager)
        self.player_attack_input_system.update(self.ecm, input_manager)
        self.enemy_chase_system.update(self.ecm)
        previous_positions = self.movement_system.update(self.ecm, dt)
        self.collision_system.update(self.ecm, self.tile_map, previous_positions)
        self.melee_attack_system.update(self.ecm, dt)
        self.enemy_death_system.update(self.ecm, self.get_current_region_id())
        self.enemy_attack_system.update(self.ecm, dt)
        self.player_death_system.update(self.ecm)

        if not self.is_player_defeated():
            self.outpost_system.update(self.ecm, self.get_current_region_id())

        self.cleanup_system.update(self.ecm)

    def draw(self, screen: pygame.Surface):
        self.tile_map.draw(screen)
        self.render_system.draw(self.ecm, screen)
        self.hud.draw(screen, self.ecm, self.ecs_player_id, self.get_region_title())
        if self.is_player_defeated():
            self.hud.draw_defeat_message(screen)
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
