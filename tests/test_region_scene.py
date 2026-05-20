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
        self.assertEqual(len(scene.ecm.alive_entities), 2)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackIntent))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))

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


if __name__ == "__main__":
    unittest.main()
