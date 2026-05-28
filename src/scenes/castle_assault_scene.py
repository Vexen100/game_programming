import pygame
import settings
from src.algorithms.flood_fill import are_tiles_reachable
from src.components.components import (
    CapturePoint,
    Collider,
    Health,
    PatrolRoute,
    PlayerDefeated,
    Position,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.scenes.base_scene import BaseScene
from src.systems.capture_system import CaptureSystem
from src.systems.castle_wave_system import CastleWaveSystem
from src.systems.cleanup_system import CleanupSystem
from src.systems.collision_system import CollisionSystem
from src.systems.enemy_attack_system import EnemyAttackSystem
from src.systems.enemy_chase_system import EnemyChaseSystem
from src.systems.enemy_death_system import EnemyDeathSystem
from src.systems.melee_attack_system import MeleeAttackSystem
from src.systems.movement_system import MovementSystem
from src.systems.player_attack_input_system import PlayerAttackInputSystem
from src.systems.player_death_system import PlayerDeathSystem
from src.systems.player_input_system import PlayerInputSystem
from src.systems.render_system import RenderSystem
from src.systems.spatial_index_system import SpatialIndexSystem
from src.ui import texts
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class CastleAssaultScene(BaseScene):
    """Статическая сцена штурма замка"""

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
        self.capture_system = CaptureSystem(self.event_bus)
        self.enemy_attack_system = EnemyAttackSystem()
        self.player_death_system = PlayerDeathSystem()
        self.spatial_index_system = SpatialIndexSystem()
        self.cleanup_system = CleanupSystem()
        self.render_system = RenderSystem()
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None
        self.enemy_spatial_index = None
        self.castle_wave_spawn_tiles = [
            (4, 3),
            (20, 6),
        ]
        self.restart_castle()

    def check_entity_components(self, entity_id, entity_name, *component_types):
        """Проверяет, что сущность создана с нужными компонентами"""
        for component_type in component_types:
            component = self.ecm.get_component(entity_id, component_type)
            if component is None:
                raise RuntimeError(
                    f"{entity_name} was created without {component_type.__name__} component"
                )

    def create_test_castle_map(self):
        """Создаёт простую статическую карту замка"""
        width = settings.SCREEN_WIDTH // settings.TILE_SIZE
        height = settings.SCREEN_HEIGHT // settings.TILE_SIZE + 1
        matrix = []

        for row in range(height):
            map_row = []
            for tile in range(width):
                is_border = row == 0 or tile == 0 or row == height - 1 or tile == width - 1
                is_inner_wall = (
                    (tile == 8 and 2 <= row <= 10 and row not in (5, 6))
                    or (row == 6 and 12 <= tile <= 28 and tile not in (20, 21))
                    or (tile == 25 and 10 <= row <= 20 and row not in (15, 16))
                    or (row == 16 and 3 <= tile <= 18 and tile not in (11, 12))
                    or (row == 11 and 28 <= tile <= 36 and tile not in (32, 33))
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
            if self.assault_completed:
                self.manager.request_change(settings.WORLD_MAP_SCENE)
            elif hasattr(self.manager, "open_world_map"):
                self.manager.open_world_map(return_scene=self)
            else:
                self.manager.request_change(settings.WORLD_MAP_SCENE)

    def request_pause(self):
        if self.manager is not None:
            self.manager.request_pause(settings.PAUSE_SCENE)

    def get_current_region_id(self):
        if self.game_state is None:
            return None

        return self.game_state.current_region_id

    def get_castle_title(self):
        if self.game_state is None:
            return "Штурм замка"

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return "Штурм замка"

        return f"Штурм: {region.name}"

    def get_entity_tile(self, entity_id):
        position = self.ecm.get_component(entity_id, Position)
        collider = self.ecm.get_component(entity_id, Collider)

        if collider is None:
            return self.tile_map.coord_pixels_to_tile(position.x, position.y)

        return self.tile_map.coord_pixels_to_tile(
            position.x + collider.width / 2,
            position.y + collider.height / 2,
        )

    def validate_castle_layout(self):
        start_tile = self.get_entity_tile(self.ecs_player_id)
        target_tiles = []

        for enemy_id in self.enemy_ids:
            target_tiles.append(self.get_entity_tile(enemy_id))
            patrol_route = self.ecm.get_component(enemy_id, PatrolRoute)

            if patrol_route is not None:
                target_tiles.extend(patrol_route.patrol_tiles)

        for capture_point_id in self.capture_point_ids:
            target_tiles.append(self.get_entity_tile(capture_point_id))

        for spawn_tile in self.castle_wave_spawn_tiles:
            target_tiles.append(spawn_tile)

        if not are_tiles_reachable(self.tile_map, start_tile, target_tiles):
            raise ValueError("Castle layout has unreachable important tiles")

    def are_all_capture_points_captured(self):
        if not self.capture_point_ids:
            return False

        for capture_point_id in self.capture_point_ids:
            capture_point = self.ecm.get_component(capture_point_id, CapturePoint)

            if not capture_point.captured:
                return False

        return True

    def complete_assault_if_ready(self):
        if self.assault_completed:
            return

        if not self.are_all_capture_points_captured():
            return

        self.assault_completed = True

    def restart_castle(self):
        self.assault_completed = False
        self.enemy_spatial_index = None
        self.tile_map = TileMap(self.create_test_castle_map())
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        self.castle_wave_system = CastleWaveSystem(
            spawn_tiles=self.castle_wave_spawn_tiles,
            enemies_per_wave=2,
        )

        self.ecs_player_id = self.entity_factory.create_player(
            x=settings.TILE_SIZE * 3,
            y=settings.TILE_SIZE * 3,
        )
        self.check_entity_components(self.ecs_player_id, "ECS player", Position, Health)

        self.enemy_ids = [
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 10,
                y=settings.TILE_SIZE * 3,
            ),
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 7,
                y=settings.TILE_SIZE * 6,
            ),
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 11,
                y=settings.TILE_SIZE * 6,
            ),
        ]
        self.enemy_id = self.enemy_ids[0]
        self.add_patrol_routes()

        for enemy_id in self.enemy_ids:
            self.check_entity_components(enemy_id, "ECS enemy", Position, Health)

        self.capture_point_ids = [
            self.entity_factory.create_capture_point(
                x=settings.TILE_SIZE * 4,
                y=settings.TILE_SIZE * 2,
            ),
            self.entity_factory.create_capture_point(
                x=settings.TILE_SIZE * 10,
                y=settings.TILE_SIZE * 6,
            ),
        ]

        for capture_point_id in self.capture_point_ids:
            self.check_entity_components(capture_point_id, "CapturePoint", Position, CapturePoint)

        self.validate_castle_layout()
        self.capture_system.reset()
        self.castle_wave_system.reset()

    def rebuild_enemy_spatial_index(self):
        self.enemy_spatial_index = self.spatial_index_system.build_enemy_index(
            self.ecm,
            self.tile_map.width * self.tile_map.tile_size,
            self.tile_map.height * self.tile_map.tile_size,
            settings.TILE_SIZE * 4,
        )

    def add_patrol_routes(self):
        patrol_routes = [
            [(10, 3), (12, 3), (12, 5), (9, 5)],
            [(7, 6), (7, 9), (5, 9), (5, 6)],
            [(11, 6), (11, 8), (9, 8), (9, 6)],
        ]

        for enemy_id, patrol_tiles in zip(self.enemy_ids, patrol_routes):
            self.ecm.add_component(
                enemy_id,
                PatrolRoute(
                    patrol_tiles=patrol_tiles,
                    wait_duration=0.2,
                ),
            )

    def update(self, dt, input_manager):
        self.current_dt = dt

        if input_manager.was_pressed(settings.DEBUG):
            self.debug_overlay.toggle()

        if input_manager.was_pressed(settings.PAUSE):
            self.request_pause()
            return

        if input_manager.was_pressed(settings.OPEN_WORLD_MAP):
            self.request_world_map()
            return

        if self.assault_completed:
            return

        if self.is_player_defeated():
            if input_manager.was_pressed(settings.RESTART):
                self.restart_castle()
            return

        self.player_input_system.update(self.ecm, input_manager)
        self.player_attack_input_system.update(self.ecm, input_manager)
        self.enemy_chase_system.update(self.ecm, self.tile_map, dt)
        previous_positions = self.movement_system.update(self.ecm, dt)
        self.collision_system.update(self.ecm, self.tile_map, previous_positions)
        self.rebuild_enemy_spatial_index()
        self.melee_attack_system.update(
            self.ecm,
            dt,
            self.tile_map,
            self.enemy_spatial_index,
        )
        self.enemy_death_system.update(self.ecm, self.get_current_region_id())
        self.enemy_attack_system.update(self.ecm, dt, self.enemy_spatial_index)
        self.player_death_system.update(self.ecm)

        if not self.is_player_defeated():
            self.capture_system.update(
                self.ecm,
                dt,
                self.get_current_region_id(),
                self.enemy_spatial_index,
            )
            spawned_enemy_ids = self.castle_wave_system.update(
                self.ecm,
                self.entity_factory,
                self.tile_map,
                self.capture_point_ids,
            )
            self.enemy_ids.extend(spawned_enemy_ids)
            self.complete_assault_if_ready()

        self.cleanup_system.update(self.ecm)

    def draw_assault_completed_message(self, screen):
        font = pygame.font.Font(None, 36)
        text_surface = font.render(
            texts.ASSAULT_COMPLETED,
            True,
            (255, 255, 255),
        )
        screen.blit(
            text_surface,
            (
                settings.SCREEN_WIDTH // 2 - text_surface.get_width() // 2,
                settings.SCREEN_HEIGHT - 96,
            ),
        )

    def draw(self, screen: pygame.Surface):
        self.tile_map.draw(screen)
        self.render_system.draw(self.ecm, screen)
        self.render_system.draw_attack_hitboxes(self.ecm, screen)
        self.render_system.draw_enemy_health_bars(self.ecm, screen)
        self.hud.draw(screen, self.ecm, self.ecs_player_id, self.get_castle_title())
        if self.is_player_defeated():
            self.hud.draw_defeat_message(screen, texts.DEFEATED_RESTART)
        if self.assault_completed:
            self.draw_assault_completed_message(screen)
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
