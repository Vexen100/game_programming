import unittest

import pygame
import settings
from src.components.components import (
    AttackHitbox,
    CapturePoint,
    ChaseBehavior,
    Enemy,
    EnemyAttackState,
    Health,
    MeleeAttack,
    PatrolRoute,
    PlayerControlled,
    PlayerDefeated,
    Position,
)
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.events.game_events import RegionLiberatedEvent
from src.algorithms.bsp import RectInt
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.systems.region_liberation_system import RegionLiberationSystem
from src.ui import texts
from src.world.castle_generator import CastleLayout
from src.world.tile_types import FLOOR, WALL


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None
        self.pause_requested_scene_id = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id

    def request_pause(self, scene_id):
        self.pause_requested_scene_id = scene_id


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class FakeInputManager:
    def was_pressed(self, action):
        return False

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeRestartInputManager:
    def was_pressed(self, action):
        return action == settings.RESTART

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeWorldMapInputManager:
    def was_pressed(self, action):
        return action == settings.OPEN_WORLD_MAP

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeAttackInputManager:
    def was_pressed(self, action):
        return action == settings.ATTACK

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakePauseInputManager:
    def was_pressed(self, action):
        return action == settings.PAUSE

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class TestCastleAssaultScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def create_test_castle_layout(self):
        width = 14
        height = 10
        matrix = []

        for tile_y in range(height):
            row = []
            for tile_x in range(width):
                if tile_x == 0 or tile_y == 0 or tile_x == width - 1 or tile_y == height - 1:
                    row.append(WALL)
                else:
                    row.append(FLOOR)
            matrix.append(row)

        return CastleLayout(
            matrix=matrix,
            rooms=[RectInt(1, 1, width - 2, height - 2)],
            corridors=[],
            entrance_tile=(2, 2),
            final_room_tile=(11, 7),
            capture_point_tiles=[(5, 2), (9, 6)],
            enemy_spawn_tiles=[(4, 4), (7, 4), (10, 4)],
            wave_spawn_tiles=[(3, 7), (8, 7)],
            seed=123,
        )

    def get_position_tile(self, scene, entity_id):
        position = scene.ecm.get_component(entity_id, Position)
        return scene.tile_map.coord_pixels_to_tile(position.x, position.y)

    def get_layout_important_tiles(self, layout):
        return [
            layout.entrance_tile,
            layout.final_room_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

    def test_castle_assault_scene_creates_without_game_state(self):
        scene = CastleAssaultScene()

        self.assertEqual(scene.get_castle_title(), "Штурм замка")
        self.assertFalse(scene.assault_completed)

    def test_castle_assault_scene_uses_castle_layout_matrix(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)

        self.assertEqual(scene.tile_map.width, len(layout.matrix[0]))
        self.assertEqual(scene.tile_map.height, len(layout.matrix))
        self.assertEqual(scene.tile_map.matrix, layout.matrix)

    def test_player_spawns_at_layout_entrance(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)

        self.assertEqual(scene.get_entity_tile(scene.ecs_player_id), layout.entrance_tile)

    def test_capture_points_spawn_from_layout(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)
        capture_point_tiles = [
            self.get_position_tile(scene, capture_point_id)
            for capture_point_id in scene.capture_point_ids
        ]

        self.assertEqual(capture_point_tiles, layout.capture_point_tiles)

    def test_enemies_spawn_from_layout(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)
        enemy_tiles = [
            scene.get_entity_tile(enemy_id)
            for enemy_id in scene.enemy_ids
        ]

        self.assertEqual(len(scene.enemy_ids), len(layout.enemy_spawn_tiles))
        self.assertEqual(enemy_tiles, layout.enemy_spawn_tiles)

    def test_wave_spawn_tiles_come_from_layout(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)

        self.assertEqual(scene.castle_wave_spawn_tiles, layout.wave_spawn_tiles)
        self.assertEqual(scene.castle_wave_system.spawn_tiles, layout.wave_spawn_tiles)

    def test_final_room_tile_is_reachable_in_scene_validation(self):
        layout = self.create_test_castle_layout()

        scene = CastleAssaultScene(castle_layout=layout)

        self.assertEqual(scene.final_room_tile, layout.final_room_tile)
        scene.validate_castle_layout()

    def test_restart_keeps_same_layout(self):
        scene = CastleAssaultScene(castle_seed=12345)
        layout_matrix = [row[:] for row in scene.castle_layout.matrix]
        tile_map_matrix = [row[:] for row in scene.tile_map.matrix]
        important_tiles = self.get_layout_important_tiles(scene.castle_layout)

        scene.restart_castle()

        self.assertEqual(scene.castle_layout.matrix, layout_matrix)
        self.assertEqual(scene.tile_map.matrix, tile_map_matrix)
        self.assertEqual(
            self.get_layout_important_tiles(scene.castle_layout),
            important_tiles,
        )

    def test_same_region_seed_produces_same_castle_layout(self):
        first_game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        first_game_state.set_current_region("old_ruins")
        second_game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        second_game_state.set_current_region("old_ruins")

        first_scene = CastleAssaultScene(game_state=first_game_state)
        second_scene = CastleAssaultScene(game_state=second_game_state)

        self.assertEqual(first_scene.castle_layout.matrix, second_scene.castle_layout.matrix)
        self.assertEqual(
            self.get_layout_important_tiles(first_scene.castle_layout),
            self.get_layout_important_tiles(second_scene.castle_layout),
        )

    def test_different_region_seed_can_produce_different_castle_layout(self):
        first_scene = CastleAssaultScene(castle_seed=1)
        second_scene = CastleAssaultScene(castle_seed=2)

        self.assertNotEqual(first_scene.castle_layout.matrix, second_scene.castle_layout.matrix)

    def test_invalid_layout_raises_value_error(self):
        layout = self.create_test_castle_layout()
        final_x, final_y = layout.final_room_tile
        layout.matrix[final_y][final_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            CastleAssaultScene(castle_layout=layout)

    def test_castle_assault_scene_creates_player_and_enemy(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "ecs_player_id"))
        self.assertTrue(hasattr(scene, "enemy_ids"))
        self.assertTrue(hasattr(scene, "enemy_id"))
        self.assertEqual(len(scene.enemy_ids), 3)
        self.assertEqual(scene.enemy_id, scene.enemy_ids[0])
        self.assertEqual(len(scene.ecm.alive_entities), 6)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))

        for enemy_id in scene.enemy_ids:
            self.assertTrue(scene.ecm.has_component(enemy_id, Enemy))
            self.assertTrue(scene.ecm.has_component(enemy_id, Position))
            self.assertTrue(scene.ecm.has_component(enemy_id, Health))
            self.assertTrue(scene.ecm.has_component(enemy_id, ChaseBehavior))
            self.assertTrue(scene.ecm.has_component(enemy_id, MeleeAttack))
            self.assertTrue(scene.ecm.has_component(enemy_id, AttackHitbox))
            self.assertTrue(scene.ecm.has_component(enemy_id, EnemyAttackState))
            self.assertTrue(scene.ecm.has_component(enemy_id, PatrolRoute))

    def test_castle_assault_scene_has_capture_system(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "capture_system"))

    def test_castle_assault_scene_has_castle_wave_system(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "castle_wave_system"))

    def test_castle_assault_scene_has_wave_spawn_tiles(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "castle_wave_spawn_tiles"))
        self.assertGreater(len(scene.castle_wave_spawn_tiles), 0)

    def test_castle_assault_scene_creates_capture_points(self):
        scene = CastleAssaultScene()

        self.assertEqual(len(scene.capture_point_ids), 2)
        for capture_point_id in scene.capture_point_ids:
            self.assertTrue(scene.ecm.has_component(capture_point_id, CapturePoint))

    def test_castle_assault_scene_has_gameplay_systems(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "player_input_system"))
        self.assertTrue(hasattr(scene, "player_attack_input_system"))
        self.assertTrue(hasattr(scene, "enemy_chase_system"))
        self.assertTrue(hasattr(scene, "movement_system"))
        self.assertTrue(hasattr(scene, "collision_system"))
        self.assertTrue(hasattr(scene, "melee_attack_system"))
        self.assertTrue(hasattr(scene, "enemy_death_system"))
        self.assertTrue(hasattr(scene, "enemy_attack_system"))
        self.assertTrue(hasattr(scene, "player_death_system"))
        self.assertTrue(hasattr(scene, "cleanup_system"))
        self.assertTrue(hasattr(scene, "render_system"))

    def test_restart_castle_resets_assault_completed(self):
        scene = CastleAssaultScene()
        scene.assault_completed = True

        scene.restart_castle()

        self.assertFalse(scene.assault_completed)

    def test_player_and_enemy_spawn_on_floor(self):
        scene = CastleAssaultScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)

        player_tile_x, player_tile_y = scene.tile_map.coord_pixels_to_tile(
            player_position.x,
            player_position.y,
        )

        self.assertEqual(scene.tile_map.matrix[player_tile_y][player_tile_x], FLOOR)

        for enemy_id in scene.enemy_ids:
            enemy_position = scene.ecm.get_component(enemy_id, Position)
            enemy_tile_x, enemy_tile_y = scene.tile_map.coord_pixels_to_tile(
                enemy_position.x,
                enemy_position.y,
            )

            self.assertEqual(scene.tile_map.matrix[enemy_tile_y][enemy_tile_x], FLOOR)

    def test_enemies_do_not_spawn_on_player_or_capture_points(self):
        scene = CastleAssaultScene()
        player_tile = scene.get_entity_tile(scene.ecs_player_id)
        capture_point_tiles = {
            scene.get_entity_tile(capture_point_id)
            for capture_point_id in scene.capture_point_ids
        }

        for enemy_id in scene.enemy_ids:
            enemy_tile = scene.get_entity_tile(enemy_id)

            self.assertNotEqual(enemy_tile, player_tile)
            self.assertNotIn(enemy_tile, capture_point_tiles)

    def test_capture_points_spawn_on_floor(self):
        scene = CastleAssaultScene()

        for capture_point_id in scene.capture_point_ids:
            capture_point_position = scene.ecm.get_component(capture_point_id, Position)
            tile_x, tile_y = scene.tile_map.coord_pixels_to_tile(
                capture_point_position.x,
                capture_point_position.y,
            )

            self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

    def test_validate_castle_layout_does_not_fail_on_procedural_map(self):
        scene = CastleAssaultScene()

        scene.validate_castle_layout()

    def test_validate_castle_layout_does_not_fail_on_wave_spawn_tiles(self):
        scene = CastleAssaultScene()

        for tile_x, tile_y in scene.castle_wave_spawn_tiles:
            self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

        scene.validate_castle_layout()

    def test_castle_patrol_tiles_are_floor(self):
        scene = CastleAssaultScene()

        for enemy_id in scene.enemy_ids:
            patrol_route = scene.ecm.get_component(enemy_id, PatrolRoute)
            self.assertIsNotNone(patrol_route)

            for tile_x, tile_y in patrol_route.patrol_tiles:
                self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

    def test_castle_layout_corridors_are_floor(self):
        scene = CastleAssaultScene()

        for corridor in scene.castle_layout.corridors:
            for tile_x, tile_y in corridor:
                self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

    def test_get_entity_tile_returns_player_tile_coordinates(self):
        scene = CastleAssaultScene()

        self.assertEqual(
            scene.get_entity_tile(scene.ecs_player_id),
            scene.castle_layout.entrance_tile,
        )

    def test_validate_castle_layout_raises_if_capture_point_is_unreachable(self):
        scene = CastleAssaultScene()
        capture_point_id = scene.capture_point_ids[0]
        tile_x, tile_y = scene.get_entity_tile(capture_point_id)

        for wall_x, wall_y in (
            (tile_x + 1, tile_y),
            (tile_x - 1, tile_y),
            (tile_x, tile_y + 1),
            (tile_x, tile_y - 1),
        ):
            scene.tile_map.matrix[wall_y][wall_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_castle_layout()

    def test_validate_castle_layout_raises_if_enemy_is_unreachable(self):
        scene = CastleAssaultScene()
        enemy_id = scene.enemy_ids[0]
        tile_x, tile_y = scene.get_entity_tile(enemy_id)

        for wall_x, wall_y in (
            (tile_x + 1, tile_y),
            (tile_x - 1, tile_y),
            (tile_x, tile_y + 1),
            (tile_x, tile_y - 1),
        ):
            scene.tile_map.matrix[wall_y][wall_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_castle_layout()

    def test_validate_castle_layout_raises_if_wave_spawn_tile_is_blocked(self):
        scene = CastleAssaultScene()
        tile_x, tile_y = scene.castle_wave_spawn_tiles[0]
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_castle_layout()

    def test_validate_castle_layout_raises_if_player_spawn_is_blocked(self):
        scene = CastleAssaultScene()
        tile_x, tile_y = scene.get_entity_tile(scene.ecs_player_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_castle_layout()

    def test_get_castle_title_without_game_state(self):
        scene = CastleAssaultScene()

        self.assertEqual(scene.get_castle_title(), "Штурм замка")

    def test_get_castle_title_uses_current_region_name(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = CastleAssaultScene(game_state)

        self.assertEqual(scene.get_castle_title(), "Штурм: Old Ruins")

    def test_open_world_map_requests_world_map_scene(self):
        scene = CastleAssaultScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_open_world_map_without_manager_does_not_crash(self):
        scene = CastleAssaultScene()

        scene.update(0.1, FakeWorldMapInputManager())

    def test_pause_requests_pause_scene(self):
        scene = CastleAssaultScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakePauseInputManager())

        self.assertEqual(scene.manager.pause_requested_scene_id, settings.PAUSE_SCENE)

    def test_pause_skips_gameplay_update(self):
        scene = CastleAssaultScene()
        scene.manager = FakeSceneManager()

        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        scene.update(0.1, FakePauseInputManager())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_pause_without_manager_does_not_crash(self):
        scene = CastleAssaultScene()

        scene.update(0.1, FakePauseInputManager())

    def test_update_with_los_and_pathfinding_cache_does_not_crash(self):
        scene = CastleAssaultScene()

        scene.update(0.1, FakeInputManager())

        self.assertTrue(hasattr(scene.enemy_chase_system, "cached_paths"))
        self.assertTrue(hasattr(scene.enemy_chase_system, "last_seen_player_tiles"))

    def test_update_can_activate_enemy_attack_hitbox(self):
        scene = CastleAssaultScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        attack_state = scene.ecm.get_component(scene.enemy_id, EnemyAttackState)
        hitbox = scene.ecm.get_component(scene.enemy_id, AttackHitbox)

        player_position.x = settings.TILE_SIZE * 9
        player_position.y = settings.TILE_SIZE * 3
        enemy_position.x = settings.TILE_SIZE * 10
        enemy_position.y = settings.TILE_SIZE * 3
        old_health = player_health.current

        scene.update(0.1, FakeInputManager())

        self.assertEqual(player_health.current, old_health)
        self.assertTrue(attack_state.pending)
        self.assertTrue(hitbox.active)

    def test_player_near_capture_point_increases_progress(self):
        scene = CastleAssaultScene()
        capture_point_id = scene.capture_point_ids[0]
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        capture_point_position = scene.ecm.get_component(capture_point_id, Position)
        capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)

        player_position.x = capture_point_position.x
        player_position.y = capture_point_position.y

        scene.capture_system.update(scene.ecm, dt=1, region_id=scene.get_current_region_id())

        self.assertGreater(capture_point.progress, 0)

    def test_castle_rebuild_enemy_spatial_index_creates_index(self):
        scene = CastleAssaultScene()
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        scene.rebuild_enemy_spatial_index()

        self.assertIsNotNone(scene.enemy_spatial_index)
        self.assertIn(
            scene.enemy_id,
            scene.enemy_spatial_index.query_rect(
                enemy_position.x,
                enemy_position.y,
                settings.TILE_SIZE,
                settings.TILE_SIZE,
            ),
        )

    def test_capture_system_blocks_progress_with_scene_spatial_index(self):
        scene = CastleAssaultScene()
        capture_point_id = scene.capture_point_ids[0]
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        capture_point_position = scene.ecm.get_component(capture_point_id, Position)
        capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        player_position.x = capture_point_position.x
        player_position.y = capture_point_position.y
        enemy_position.x = capture_point_position.x
        enemy_position.y = capture_point_position.y
        scene.rebuild_enemy_spatial_index()

        scene.capture_system.update(
            scene.ecm,
            dt=1,
            region_id=scene.get_current_region_id(),
            enemy_spatial_index=scene.enemy_spatial_index,
        )

        self.assertEqual(capture_point.progress, 0)

    def test_defeated_player_does_not_capture_point(self):
        scene = CastleAssaultScene()
        capture_point_id = scene.capture_point_ids[0]
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        capture_point_position = scene.ecm.get_component(capture_point_id, Position)
        capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)

        player_position.x = capture_point_position.x
        player_position.y = capture_point_position.y
        scene.ecm.add_component(scene.ecs_player_id, PlayerDefeated())

        scene.capture_system.update(scene.ecm, dt=1, region_id=scene.get_current_region_id())

        self.assertEqual(capture_point.progress, 0)

    def test_complete_assault_if_ready_sets_assault_completed(self):
        scene = CastleAssaultScene()

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True

        scene.complete_assault_if_ready()

        self.assertTrue(scene.assault_completed)

    def test_complete_assault_if_ready_does_not_complete_with_one_capture_point(self):
        scene = CastleAssaultScene()
        capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        capture_point.captured = True

        scene.complete_assault_if_ready()

        self.assertFalse(scene.assault_completed)

    def test_update_skips_gameplay_when_assault_completed(self):
        scene = CastleAssaultScene()
        scene.assault_completed = True
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        scene.update(1, FakeInputManager())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_world_map_request_works_when_assault_completed(self):
        scene = CastleAssaultScene()
        scene.assault_completed = True
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_pause_request_works_when_assault_completed(self):
        scene = CastleAssaultScene()
        scene.assault_completed = True
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakePauseInputManager())

        self.assertEqual(scene.manager.pause_requested_scene_id, settings.PAUSE_SCENE)

    def test_captured_non_final_capture_point_spawns_reinforcements(self):
        scene = CastleAssaultScene()
        capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        capture_point.captured = True
        capture_point.owner = "player"

        scene.update(0, FakeInputManager())

        self.assertEqual(len(scene.enemy_ids), 5)
        for enemy_id in scene.enemy_ids:
            self.assertTrue(scene.ecm.has_component(enemy_id, Enemy))

    def test_wave_spawned_enemies_enter_spatial_index_on_next_update(self):
        scene = CastleAssaultScene()
        capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        capture_point.captured = True
        capture_point.owner = "player"

        scene.update(0, FakeInputManager())
        spawned_enemy_id = scene.enemy_ids[-1]
        spawned_enemy_position = scene.ecm.get_component(spawned_enemy_id, Position)

        self.assertNotIn(
            spawned_enemy_id,
            scene.enemy_spatial_index.query_rect(
                spawned_enemy_position.x,
                spawned_enemy_position.y,
                settings.TILE_SIZE,
                settings.TILE_SIZE,
            ),
        )

        scene.update(0, FakeInputManager())

        self.assertIn(
            spawned_enemy_id,
            scene.enemy_spatial_index.query_rect(
                spawned_enemy_position.x,
                spawned_enemy_position.y,
                settings.TILE_SIZE,
                settings.TILE_SIZE,
            ),
        )

    def test_repeated_update_does_not_spawn_second_wave_for_same_capture_point(self):
        scene = CastleAssaultScene()
        capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        capture_point.captured = True
        capture_point.owner = "player"

        scene.update(0, FakeInputManager())
        scene.update(0, FakeInputManager())

        self.assertEqual(len(scene.enemy_ids), 5)

    def test_all_capture_points_captured_before_update_do_not_spawn_wave(self):
        scene = CastleAssaultScene()

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True
            capture_point.owner = "player"

        scene.update(0, FakeInputManager())

        self.assertEqual(len(scene.enemy_ids), 3)
        self.assertTrue(scene.assault_completed)

    def test_restart_resets_castle_wave_state(self):
        scene = CastleAssaultScene()
        first_capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        first_capture_point.captured = True
        first_capture_point.owner = "player"

        scene.update(0, FakeInputManager())

        self.assertEqual(len(scene.enemy_ids), 5)

        scene.restart_castle()
        second_first_capture_point = scene.ecm.get_component(
            scene.capture_point_ids[0],
            CapturePoint,
        )
        second_first_capture_point.captured = True
        second_first_capture_point.owner = "player"

        self.assertEqual(len(scene.enemy_ids), 3)

        scene.update(0, FakeInputManager())

        self.assertEqual(len(scene.enemy_ids), 5)

    def test_all_capture_points_publish_region_liberated_event(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = FakeEventBus()
        scene = CastleAssaultScene(game_state, event_bus)

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True

        scene.capture_system.update(scene.ecm, dt=0.1, region_id=scene.get_current_region_id())

        self.assertTrue(
            any(isinstance(event, RegionLiberatedEvent) for event in event_bus.events)
        )

    def test_final_capture_update_completes_assault_and_publishes_liberation_event(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = FakeEventBus()
        scene = CastleAssaultScene(game_state, event_bus)

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True

        scene.update(0, FakeInputManager())

        self.assertTrue(scene.assault_completed)
        self.assertTrue(
            any(isinstance(event, RegionLiberatedEvent) for event in event_bus.events)
        )

    def test_existing_castle_assault_liberation_flow_still_works(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = FakeEventBus()
        scene = CastleAssaultScene(game_state, event_bus)

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True
            capture_point.owner = "player"

        scene.update(0, FakeInputManager())

        self.assertTrue(scene.assault_completed)
        self.assertTrue(
            any(isinstance(event, RegionLiberatedEvent) for event in event_bus.events)
        )

    def test_region_liberation_event_updates_game_state(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        region_liberation_system = RegionLiberationSystem(game_state)
        region_liberation_system.subscribe(event_bus)
        scene = CastleAssaultScene(game_state, event_bus)

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True

        scene.capture_system.update(scene.ecm, dt=0.1, region_id=scene.get_current_region_id())
        region = game_state.get_region("old_ruins")

        self.assertTrue(region.liberated)

    def test_final_capture_update_completes_assault_and_updates_game_state(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        region_liberation_system = RegionLiberationSystem(game_state)
        region_liberation_system.subscribe(event_bus)
        scene = CastleAssaultScene(game_state, event_bus)

        for capture_point_id in scene.capture_point_ids:
            capture_point = scene.ecm.get_component(capture_point_id, CapturePoint)
            capture_point.captured = True

        scene.update(0, FakeInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(scene.assault_completed)
        self.assertTrue(region.liberated)

    def test_update_after_victory_does_not_spawn_new_wave(self):
        scene = CastleAssaultScene()
        first_capture_point = scene.ecm.get_component(scene.capture_point_ids[0], CapturePoint)
        first_capture_point.captured = True
        first_capture_point.owner = "player"

        scene.update(0, FakeInputManager())

        second_capture_point = scene.ecm.get_component(scene.capture_point_ids[1], CapturePoint)
        second_capture_point.captured = True
        second_capture_point.owner = "player"

        scene.update(0, FakeInputManager())
        enemy_count_after_victory = len(scene.enemy_ids)
        scene.update(0, FakeInputManager())

        self.assertTrue(scene.assault_completed)
        self.assertEqual(len(scene.enemy_ids), enemy_count_after_victory)

    def test_restart_after_defeat_resets_castle(self):
        scene = CastleAssaultScene()
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        old_ecm = scene.ecm

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

        scene.update(0.1, FakeRestartInputManager())
        new_player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        self.assertIsNot(scene.ecm, old_ecm)
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertEqual(new_player_health.current, new_player_health.maximum)
        self.assertEqual(len(scene.enemy_ids), 3)
        self.assertEqual(scene.enemy_id, scene.enemy_ids[0])
        self.assertEqual(len(scene.ecm.alive_entities), 6)

    def test_draw_does_not_crash(self):
        scene = CastleAssaultScene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)

    def test_draw_does_not_crash_when_assault_completed(self):
        scene = CastleAssaultScene()
        scene.assault_completed = True
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)


if __name__ == "__main__":
    unittest.main()
