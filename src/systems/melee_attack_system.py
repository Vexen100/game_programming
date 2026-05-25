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
from src.entities.entities_settings import PlayerSettings


class MeleeAttackSystem:
    """Обрабатывает ближнюю атаку игрока по врагу"""

    def update(self, ecm, dt, tile_map=None):
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
            facing = ecm.get_component(attacker_id, FacingDirection)
            hitbox = ecm.get_component(attacker_id, AttackHitbox)

            attack.cooldown_timer = max(0, attack.cooldown_timer - dt)
            self.update_hitbox_timer(hitbox, dt)

            if not attack_intent.requested:
                continue

            if attack.cooldown_timer > 0:
                attack_intent.requested = False
                continue

            attack_rect = self.build_attack_rect(attacker_position, attacker_collider, facing)
            hit_landed = self.apply_hitbox_damage(
                ecm,
                attacker_position,
                attacker_collider,
                facing,
                attack,
                attack_rect,
                tile_map,
            )

            self.activate_hitbox(hitbox, attack_rect, hit_landed)

            attack.cooldown_timer = attack.cooldown
            attack_intent.requested = False

    def update_hitbox_timer(self, hitbox, dt):
        if hitbox is None or not hitbox.active:
            return

        hitbox.timer = max(0, hitbox.timer - dt)

        if hitbox.timer == 0:
            hitbox.active = False

    def build_attack_rect(self, position, collider, facing):
        facing_x = 1
        facing_y = 0

        if facing is not None:
            facing_x = facing.x
            facing_y = facing.y

        hitbox_width = PlayerSettings.ATTACK_HITBOX_WIDTH
        hitbox_length = PlayerSettings.ATTACK_HITBOX_LENGTH

        center_x, center_y = self.get_center(position, collider)

        if facing_y < 0:
            return self.create_rect(
                center_x - hitbox_width / 2,
                position.y - hitbox_length,
                hitbox_width,
                hitbox_length,
            )

        if facing_y > 0:
            return self.create_rect(
                center_x - hitbox_width / 2,
                position.y + collider.height,
                hitbox_width,
                hitbox_length,
            )

        if facing_x < 0:
            return self.create_rect(
                position.x - hitbox_length,
                center_y - hitbox_width / 2,
                hitbox_length,
                hitbox_width,
            )

        return self.create_rect(
            position.x + collider.width,
            center_y - hitbox_width / 2,
            hitbox_length,
            hitbox_width,
        )

    def create_rect(self, x, y, width, height):
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }

    def apply_hitbox_damage(
        self,
        ecm,
        attacker_position,
        attacker_collider,
        facing,
        attack,
        attack_rect,
        tile_map,
    ):
        hit_landed = False
        attacker_center_x, attacker_center_y = self.get_center(attacker_position, attacker_collider)
        fallback_x, fallback_y = self.get_knockback_fallback(facing)

        for target_id in ecm.get_entities_with(Enemy, Position, Collider, Health):
            if ecm.has_component(target_id, Dead):
                continue

            target_position = ecm.get_component(target_id, Position)
            target_collider = ecm.get_component(target_id, Collider)

            if not self.rects_intersect(attack_rect, target_position, target_collider):
                continue

            target_health = ecm.get_component(target_id, Health)
            target_health.current = max(0, target_health.current - attack.damage)
            self.apply_knockback(
                target_position,
                target_collider,
                attacker_center_x,
                attacker_center_y,
                attack.knockback_distance,
                tile_map,
                fallback_x,
                fallback_y,
            )
            hit_landed = True

        return hit_landed

    def get_knockback_fallback(self, facing):
        if facing is None:
            return 1, 0

        return facing.x, facing.y

    def rects_intersect(self, attack_rect, target_position, target_collider):
        return (
            attack_rect["x"] < target_position.x + target_collider.width
            and attack_rect["x"] + attack_rect["width"] > target_position.x
            and attack_rect["y"] < target_position.y + target_collider.height
            and attack_rect["y"] + attack_rect["height"] > target_position.y
        )

    def apply_knockback(
        self,
        target_position,
        target_collider,
        attacker_center_x,
        attacker_center_y,
        knockback_distance,
        tile_map,
        fallback_x=1,
        fallback_y=0,
    ):
        if knockback_distance <= 0:
            return

        target_center_x, target_center_y = self.get_center(target_position, target_collider)
        dx = target_center_x - attacker_center_x
        dy = target_center_y - attacker_center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5

        if distance == 0:
            dx = fallback_x
            dy = fallback_y

            if dx == 0 and dy == 0:
                dx = 1
                dy = 0

            distance = (dx ** 2 + dy ** 2) ** 0.5

        next_x = target_position.x + dx / distance * knockback_distance
        next_y = target_position.y + dy / distance * knockback_distance

        if tile_map is not None and tile_map.is_rect_blocked(
            next_x,
            next_y,
            target_collider.width,
            target_collider.height,
        ):
            return

        target_position.x = next_x
        target_position.y = next_y

    def activate_hitbox(self, hitbox, attack_rect, hit_landed):
        if hitbox is None:
            return

        hitbox.active = True
        hitbox.x = attack_rect["x"]
        hitbox.y = attack_rect["y"]
        hitbox.width = int(attack_rect["width"])
        hitbox.height = int(attack_rect["height"])
        hitbox.timer = hitbox.duration
        hitbox.hit_landed = hit_landed

    def get_center(self, position, collider):
        center_x = position.x + collider.width / 2
        center_y = position.y + collider.height / 2
        return center_x, center_y
