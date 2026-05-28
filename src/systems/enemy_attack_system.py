from src.components.components import (
    Collider,
    Dead,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    Position,
)


class EnemyAttackSystem:
    """Наносит урон игроку, если живой враг находится рядом"""

    def update(self, ecm, dt, enemy_spatial_index=None):
        player_entities = ecm.get_entities_with(
            PlayerControlled,
            Position,
            Collider,
            Health,
        )

        if not player_entities:
            return

        player_id = next(iter(player_entities))
        player_position = ecm.get_component(player_id, Position)
        player_collider = ecm.get_component(player_id, Collider)
        player_health = ecm.get_component(player_id, Health)
        enemy_ids = ecm.get_entities_with(Enemy, Position, Collider, MeleeAttack)
        max_attack_range = 0

        for enemy_id in enemy_ids:
            if ecm.has_component(enemy_id, Dead):
                continue

            attack = ecm.get_component(enemy_id, MeleeAttack)
            attack.cooldown_timer = max(0, attack.cooldown_timer - dt)
            max_attack_range = max(max_attack_range, attack.attack_range)

        for enemy_id in self.get_enemy_candidates(
            ecm,
            enemy_ids,
            player_position,
            player_collider,
            max_attack_range,
            enemy_spatial_index,
        ):
            if not self.is_attacking_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)
            enemy_collider = ecm.get_component(enemy_id, Collider)
            attack = ecm.get_component(enemy_id, MeleeAttack)

            if attack.cooldown_timer > 0:
                continue

            distance = self.get_distance_between_rects(
                enemy_position,
                enemy_collider,
                player_position,
                player_collider,
            )

            if distance > attack.attack_range:
                continue

            player_health.current = max(0, player_health.current - attack.damage)
            attack.cooldown_timer = attack.cooldown

    def get_enemy_candidates(
        self,
        ecm,
        enemy_ids,
        player_position,
        player_collider,
        max_attack_range,
        enemy_spatial_index,
    ):
        if enemy_spatial_index is None:
            return enemy_ids

        if max_attack_range <= 0:
            return set()

        player_center_x = player_position.x + player_collider.width / 2
        player_center_y = player_position.y + player_collider.height / 2
        return enemy_spatial_index.query_radius(
            player_center_x,
            player_center_y,
            max_attack_range,
        )

    def is_attacking_enemy(self, ecm, enemy_id):
        if ecm.has_component(enemy_id, Dead):
            return False

        return (
            ecm.has_component(enemy_id, Enemy)
            and ecm.has_component(enemy_id, Position)
            and ecm.has_component(enemy_id, Collider)
            and ecm.has_component(enemy_id, MeleeAttack)
        )

    def get_distance_between_rects(
        self,
        first_position,
        first_collider,
        second_position,
        second_collider,
    ):
        first_center_x = first_position.x + first_collider.width / 2
        first_center_y = first_position.y + first_collider.height / 2

        second_center_x = second_position.x + second_collider.width / 2
        second_center_y = second_position.y + second_collider.height / 2

        dx = second_center_x - first_center_x
        dy = second_center_y - first_center_y

        return (dx ** 2 + dy ** 2) ** 0.5
