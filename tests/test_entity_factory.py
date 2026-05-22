import unittest

from src.components.components import (
    AttackIntent,
    ChaseBehavior,
    Collider,
    Enemy,
    Health,
    MeleeAttack,
    Outpost,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import EnemySettings, OutpostSettings, PlayerSettings
from src.entities.entity_factory import EntityFactory


class TestEntityFactory(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)

    def test_create_player(self):
        player = self.entity_factory.create_player(x=100, y=100)

        self.assertIn(player, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(player, Position))
        self.assertTrue(self.ecm.has_component(player, Velocity))
        self.assertTrue(self.ecm.has_component(player, Collider))
        self.assertTrue(self.ecm.has_component(player, Renderable))
        self.assertTrue(self.ecm.has_component(player, Health))
        self.assertTrue(self.ecm.has_component(player, PlayerControlled))
        self.assertTrue(self.ecm.has_component(player, AttackIntent))
        self.assertTrue(self.ecm.has_component(player, MeleeAttack))

        health = self.ecm.get_component(player, Health)
        collider = self.ecm.get_component(player, Collider)
        renderable = self.ecm.get_component(player, Renderable)
        melee_attack = self.ecm.get_component(player, MeleeAttack)

        self.assertEqual(health.current, PlayerSettings.HEALTH)
        self.assertEqual(health.maximum, PlayerSettings.HEALTH)
        self.assertEqual(collider.width, PlayerSettings.SIZE)
        self.assertEqual(collider.height, PlayerSettings.SIZE)
        self.assertEqual(renderable.color, PlayerSettings.COLOR)
        self.assertEqual(melee_attack.damage, PlayerSettings.DAMAGE)
        self.assertEqual(melee_attack.attack_range, PlayerSettings.ATTACK_RANGE)
        self.assertEqual(melee_attack.cooldown, PlayerSettings.ATTACK_COOLDOWN)

    def test_create_enemy(self):
        enemy = self.entity_factory.create_enemy(x=200, y=200)

        self.assertIn(enemy, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(enemy, Position))
        self.assertTrue(self.ecm.has_component(enemy, Velocity))
        self.assertTrue(self.ecm.has_component(enemy, Collider))
        self.assertTrue(self.ecm.has_component(enemy, Renderable))
        self.assertTrue(self.ecm.has_component(enemy, Health))
        self.assertTrue(self.ecm.has_component(enemy, Enemy))
        self.assertTrue(self.ecm.has_component(enemy, ChaseBehavior))
        self.assertTrue(self.ecm.has_component(enemy, MeleeAttack))
        self.assertFalse(self.ecm.has_component(enemy, PlayerControlled))

        health = self.ecm.get_component(enemy, Health)
        collider = self.ecm.get_component(enemy, Collider)
        renderable = self.ecm.get_component(enemy, Renderable)
        chase = self.ecm.get_component(enemy, ChaseBehavior)
        melee_attack = self.ecm.get_component(enemy, MeleeAttack)

        self.assertEqual(health.current, EnemySettings.HEALTH)
        self.assertEqual(health.maximum, EnemySettings.HEALTH)
        self.assertEqual(collider.width, EnemySettings.SIZE)
        self.assertEqual(collider.height, EnemySettings.SIZE)
        self.assertEqual(renderable.color, EnemySettings.COLOR)
        self.assertEqual(chase.speed, EnemySettings.SPEED)
        self.assertEqual(chase.detection_radius, EnemySettings.DETECTION_RADIUS)
        self.assertEqual(melee_attack.damage, EnemySettings.DAMAGE)
        self.assertEqual(melee_attack.attack_range, EnemySettings.ATTACK_RANGE)
        self.assertEqual(melee_attack.cooldown, EnemySettings.ATTACK_COOLDOWN)

    def test_create_outpost(self):
        outpost = self.entity_factory.create_outpost(x=300, y=200)

        self.assertIn(outpost, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(outpost, Position))
        self.assertTrue(self.ecm.has_component(outpost, Renderable))
        self.assertTrue(self.ecm.has_component(outpost, Outpost))
        self.assertFalse(self.ecm.has_component(outpost, Collider))
        self.assertFalse(self.ecm.has_component(outpost, Health))

        renderable = self.ecm.get_component(outpost, Renderable)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertEqual(renderable.width, OutpostSettings.SIZE)
        self.assertEqual(renderable.height, OutpostSettings.SIZE)
        self.assertEqual(renderable.color, OutpostSettings.ENEMY_COLOR)
        self.assertEqual(outpost_component.radius, OutpostSettings.RADIUS)
        self.assertFalse(outpost_component.cleared)


if __name__ == "__main__":
    unittest.main()
