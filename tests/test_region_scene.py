import unittest

import pygame
import settings

from src.components.components import (
    AttackIntent,
    ChaseBehavior,
    Enemy,
    Health,
    MeleeAttack,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
)
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id


class FakeInputManager:
    def was_pressed(self, action):
        return False

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeAttackInputManager:
    def was_pressed(self, action):
        return action == settings.ATTACK

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


class TestRegionScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_region_scene_creates_player_and_enemy(self):
        scene = RegionScene()

        self.assertTrue(hasattr(scene, "ecs_player_id"))
        self.assertTrue(hasattr(scene, "enemy_id"))
        self.assertTrue(hasattr(scene, "enemy_chase_system"))
        self.assertTrue(hasattr(scene, "player_attack_input_system"))
        self.assertTrue(hasattr(scene, "melee_attack_system"))
        self.assertTrue(hasattr(scene, "enemy_death_system"))
        self.assertTrue(hasattr(scene, "outpost_system"))
        self.assertTrue(hasattr(scene, "enemy_attack_system"))
        self.assertTrue(hasattr(scene, "player_death_system"))
        self.assertTrue(hasattr(scene, "cleanup_system"))
        self.assertEqual(len(scene.ecm.alive_entities), 3)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackIntent))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.outpost_id, Outpost))

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.outpost_id, Position))

    def test_region_scene_update_moves_enemy_towards_player(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_enemy_x = enemy_position.x
        old_enemy_y = enemy_position.y

        scene.update(0.1, FakeInputManager())

        self.assertLess(enemy_position.x, old_enemy_x)
        self.assertEqual(enemy_position.y, old_enemy_y)

    def test_region_scene_update_player_attack_damages_enemy(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_health = enemy_health.current

        scene.update(0.1, FakeAttackInputManager())

        self.assertLess(enemy_health.current, old_health)

    def test_region_scene_update_removes_dead_enemy_after_attack(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())

        self.assertNotIn(scene.enemy_id, scene.ecm.alive_entities)

    def test_region_scene_update_enemy_attack_damages_player(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_health = player_health.current

        scene.update(0.1, FakeInputManager())

        self.assertLess(player_health.current, old_health)

    def test_region_scene_marks_player_defeated_when_health_is_zero(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

    def test_region_scene_does_not_update_gameplay_when_player_defeated(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())

        old_x = player_position.x
        old_y = player_position.y

        scene.update(0.1, FakeInputManager())

        self.assertEqual(player_position.x, old_x)
        self.assertEqual(player_position.y, old_y)

    def test_region_scene_restart_after_defeat_resets_region(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

        scene.update(0.1, FakeRestartInputManager())

        new_player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertEqual(new_player_health.current, new_player_health.maximum)
        self.assertEqual(len(scene.ecm.alive_entities), 3)

    def test_region_scene_uses_current_region_name_from_game_state(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = RegionScene(game_state)

        self.assertEqual(scene.get_region_title(), "Old Ruins")

    def test_region_scene_without_game_state_uses_default_title(self):
        scene = RegionScene()

        self.assertEqual(scene.get_region_title(), "Region")

    def test_region_scene_enemy_death_publishes_influence_event(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())
        region = game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)

    def test_region_scene_open_world_map_requests_world_map_scene(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_region_scene_open_world_map_skips_gameplay_update(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_region_scene_open_world_map_without_manager_does_not_crash(self):
        scene = RegionScene()

        scene.update(0.1, FakeWorldMapInputManager())

    def test_region_scene_open_world_map_works_when_player_defeated(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_region_influence_is_preserved_when_returning_to_world_map(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())
        region = game_state.get_region("old_ruins")
        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)

        world_map_scene = WorldMapScene(game_state)
        status = world_map_scene.get_region_status_text(region)

        self.assertIn("player 25", status)
        self.assertIn("enemy 75", status)

    def test_region_scene_outpost_clear_changes_influence(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        enemy_position.x = outpost_position.x + outpost.radius + settings.TILE_SIZE
        enemy_position.y = outpost_position.y

        scene.update(0.1, FakeInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(outpost.cleared)
        self.assertEqual(region.player_influence, 50)
        self.assertEqual(region.enemy_influence, 50)
        self.assertTrue(region.assault_unlocked)

    def test_region_scene_outpost_does_not_clear_when_player_health_is_zero(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        enemy_position.x = outpost_position.x + outpost.radius + settings.TILE_SIZE
        enemy_position.y = outpost_position.y
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertFalse(outpost.cleared)
        self.assertEqual(region.player_influence, 0)
        self.assertEqual(region.enemy_influence, 100)


if __name__ == "__main__":
    unittest.main()
