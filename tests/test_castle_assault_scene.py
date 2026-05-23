import unittest

import pygame
import settings
from src.components.components import (
    CapturePoint,
    ChaseBehavior,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    PlayerDefeated,
    Position,
)
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.events.game_events import RegionLiberatedEvent
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.systems.region_liberation_system import RegionLiberationSystem
from src.world.tile_types import FLOOR


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

    def test_castle_assault_scene_creates_without_game_state(self):
        scene = CastleAssaultScene()

        self.assertEqual(scene.get_castle_title(), "Castle Assault")

    def test_castle_assault_scene_creates_player_and_enemy(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "ecs_player_id"))
        self.assertTrue(hasattr(scene, "enemy_id"))
        self.assertEqual(len(scene.ecm.alive_entities), 4)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, MeleeAttack))

    def test_castle_assault_scene_has_capture_system(self):
        scene = CastleAssaultScene()

        self.assertTrue(hasattr(scene, "capture_system"))

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

    def test_player_and_enemy_spawn_on_floor(self):
        scene = CastleAssaultScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        player_tile_x, player_tile_y = scene.tile_map.coord_pixels_to_tile(
            player_position.x,
            player_position.y,
        )
        enemy_tile_x, enemy_tile_y = scene.tile_map.coord_pixels_to_tile(
            enemy_position.x,
            enemy_position.y,
        )

        self.assertEqual(scene.tile_map.matrix[player_tile_y][player_tile_x], FLOOR)
        self.assertEqual(scene.tile_map.matrix[enemy_tile_y][enemy_tile_x], FLOOR)

    def test_capture_points_spawn_on_floor(self):
        scene = CastleAssaultScene()

        for capture_point_id in scene.capture_point_ids:
            capture_point_position = scene.ecm.get_component(capture_point_id, Position)
            tile_x, tile_y = scene.tile_map.coord_pixels_to_tile(
                capture_point_position.x,
                capture_point_position.y,
            )

            self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

    def test_get_castle_title_without_game_state(self):
        scene = CastleAssaultScene()

        self.assertEqual(scene.get_castle_title(), "Castle Assault")

    def test_get_castle_title_uses_current_region_name(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = CastleAssaultScene(game_state)

        self.assertEqual(scene.get_castle_title(), "Old Ruins Assault")

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
        self.assertEqual(len(scene.ecm.alive_entities), 4)

    def test_draw_does_not_crash(self):
        scene = CastleAssaultScene()
        surface = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

        scene.draw(surface)


if __name__ == "__main__":
    unittest.main()
