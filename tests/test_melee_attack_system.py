import unittest

from src.components.components import (
    AttackIntent,
    Collider,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    Position,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.melee_attack_system import MeleeAttackSystem


class TestMeleeAttackSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = MeleeAttackSystem()

    def create_player(self, x=0, y=0, damage=10, attack_range=48, cooldown=0.4):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        self.ecm.add_component(player, Collider(width=32, height=32, solid=True))
        self.ecm.add_component(player, AttackIntent(requested=True))
        self.ecm.add_component(
            player,
            MeleeAttack(
                damage=damage,
                attack_range=attack_range,
                cooldown=cooldown,
            ),
        )
        return player

    def create_enemy(self, x, y, health=40):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Position(x, y))
        self.ecm.add_component(enemy, Collider(width=32, height=32, solid=True))
        self.ecm.add_component(enemy, Health(current=health, maximum=health))
        return enemy

    def test_attack_damages_enemy_in_range(self):
        self.create_player()
        enemy = self.create_enemy(40, 0)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_attack_does_not_damage_enemy_out_of_range(self):
        self.create_player()
        enemy = self.create_enemy(100, 0)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

    def test_missed_attack_starts_cooldown(self):
        player = self.create_player(attack_range=10)
        self.create_enemy(100, 0)

        self.system.update(self.ecm, dt=0.1)
        attack = self.ecm.get_component(player, MeleeAttack)
        attack_intent = self.ecm.get_component(player, AttackIntent)

        self.assertEqual(attack.cooldown_timer, attack.cooldown)
        self.assertFalse(attack_intent.requested)

    def test_attack_without_targets_starts_cooldown(self):
        player = self.create_player()

        self.system.update(self.ecm, dt=0.1)
        attack = self.ecm.get_component(player, MeleeAttack)
        attack_intent = self.ecm.get_component(player, AttackIntent)

        self.assertEqual(attack.cooldown_timer, attack.cooldown)
        self.assertFalse(attack_intent.requested)

    def test_attack_does_not_repeat_during_cooldown(self):
        player = self.create_player()
        enemy = self.create_enemy(40, 0)

        self.system.update(self.ecm, dt=0.1)
        attack_intent = self.ecm.get_component(player, AttackIntent)
        attack_intent.requested = True
        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_cooldown_timer_decreases_by_dt(self):
        player = self.create_player()
        attack_intent = self.ecm.get_component(player, AttackIntent)
        attack = self.ecm.get_component(player, MeleeAttack)
        attack_intent.requested = False
        attack.cooldown_timer = 0.4

        self.system.update(self.ecm, dt=0.1)

        self.assertAlmostEqual(attack.cooldown_timer, 0.3)

    def test_enemy_health_does_not_go_below_zero(self):
        self.create_player(damage=100)
        enemy = self.create_enemy(40, 0, health=40)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 0)

    def test_attack_damages_closest_enemy(self):
        self.create_player(attack_range=100)
        closest_enemy = self.create_enemy(40, 0)
        far_enemy = self.create_enemy(80, 0)

        self.system.update(self.ecm, dt=0.1)
        closest_health = self.ecm.get_component(closest_enemy, Health)
        far_health = self.ecm.get_component(far_enemy, Health)

        self.assertEqual(closest_health.current, 30)
        self.assertEqual(far_health.current, 40)

    def test_no_attack_intent_does_not_damage(self):
        player = self.create_player()
        enemy = self.create_enemy(40, 0)
        attack_intent = self.ecm.get_component(player, AttackIntent)
        attack_intent.requested = False

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

    def test_attack_intent_resets_after_processing(self):
        player = self.create_player()
        self.create_enemy(40, 0)

        self.system.update(self.ecm, dt=0.1)
        attack_intent = self.ecm.get_component(player, AttackIntent)

        self.assertFalse(attack_intent.requested)


if __name__ == "__main__":
    unittest.main()
