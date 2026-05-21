import unittest

import pygame
import settings

from src.components.components import (
    AttackIntent,
    ChaseBehavior,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    PlayerDefeated,
    Position,
)
from src.scenes.region_scene import RegionScene


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
        self.assertTrue(hasattr(scene, "enemy_attack_system"))
        self.assertTrue(hasattr(scene, "player_death_system"))
        self.assertTrue(hasattr(scene, "cleanup_system"))
        self.assertEqual(len(scene.ecm.alive_entities), 2)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackIntent))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, MeleeAttack))

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Health))

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
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
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
        self.assertEqual(len(scene.ecm.alive_entities), 2)


if __name__ == "__main__":
    unittest.main()
