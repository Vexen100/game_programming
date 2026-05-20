import unittest

from src.components.components import (
    Collider,
    Dead,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    Position,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.enemy_attack_system import EnemyAttackSystem


class TestEnemyAttackSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = EnemyAttackSystem()

    def create_player(self, x=0, y=0, health=100):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        self.ecm.add_component(player, Collider(width=32, height=32, solid=True))
        self.ecm.add_component(player, Health(current=health, maximum=100))
        return player

    def create_enemy(self, x=40, y=0, damage=8, attack_range=40, cooldown=0.8):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Position(x, y))
        self.ecm.add_component(enemy, Collider(width=32, height=32, solid=True))
        self.ecm.add_component(
            enemy,
            MeleeAttack(
                damage=damage,
                attack_range=attack_range,
                cooldown=cooldown,
            ),
        )
        return enemy

    def test_enemy_damages_player_in_range(self):
        player = self.create_player()
        self.create_enemy()

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 92)

    def test_enemy_does_not_damage_player_out_of_range(self):
        player = self.create_player()
        self.create_enemy(x=100)

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 100)

    def test_enemy_does_not_repeat_attack_during_cooldown(self):
        player = self.create_player()
        self.create_enemy()

        self.system.update(self.ecm, dt=0.1)
        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 92)

    def test_cooldown_timer_decreases_by_dt(self):
        self.create_player()
        enemy = self.create_enemy(x=100)
        attack = self.ecm.get_component(enemy, MeleeAttack)
        attack.cooldown_timer = 0.8

        self.system.update(self.ecm, dt=0.1)

        self.assertAlmostEqual(attack.cooldown_timer, 0.7)

    def test_player_health_does_not_go_below_zero(self):
        player = self.create_player(health=5)
        self.create_enemy(damage=20)

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 0)

    def test_dead_enemy_does_not_attack_player(self):
        player = self.create_player()
        enemy = self.create_enemy()
        self.ecm.add_component(enemy, Dead())

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 100)

    def test_update_without_player_does_not_crash(self):
        self.create_enemy()

        self.system.update(self.ecm, dt=0.1)

    def test_update_without_enemies_does_not_crash(self):
        self.create_player()

        self.system.update(self.ecm, dt=0.1)


if __name__ == "__main__":
    unittest.main()
