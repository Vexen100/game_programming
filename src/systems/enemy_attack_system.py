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

    def update(self, ecm, dt):
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

        for enemy_id in ecm.get_entities_with(Enemy, Position, Collider, MeleeAttack):
            if ecm.has_component(enemy_id, Dead):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)
            enemy_collider = ecm.get_component(enemy_id, Collider)
            attack = ecm.get_component(enemy_id, MeleeAttack)

            attack.cooldown_timer = max(0, attack.cooldown_timer - dt)

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
