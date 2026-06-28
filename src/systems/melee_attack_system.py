from src.components.components import (
    AttackHitbox,
    AttackIntent,
    Collider,
    Dead,
    Enemy,
    FacingDirection,
    Health,
    HitFlash,
    MeleeAttack,
    PlayerControlled,
    Position,
)
from src.entities.entities_settings import PlayerSettings


class MeleeAttackSystem:
    """Инкапсулирует gameplay-логику системы: melee атака system.

    """

    def __init__(self, visual_effect_system=None):
        """Инициализирует систему melee-атаки.

        Args:
            visual_effect_system: Необязательная runtime-система визуальных эффектов.

        Returns:
            None.
        """
        self.visual_effect_system = visual_effect_system

    def update(self, ecm, dt, tile_map=None, enemy_spatial_index=None):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            None.
        """
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
            self.spawn_slash_effect(ecm, attack_rect, facing)
            hit_landed = self.apply_hitbox_damage(
                ecm,
                attacker_position,
                attacker_collider,
                facing,
                attack,
                attack_rect,
                tile_map,
                enemy_spatial_index,
            )

            self.activate_hitbox(hitbox, attack_rect, hit_landed)

            attack.cooldown_timer = attack.cooldown
            attack_intent.requested = False

    def update_hitbox_timer(self, hitbox, dt):
        """Обновляет hitbox таймер.

        Args:
            hitbox: Активный hitbox атаки.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        if hitbox is None or not hitbox.active:
            return

        hitbox.timer = max(0, hitbox.timer - dt)

        if hitbox.timer == 0:
            hitbox.active = False

    def build_attack_rect(self, position, collider, facing):
        """Собирает атака прямоугольник.

        Args:
            position: Позиция объекта в пикселях.
            collider: Коллайдер сущности для столкновений и попаданий.
            facing: Направение взгляда или удара сущности.

        Returns:
            Созданный результат: атака прямоугольник.
        """
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
        """Создает прямоугольник.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            Созданный результат: прямоугольник.
        """
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
        enemy_spatial_index=None,
    ):
        """Применяет hitbox урон.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            attacker_position: Позиция атакующей сущности в пикселях.
            attacker_collider: Коллайдер атакующей сущности.
            facing: Направение взгляда или удара сущности.
            attack: Компонент атаки с уроном, дальностью и таймерами.
            attack_rect: Прямоугольная область активного удара.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            Результат выполнения `apply_hitbox_damage`.
        """
        hit_landed = False
        attacker_center_x, attacker_center_y = self.get_center(attacker_position, attacker_collider)
        fallback_x, fallback_y = self.get_knockback_fallback(facing)

        for target_id in self.get_enemy_candidates(
            ecm,
            attack_rect,
            attacker_position,
            attacker_collider,
            enemy_spatial_index,
        ):
            if not self.is_damageable_enemy(ecm, target_id):
                continue

            target_position = ecm.get_component(target_id, Position)
            target_collider = ecm.get_component(target_id, Collider)

            if not (
                self.rects_intersect(attack_rect, target_position, target_collider)
                or self.target_intersects_attacker_body(
                    attacker_position,
                    attacker_collider,
                    target_position,
                    target_collider,
                )
            ):
                continue

            target_health = ecm.get_component(target_id, Health)
            target_health.current = max(0, target_health.current - attack.damage)
            self.trigger_hit_feedback(
                ecm,
                target_id,
                target_position,
                target_collider,
                attack.damage,
            )
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

    def spawn_slash_effect(self, ecm, attack_rect, facing):
        """Создает slash effect для принятой атаки игрока.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            attack_rect: Прямоугольная область активного удара.
            facing: Направение взгляда или удара сущности.

        Returns:
            None.
        """
        if self.visual_effect_system is None:
            return

        self.visual_effect_system.spawn_slash_effect(
            ecm,
            attack_rect,
            self.get_direction_name(facing),
        )

    def trigger_hit_feedback(self, ecm, target_id, target_position, target_collider, damage):
        """Запускает hit flash и damage popup после реального попадания.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            target_id: Идентификатор сущности, получившей урон.
            target_position: Позиция цели в пикселях.
            target_collider: Коллайдер цели.
            damage: Количество нанесенного урона.

        Returns:
            None.
        """
        self.add_hit_flash(ecm, target_id)

        if self.visual_effect_system is None:
            return

        popup_x = target_position.x + target_collider.width / 2
        popup_y = target_position.y - 6
        self.visual_effect_system.spawn_damage_popup(ecm, popup_x, popup_y, damage)

    def add_hit_flash(self, ecm, target_id):
        """Добавляет или обновляет flash-компонент цели.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            target_id: Идентификатор сущности, получившей урон.

        Returns:
            None.
        """
        hit_flash = ecm.get_component(target_id, HitFlash)

        if hit_flash is None:
            hit_flash = HitFlash()
            ecm.add_component(target_id, hit_flash)

        hit_flash.timer = hit_flash.duration

    def get_direction_name(self, facing):
        """Возвращает имя направления для slash effect.

        Args:
            facing: Направение взгляда или удара сущности.

        Returns:
            Текстовое направление эффекта.
        """
        if facing is None:
            return "right"

        if abs(facing.y) > abs(facing.x):
            return "down" if facing.y > 0 else "up"

        return "left" if facing.x < 0 else "right"

    def get_enemy_candidates(
        self,
        ecm,
        attack_rect,
        attacker_position,
        attacker_collider,
        enemy_spatial_index,
    ):
        """Возвращает враг candidates.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            attack_rect: Прямоугольная область активного удара.
            attacker_position: Позиция атакующей сущности в пикселях.
            attacker_collider: Коллайдер атакующей сущности.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            Найденное или вычисленное значение: враг candidates.
        """
        if enemy_spatial_index is None:
            return ecm.get_entities_with(Enemy, Position, Collider, Health)

        candidates = enemy_spatial_index.query_rect(
            attack_rect["x"],
            attack_rect["y"],
            attack_rect["width"],
            attack_rect["height"],
        )
        candidates.update(
            enemy_spatial_index.query_rect(
                attacker_position.x,
                attacker_position.y,
                attacker_collider.width,
                attacker_collider.height,
            )
        )
        return candidates

    def is_damageable_enemy(self, ecm, entity_id):
        """Проверяет, можно ли нанести урон врагу.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            entity_id: Идентификатор сущности в EntityComponentManager.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if ecm.has_component(entity_id, Dead):
            return False

        return (
            ecm.has_component(entity_id, Enemy)
            and ecm.has_component(entity_id, Position)
            and ecm.has_component(entity_id, Collider)
            and ecm.has_component(entity_id, Health)
        )

    def get_knockback_fallback(self, facing):
        """Возвращает отталкивание fallback.

        Args:
            facing: Направение взгляда или удара сущности.

        Returns:
            Найденное или вычисленное значение: отталкивание fallback.
        """
        if facing is None:
            return 1, 0

        return facing.x, facing.y

    def rects_intersect(self, attack_rect, target_position, target_collider):
        """Проверяет пересечение прямоугольников.

        Args:
            attack_rect: Прямоугольная область активного удара.
            target_position: Позиция цели в пикселях.
            target_collider: Коллайдер цели.

        Returns:
            Результат выполнения `rects_intersect`.
        """
        return (
            attack_rect["x"] < target_position.x + target_collider.width
            and attack_rect["x"] + attack_rect["width"] > target_position.x
            and attack_rect["y"] < target_position.y + target_collider.height
            and attack_rect["y"] + attack_rect["height"] > target_position.y
        )

    def target_intersects_attacker_body(
        self,
        attacker_position,
        attacker_collider,
        target_position,
        target_collider,
    ):
        """Проверяет пересечение цели с телом атакующего.

        Args:
            attacker_position: Позиция атакующей сущности в пикселях.
            attacker_collider: Коллайдер атакующей сущности.
            target_position: Позиция цели в пикселях.
            target_collider: Коллайдер цели.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        attacker_rect = self.create_rect(
            attacker_position.x,
            attacker_position.y,
            attacker_collider.width,
            attacker_collider.height,
        )
        return self.rects_intersect(attacker_rect, target_position, target_collider)

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
        """Применяет отталкивание.

        Args:
            target_position: Позиция цели в пикселях.
            target_collider: Коллайдер цели.
            attacker_center_x: Координата центра атакующего по оси X.
            attacker_center_y: Координата центра атакующего по оси Y.
            knockback_distance: Дистанция отталкивания цели после попадания.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            fallback_x: Запасное направление отталкивания по оси X.
            fallback_y: Запасное направление отталкивания по оси Y.

        Returns:
            None.
        """
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
        """Активирует hitbox атаки.

        Args:
            hitbox: Активный hitbox атаки.
            attack_rect: Прямоугольная область активного удара.
            hit_landed: Флаг, показывающий, было ли уже засчитано попадание.

        Returns:
            None.
        """
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
        """Возвращает центр.

        Args:
            position: Позиция объекта в пикселях.
            collider: Коллайдер сущности для столкновений и попаданий.

        Returns:
            Найденное или вычисленное значение: центр.
        """
        center_x = position.x + collider.width / 2
        center_y = position.y + collider.height / 2
        return center_x, center_y
