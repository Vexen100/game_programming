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
from src.world.castle_generator import CastleGenerator, CastleLayout


class CastleAssaultScene(BaseScene):
    """Сцена штурма замка"""

    DEFAULT_CASTLE_SEED = 41042
    CASTLE_LAYOUT_WIDTH = settings.SCREEN_WIDTH // settings.TILE_SIZE
    CASTLE_LAYOUT_HEIGHT = settings.SCREEN_HEIGHT // settings.TILE_SIZE + 1

    def __init__(
        self,
        game_state=None,
        event_bus=None,
        castle_layout: CastleLayout | None = None,
        castle_seed=None,
        resource_manager=None,
    ) -> None:
        self.game_state = game_state
        self.event_bus = event_bus
        self.resource_manager = resource_manager
        self.castle_seed = self.resolve_castle_seed(castle_seed)
        self.castle_layout = castle_layout or self.generate_castle_layout()
        self.final_room_tile = self.castle_layout.final_room_tile
        self.capture_point_tiles = list(self.castle_layout.capture_point_tiles)
        self.enemy_spawn_tiles = list(self.castle_layout.enemy_spawn_tiles)
        self.castle_wave_spawn_tiles = list(self.castle_layout.wave_spawn_tiles)
        self.validate_castle_layout_data()
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
        self.render_system = RenderSystem(self.resource_manager)
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None
        self.enemy_spatial_index = None
        self.restart_castle()

    def resolve_castle_seed(self, castle_seed):
        if castle_seed is not None:
            return castle_seed

        region_id = self.get_current_region_id()
        if region_id is None:
            return self.DEFAULT_CASTLE_SEED

        return self.DEFAULT_CASTLE_SEED + self.make_stable_seed_from_text(region_id)

    def make_stable_seed_from_text(self, text):
        total = 0

        for index, character in enumerate(text):
            total += (index + 1) * ord(character)

        return total

    def generate_castle_layout(self):
        return CastleGenerator(
            self.CASTLE_LAYOUT_WIDTH,
            self.CASTLE_LAYOUT_HEIGHT,
            seed=self.castle_seed,
        ).generate()

    def validate_castle_layout_data(self):
        if not self.castle_layout.matrix:
            raise ValueError("Castle layout matrix is empty")

        if not self.capture_point_tiles:
            raise ValueError("Castle layout has no capture point tiles")

        if not self.enemy_spawn_tiles:
            raise ValueError("Castle layout has no enemy spawn tiles")

        if not self.castle_wave_spawn_tiles:
            raise ValueError("Castle layout has no wave spawn tiles")

    def check_entity_components(self, entity_id, entity_name, *component_types):
        """Проверяет, что сущность создана с нужными компонентами"""
        for component_type in component_types:
            component = self.ecm.get_component(entity_id, component_type)
            if component is None:
                raise RuntimeError(
                    f"{entity_name} was created without {component_type.__name__} component"
                )

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
        target_tiles = [self.final_room_tile]

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
        self.tile_map = self.castle_layout.to_tile_map()
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        self.castle_wave_system = CastleWaveSystem(
            spawn_tiles=self.castle_wave_spawn_tiles,
            enemies_per_wave=2,
        )

        player_x, player_y = self.tile_to_pixels(self.castle_layout.entrance_tile)
        self.ecs_player_id = self.entity_factory.create_player(
            x=player_x,
            y=player_y,
        )
        self.check_entity_components(self.ecs_player_id, "ECS player", Position, Health)

        self.enemy_ids = []

        for spawn_tile in self.enemy_spawn_tiles:
            enemy_x, enemy_y = self.tile_to_pixels(spawn_tile)
            self.enemy_ids.append(
                self.entity_factory.create_enemy(
                    x=enemy_x,
                    y=enemy_y,
                )
            )

        self.enemy_id = self.enemy_ids[0]
        self.add_patrol_routes()

        for enemy_id in self.enemy_ids:
            self.check_entity_components(enemy_id, "ECS enemy", Position, Health)

        self.capture_point_ids = []

        for capture_point_tile in self.capture_point_tiles:
            capture_x, capture_y = self.tile_to_pixels(capture_point_tile)
            self.capture_point_ids.append(
                self.entity_factory.create_capture_point(
                    x=capture_x,
                    y=capture_y,
                )
            )

        for capture_point_id in self.capture_point_ids:
            self.check_entity_components(capture_point_id, "CapturePoint", Position, CapturePoint)

        self.validate_castle_layout()
        self.capture_system.reset()
        self.castle_wave_system.reset()

    def tile_to_pixels(self, tile):
        tile_x, tile_y = tile
        return self.tile_map.coord_tile_to_pixels(tile_x, tile_y)

    def rebuild_enemy_spatial_index(self):
        self.enemy_spatial_index = self.spatial_index_system.build_enemy_index(
            self.ecm,
            self.tile_map.width * self.tile_map.tile_size,
            self.tile_map.height * self.tile_map.tile_size,
            settings.TILE_SIZE * 4,
        )

    def add_patrol_routes(self):
        for enemy_id, spawn_tile in zip(self.enemy_ids, self.enemy_spawn_tiles):
            self.ecm.add_component(
                enemy_id,
                PatrolRoute(
                    patrol_tiles=self.create_patrol_tiles(spawn_tile),
                    wait_duration=0.2,
                ),
            )

    def create_patrol_tiles(self, spawn_tile):
        patrol_tiles = []

        for radius in range(0, 4):
            for tile in self.get_square_ring_tiles(spawn_tile, radius):
                if self.tile_map.is_tile_blocked(*tile):
                    continue

                if tile in patrol_tiles:
                    continue

                patrol_tiles.append(tile)

                if len(patrol_tiles) == 4:
                    return patrol_tiles

        return patrol_tiles

    def get_square_ring_tiles(self, center_tile, radius):
        center_x, center_y = center_tile

        if radius == 0:
            return [center_tile]

        tiles = []

        for tile_x in range(center_x - radius, center_x + radius + 1):
            tiles.append((tile_x, center_y - radius))
            tiles.append((tile_x, center_y + radius))

        for tile_y in range(center_y - radius + 1, center_y + radius):
            tiles.append((center_x - radius, tile_y))
            tiles.append((center_x + radius, tile_y))

        return tiles

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
        self.tile_map.draw(screen, resource_manager=self.resource_manager)
        self.render_system.draw(self.ecm, screen)
        self.render_system.draw_attack_hitboxes(self.ecm, screen)
        self.render_system.draw_enemy_health_bars(self.ecm, screen)
        self.hud.draw(screen, self.ecm, self.ecs_player_id, self.get_castle_title())
        if self.is_player_defeated():
            self.hud.draw_defeat_message(screen, texts.DEFEATED_RESTART)
        if self.assault_completed:
            self.draw_assault_completed_message(screen)
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
