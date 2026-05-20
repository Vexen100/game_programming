from src.components.components import (
    AttackIntent,
    Collider,
    Enemy,
    Health,
    MeleeAttack,
    PlayerControlled,
    Position,
)


class MeleeAttackSystem:
    """Обрабатывает ближнюю атаку игрока по врагу"""

    def update(self, ecm, dt):
        for attacker_id in ecm.get_entities_with(
            PlayerControlled,
            Position,
            Collider,
            AttackIntent,
            MeleeAttack,
        ):
            attacker_position = ecm.get_component(attacker_id, Position)
            attacker_collider = ecm.get_component(attacker_id, Collider)
            attack_intent = ecm.get_component(attacker_id, AttackIntent)
            attack = ecm.get_component(attacker_id, MeleeAttack)

            attack.cooldown_timer = max(0, attack.cooldown_timer - dt)

            if not attack_intent.requested:
                continue

            if attack.cooldown_timer > 0:
                attack_intent.requested = False
                continue

            target_id = self.find_closest_target(
                ecm,
                attacker_position,
                attacker_collider,
                attack.attack_range,
            )

            if target_id is not None:
                target_health = ecm.get_component(target_id, Health)
                target_health.current = max(0, target_health.current - attack.damage)
                attack.cooldown_timer = attack.cooldown

            attack_intent.requested = False

    def find_closest_target(self, ecm, attacker_position, attacker_collider, attack_range):
        closest_target_id = None
        closest_distance = None

        attacker_center_x, attacker_center_y = self.get_center(attacker_position, attacker_collider)

        for target_id in ecm.get_entities_with(Enemy, Position, Collider, Health):
            target_position = ecm.get_component(target_id, Position)
            target_collider = ecm.get_component(target_id, Collider)
            target_center_x, target_center_y = self.get_center(target_position, target_collider)

            dx = target_center_x - attacker_center_x
            dy = target_center_y - attacker_center_y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > attack_range:
                continue

            if closest_distance is None or distance < closest_distance:
                closest_target_id = target_id
                closest_distance = distance

        return closest_target_id

    def get_center(self, position, collider):
        center_x = position.x + collider.width / 2
        center_y = position.y + collider.height / 2
        return center_x, center_y
