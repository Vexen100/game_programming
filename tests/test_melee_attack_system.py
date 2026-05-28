import unittest

from src.algorithms.uniform_grid import UniformGrid
from src.components.components import (
    AttackHitbox,
    AttackIntent,
    Collider,
    Dead,
    Enemy,
    FacingDirection,
    Health,
    MeleeAttack,
    PlayerControlled,
    Position,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import PlayerSettings
from src.systems.melee_attack_system import MeleeAttackSystem


class TestMeleeAttackSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = MeleeAttackSystem()

    def create_player(
        self,
        x=0,
        y=0,
        damage=10,
        attack_range=48,
        cooldown=0.4,
        facing_x=1,
        facing_y=0,
        knockback_distance=0,
    ):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        self.ecm.add_component(player, Collider(width=32, height=32, solid=True))
        self.ecm.add_component(player, AttackIntent(requested=True))
        self.ecm.add_component(player, FacingDirection(facing_x, facing_y))
        self.ecm.add_component(player, AttackHitbox(duration=0.12))
        self.ecm.add_component(
            player,
            MeleeAttack(
                damage=damage,
                attack_range=attack_range,
                cooldown=cooldown,
                knockback_distance=knockback_distance,
            ),
        )
        return player

    def create_enemy(self, x, y, health=40, dead=False, width=32, height=32):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Position(x, y))
        self.ecm.add_component(enemy, Collider(width=width, height=height, solid=True))
        self.ecm.add_component(enemy, Health(current=health, maximum=health))
        if dead:
            self.ecm.add_component(enemy, Dead())
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

    def test_attack_damages_enemy_in_range(self):
        self.create_player()
        enemy = self.create_enemy(40, 0)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_attack_with_spatial_index_damages_enemy_inside_hitbox(self):
        self.create_player()
        enemy = self.create_enemy(40, 0)
        enemy_index = self.create_enemy_index(enemy)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_attack_with_spatial_index_does_not_damage_enemy_outside_hitbox(self):
        self.create_player(x=64, y=64, facing_x=1, facing_y=0)
        enemy = self.create_enemy(64, 120)
        enemy_index = self.create_enemy_index(enemy)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

    def test_attack_with_spatial_index_missing_enemy_does_not_damage(self):
        self.create_player()
        enemy = self.create_enemy(40, 0)
        enemy_index = UniformGrid(width=400, height=400, cell_size=64)

        self.system.update(self.ecm, dt=0.1, enemy_spatial_index=enemy_index)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

    def test_facing_right_does_not_hit_enemy_on_left(self):
        self.create_player(x=64, y=64, facing_x=1, facing_y=0)
        enemy = self.create_enemy(32, 64)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

    def test_facing_left_hits_enemy_on_left(self):
        self.create_player(x=64, y=64, facing_x=-1, facing_y=0)
        enemy = self.create_enemy(32, 64)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_facing_up_hits_enemy_above(self):
        self.create_player(x=64, y=64, facing_x=0, facing_y=-1)
        enemy = self.create_enemy(64, 32)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_facing_down_hits_enemy_below(self):
        self.create_player(x=64, y=64, facing_x=0, facing_y=1)
        enemy = self.create_enemy(64, 96)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 30)

    def test_enemy_outside_hitbox_is_not_damaged(self):
        self.create_player(x=64, y=64, facing_x=1, facing_y=0)
        enemy = self.create_enemy(64, 120)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)

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

    def test_attack_damages_all_enemies_inside_hitbox(self):
        self.create_player(x=64, y=64, facing_x=1, facing_y=0)
        first_enemy = self.create_enemy(96, 64)
        second_enemy = self.create_enemy(112, 64)

        self.system.update(self.ecm, dt=0.1)

        first_health = self.ecm.get_component(first_enemy, Health)
        second_health = self.ecm.get_component(second_enemy, Health)

        self.assertEqual(first_health.current, 30)
        self.assertEqual(second_health.current, 30)

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

    def test_hitbox_active_after_attack_and_hit_landed_true(self):
        player = self.create_player()
        self.create_enemy(40, 0)

        self.system.update(self.ecm, dt=0.1)
        hitbox = self.ecm.get_component(player, AttackHitbox)

        self.assertTrue(hitbox.active)
        self.assertTrue(hitbox.hit_landed)

    def test_hitbox_hit_landed_false_on_miss(self):
        player = self.create_player()

        self.system.update(self.ecm, dt=0.1)
        hitbox = self.ecm.get_component(player, AttackHitbox)

        self.assertTrue(hitbox.active)
        self.assertFalse(hitbox.hit_landed)

    def test_hitbox_expires(self):
        player = self.create_player()
        attack_intent = self.ecm.get_component(player, AttackIntent)
        self.system.update(self.ecm, dt=0.1)
        attack_intent.requested = False

        self.system.update(self.ecm, dt=0.2)
        hitbox = self.ecm.get_component(player, AttackHitbox)

        self.assertFalse(hitbox.active)

    def test_sequential_attacks_do_not_reuse_previous_runtime_hitbox_dimensions(self):
        player = self.create_player(facing_x=1, facing_y=0)

        self.system.update(self.ecm, dt=0.1)

        hitbox = self.ecm.get_component(player, AttackHitbox)
        self.assertEqual(hitbox.width, PlayerSettings.ATTACK_HITBOX_LENGTH)
        self.assertEqual(hitbox.height, PlayerSettings.ATTACK_HITBOX_WIDTH)

        attack = self.ecm.get_component(player, MeleeAttack)
        attack_intent = self.ecm.get_component(player, AttackIntent)
        facing = self.ecm.get_component(player, FacingDirection)

        self.system.update(self.ecm, dt=attack.cooldown)

        facing.x = 0
        facing.y = -1
        attack_intent.requested = True

        self.system.update(self.ecm, dt=0.1)

        self.assertEqual(hitbox.width, PlayerSettings.ATTACK_HITBOX_WIDTH)
        self.assertEqual(hitbox.height, PlayerSettings.ATTACK_HITBOX_LENGTH)

    def test_knockback_moves_enemy(self):
        self.create_player(x=64, y=64, facing_x=1, facing_y=0, knockback_distance=28)
        enemy = self.create_enemy(96, 64)
        enemy_position = self.ecm.get_component(enemy, Position)
        old_x = enemy_position.x

        self.system.update(self.ecm, dt=0.1)

        self.assertGreater(enemy_position.x, old_x)

    def test_knockback_uses_facing_direction_when_centers_match(self):
        self.create_player(x=64, y=64, facing_x=-1, facing_y=0, knockback_distance=28)
        enemy = self.create_enemy(32, 64, width=96)
        enemy_position = self.ecm.get_component(enemy, Position)
        old_x = enemy_position.x

        self.system.update(self.ecm, dt=0.1)

        self.assertLess(enemy_position.x, old_x)

    def test_knockback_does_not_move_enemy_into_wall(self):
        class BlockingTileMap:
            def is_rect_blocked(self, x, y, width, height):
                return True

        self.create_player(x=64, y=64, facing_x=1, facing_y=0, knockback_distance=28)
        enemy = self.create_enemy(96, 64)
        enemy_position = self.ecm.get_component(enemy, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        self.system.update(self.ecm, dt=0.1, tile_map=BlockingTileMap())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_dead_enemy_is_not_damaged(self):
        self.create_player()
        enemy = self.create_enemy(40, 0, dead=True)

        self.system.update(self.ecm, dt=0.1)
        health = self.ecm.get_component(enemy, Health)

        self.assertEqual(health.current, 40)


if __name__ == "__main__":
    unittest.main()
