import unittest

import settings
from src.components.components import (
    AttackIntent,
    AttackHitbox,
    CapturePoint,
    ChaseBehavior,
    Collider,
    Enemy,
    EnemyAttackState,
    FacingDirection,
    Health,
    MeleeAttack,
    NPC,
    Outpost,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import (
    CapturePointSettings,
    EnemySettings,
    NPCSettings,
    OutpostSettings,
    PlayerSettings,
)
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
        self.assertTrue(self.ecm.has_component(player, FacingDirection))
        self.assertTrue(self.ecm.has_component(player, AttackHitbox))
        self.assertTrue(self.ecm.has_component(player, MeleeAttack))

        health = self.ecm.get_component(player, Health)
        collider = self.ecm.get_component(player, Collider)
        renderable = self.ecm.get_component(player, Renderable)
        melee_attack = self.ecm.get_component(player, MeleeAttack)
        hitbox = self.ecm.get_component(player, AttackHitbox)

        self.assertEqual(health.current, PlayerSettings.HEALTH)
        self.assertEqual(health.maximum, PlayerSettings.HEALTH)
        self.assertEqual(collider.width, PlayerSettings.SIZE)
        self.assertEqual(collider.height, PlayerSettings.SIZE)
        self.assertLess(collider.width, settings.TILE_SIZE)
        self.assertLess(collider.height, settings.TILE_SIZE)
        self.assertEqual(renderable.width, PlayerSettings.SIZE)
        self.assertEqual(renderable.height, PlayerSettings.SIZE)
        self.assertLess(renderable.width, settings.TILE_SIZE)
        self.assertLess(renderable.height, settings.TILE_SIZE)
        self.assertEqual(renderable.color, PlayerSettings.COLOR)
        self.assertEqual(melee_attack.damage, PlayerSettings.DAMAGE)
        self.assertEqual(melee_attack.attack_range, PlayerSettings.ATTACK_RANGE)
        self.assertEqual(melee_attack.cooldown, PlayerSettings.ATTACK_COOLDOWN)
        self.assertEqual(melee_attack.knockback_distance, PlayerSettings.KNOCKBACK_DISTANCE)
        self.assertEqual(hitbox.width, 0)
        self.assertEqual(hitbox.height, 0)
        self.assertEqual(hitbox.duration, PlayerSettings.ATTACK_HITBOX_DURATION)

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
        self.assertTrue(self.ecm.has_component(enemy, AttackHitbox))
        self.assertTrue(self.ecm.has_component(enemy, EnemyAttackState))
        self.assertFalse(self.ecm.has_component(enemy, PlayerControlled))

        health = self.ecm.get_component(enemy, Health)
        collider = self.ecm.get_component(enemy, Collider)
        renderable = self.ecm.get_component(enemy, Renderable)
        chase = self.ecm.get_component(enemy, ChaseBehavior)
        melee_attack = self.ecm.get_component(enemy, MeleeAttack)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)

        self.assertEqual(health.current, EnemySettings.HEALTH)
        self.assertEqual(health.maximum, EnemySettings.HEALTH)
        self.assertEqual(collider.width, EnemySettings.SIZE)
        self.assertEqual(collider.height, EnemySettings.SIZE)
        self.assertLess(collider.width, settings.TILE_SIZE)
        self.assertLess(collider.height, settings.TILE_SIZE)
        self.assertEqual(renderable.width, EnemySettings.SIZE)
        self.assertEqual(renderable.height, EnemySettings.SIZE)
        self.assertLess(renderable.width, settings.TILE_SIZE)
        self.assertLess(renderable.height, settings.TILE_SIZE)
        self.assertEqual(renderable.color, EnemySettings.COLOR)
        self.assertEqual(chase.speed, EnemySettings.SPEED)
        self.assertEqual(chase.detection_radius, EnemySettings.DETECTION_RADIUS)
        self.assertEqual(melee_attack.damage, EnemySettings.DAMAGE)
        self.assertEqual(melee_attack.attack_range, EnemySettings.ATTACK_RANGE)
        self.assertEqual(melee_attack.cooldown, EnemySettings.ATTACK_COOLDOWN)
        self.assertEqual(hitbox.width, 0)
        self.assertEqual(hitbox.height, 0)
        self.assertEqual(hitbox.duration, EnemySettings.ATTACK_HITBOX_DURATION)
        self.assertFalse(hitbox.active)
        self.assertFalse(attack_state.pending)
        self.assertEqual(attack_state.windup_duration, EnemySettings.ATTACK_WINDUP_DURATION)

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

    def test_create_npc(self):
        outpost_id = 10
        npc = self.entity_factory.create_npc(
            x=120,
            y=160,
            quest_id="clear_old_ruins_outpost",
            required_outpost_id=outpost_id,
        )

        self.assertIn(npc, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(npc, Position))
        self.assertTrue(self.ecm.has_component(npc, Renderable))
        self.assertTrue(self.ecm.has_component(npc, NPC))
        self.assertFalse(self.ecm.has_component(npc, Collider))
        self.assertFalse(self.ecm.has_component(npc, Health))

        renderable = self.ecm.get_component(npc, Renderable)
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertEqual(renderable.width, NPCSettings.SIZE)
        self.assertEqual(renderable.height, NPCSettings.SIZE)
        self.assertEqual(renderable.color, NPCSettings.ACTIVE_COLOR)
        self.assertEqual(npc_component.interaction_radius, NPCSettings.INTERACTION_RADIUS)
        self.assertEqual(npc_component.quest_id, "clear_old_ruins_outpost")
        self.assertEqual(npc_component.required_outpost_id, outpost_id)
        self.assertFalse(npc_component.quest_completed)

    def test_create_capture_point(self):
        capture_point = self.entity_factory.create_capture_point(x=180, y=220)

        self.assertIn(capture_point, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(capture_point, Position))
        self.assertTrue(self.ecm.has_component(capture_point, Renderable))
        self.assertTrue(self.ecm.has_component(capture_point, CapturePoint))
        self.assertFalse(self.ecm.has_component(capture_point, Collider))
        self.assertFalse(self.ecm.has_component(capture_point, Health))

        renderable = self.ecm.get_component(capture_point, Renderable)
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(renderable.width, CapturePointSettings.SIZE)
        self.assertEqual(renderable.height, CapturePointSettings.SIZE)
        self.assertEqual(renderable.color, CapturePointSettings.ENEMY_COLOR)
        self.assertEqual(capture_point_component.radius, CapturePointSettings.RADIUS)
        self.assertEqual(capture_point_component.progress, 0)
        self.assertEqual(capture_point_component.owner, "enemy")
        self.assertFalse(capture_point_component.captured)


if __name__ == "__main__":
    unittest.main()
