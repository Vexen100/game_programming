import unittest

from src.algorithms.uniform_grid import UniformGrid
from src.components.components import (
    AttackHitbox,
    Collider,
    Dead,
    Enemy,
    EnemyAttackState,
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

    def create_enemy(
        self,
        x=40,
        y=0,
        damage=8,
        attack_range=40,
        cooldown=0.8,
        readable=False,
    ):
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

        if readable:
            self.ecm.add_component(enemy, AttackHitbox(duration=0.12))
            self.ecm.add_component(enemy, EnemyAttackState(windup_duration=0.35))

        return enemy

    def create_enemy_index(self, *enemy_ids):
        enemy_index = UniformGrid(width=400, height=400, cell_size=64)

        for enemy_id in enemy_ids:
            position = self.ecm.get_component(enemy_id, Position)
            collider = self.ecm.get_component(enemy_id, Collider)
            enemy_index.insert(
                enemy_id,
                position.x,
                position.y,
                collider.width,
                collider.height,
            )

        return enemy_index

    def test_enemy_damages_player_in_range(self):
        player = self.create_player()
        self.create_enemy()

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 92)

    def test_enemy_without_attack_state_uses_legacy_instant_attack(self):
        player = self.create_player()
        enemy = self.create_enemy()

        self.assertFalse(self.ecm.has_component(enemy, EnemyAttackState))
        self.assertFalse(self.ecm.has_component(enemy, AttackHitbox))

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 92)

    def test_readable_enemy_attack_starts_windup_without_immediate_damage(self):
        player = self.create_player()
        enemy = self.create_enemy(readable=True)

        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.assertEqual(player_health.current, 100)
        self.assertTrue(attack_state.pending)
        self.assertAlmostEqual(attack_state.windup_timer, attack_state.windup_duration)
        self.assertTrue(hitbox.active)
        self.assertFalse(hitbox.hit_landed)
        self.assertGreater(hitbox.width, 0)
        self.assertGreater(hitbox.height, 0)

    def test_readable_enemy_attack_damages_after_windup_if_player_stays(self):
        player = self.create_player()
        enemy = self.create_enemy(readable=True)

        self.system.update(self.ecm, dt=0.1)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        self.system.update(self.ecm, dt=attack_state.windup_duration)
        player_health = self.ecm.get_component(player, Health)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.assertEqual(player_health.current, 92)
        self.assertFalse(attack_state.pending)
        self.assertTrue(hitbox.active)
        self.assertTrue(hitbox.hit_landed)

    def test_readable_enemy_attack_misses_if_player_leaves_before_windup(self):
        player = self.create_player()
        enemy = self.create_enemy(readable=True)
        player_position = self.ecm.get_component(player, Position)

        self.system.update(self.ecm, dt=0.1)
        player_position.x = -200
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        self.system.update(self.ecm, dt=attack_state.windup_duration)
        player_health = self.ecm.get_component(player, Health)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.assertEqual(player_health.current, 100)
        self.assertFalse(attack_state.pending)
        self.assertTrue(hitbox.active)
        self.assertFalse(hitbox.hit_landed)

    def test_readable_enemy_attack_sets_cooldown_after_resolve(self):
        self.create_player()
        enemy = self.create_enemy(readable=True, cooldown=0.8)
        attack = self.ecm.get_component(enemy, MeleeAttack)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)

        self.system.update(self.ecm, dt=0.1)
        self.system.update(self.ecm, dt=attack_state.windup_duration)

        self.assertAlmostEqual(attack.cooldown_timer, attack.cooldown)

    def test_readable_enemy_hitbox_deactivates_after_flash_duration(self):
        self.create_player()
        enemy = self.create_enemy(readable=True)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.system.update(self.ecm, dt=0.1)
        self.system.update(self.ecm, dt=attack_state.windup_duration)
        self.system.update(self.ecm, dt=hitbox.duration)

        self.assertFalse(hitbox.active)
        self.assertEqual(hitbox.timer, 0)
        self.assertFalse(hitbox.hit_landed)

    def test_dead_readable_enemy_does_not_keep_hitbox_active(self):
        player = self.create_player()
        enemy = self.create_enemy(readable=True)

        self.system.update(self.ecm, dt=0.1)
        self.ecm.add_component(enemy, Dead())
        self.system.update(self.ecm, dt=0.1)
        player_health = self.ecm.get_component(player, Health)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.assertEqual(player_health.current, 100)
        self.assertFalse(attack_state.pending)
        self.assertFalse(hitbox.active)

    def test_readable_enemy_with_spatial_index_starts_windup(self):
        player = self.create_player()
        enemy = self.create_enemy(readable=True)
        enemy_index = self.create_enemy_index(enemy)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        player_health = self.ecm.get_component(player, Health)
        attack_state = self.ecm.get_component(enemy, EnemyAttackState)
        hitbox = self.ecm.get_component(enemy, AttackHitbox)

        self.assertEqual(player_health.current, 100)
        self.assertTrue(attack_state.pending)
        self.assertTrue(hitbox.active)

    def test_enemy_with_spatial_index_damages_player_in_range(self):
        player = self.create_player()
        enemy = self.create_enemy()
        enemy_index = self.create_enemy_index(enemy)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 92)

    def test_enemy_outside_spatial_query_does_not_damage_player(self):
        player = self.create_player()
        enemy = self.create_enemy(x=100)
        enemy_index = self.create_enemy_index(enemy)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 100)

    def test_enemy_missing_from_spatial_index_does_not_damage_player(self):
        player = self.create_player()
        self.create_enemy()
        enemy_index = UniformGrid(width=400, height=400, cell_size=64)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        player_health = self.ecm.get_component(player, Health)

        self.assertEqual(player_health.current, 100)

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
