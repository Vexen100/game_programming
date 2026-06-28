from src.components.components import (
    AnimationRequest,
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
from src.entities.entities_settings import EnemySettings
from src.systems.animation_system import direction_from_vector


class EnemyAttackSystem:
    """Инкапсулирует gameplay-логику системы: враг атака system.

    """

    def update(self, ecm, dt, enemy_spatial_index=None):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            None.
        """
        enemy_ids = ecm.get_entities_with(Enemy, Position, Collider, MeleeAttack)
        max_attack_range = self.update_enemy_timers(ecm, enemy_ids, dt)
        player_entities = ecm.get_entities_with(
            PlayerControlled,
            Position,
            Collider,
            Health,
        )

        if not player_entities:
            self.cancel_enemy_attacks(ecm, enemy_ids)
            return

        player_id = next(iter(player_entities))
        player_position = ecm.get_component(player_id, Position)
        player_collider = ecm.get_component(player_id, Collider)
        player_health = ecm.get_component(player_id, Health)
        candidate_ids = set(
            self.get_enemy_candidates(
                ecm,
                enemy_ids,
                player_position,
                player_collider,
                max_attack_range,
                enemy_spatial_index,
            )
        )
        candidate_ids.update(self.get_pending_enemy_ids(ecm, enemy_ids))

        for enemy_id in candidate_ids:
            if not self.is_attacking_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)
            enemy_collider = ecm.get_component(enemy_id, Collider)
            attack = ecm.get_component(enemy_id, MeleeAttack)

            if self.has_readable_attack_components(ecm, enemy_id):
                self.update_readable_attack(
                    ecm,
                    enemy_id,
                    enemy_position,
                    enemy_collider,
                    attack,
                    player_position,
                    player_collider,
                    player_health,
                    dt,
                )
                continue

            self.update_legacy_attack(
                enemy_position,
                enemy_collider,
                attack,
                player_position,
                player_collider,
                player_health,
            )

    def update_enemy_timers(self, ecm, enemy_ids, dt):
        """Обновляет враг timers.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_ids: Список идентификаторов врагов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Результат выполнения `update_enemy_timers`.
        """
        max_attack_range = 0

        for enemy_id in enemy_ids:
            if ecm.has_component(enemy_id, Dead):
                self.cancel_enemy_attack(ecm, enemy_id)
                continue

            attack = ecm.get_component(enemy_id, MeleeAttack)
            attack.cooldown_timer = max(0, attack.cooldown_timer - dt)
            max_attack_range = max(max_attack_range, attack.attack_range)

            if self.has_readable_attack_components(ecm, enemy_id):
                attack_state = ecm.get_component(enemy_id, EnemyAttackState)
                hitbox = ecm.get_component(enemy_id, AttackHitbox)
                self.update_hitbox_recovery(attack_state, hitbox, dt)

        return max_attack_range

    def update_readable_attack(
        self,
        ecm,
        enemy_id,
        enemy_position,
        enemy_collider,
        attack,
        player_position,
        player_collider,
        player_health,
        dt,
    ):
        """Обновляет читаемые атака.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            attack: Компонент атаки с уроном, дальностью и таймерами.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            player_health: Компонент здоровья игрока.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        attack_state = ecm.get_component(enemy_id, EnemyAttackState)
        hitbox = ecm.get_component(enemy_id, AttackHitbox)

        if attack_state.pending:
            self.update_pending_attack(
                attack_state,
                hitbox,
                attack,
                player_position,
                player_collider,
                player_health,
                dt,
            )
            return

        if attack.cooldown_timer > 0:
            return

        distance = self.get_distance_between_rects(
            enemy_position,
            enemy_collider,
            player_position,
            player_collider,
        )

        if distance > attack.attack_range:
            return

        attack_rect = self.build_enemy_attack_rect(
            enemy_position,
            enemy_collider,
            player_position,
            player_collider,
        )
        self.add_attack_animation_request(
            ecm,
            enemy_id,
            enemy_position,
            enemy_collider,
            player_position,
            player_collider,
            attack_state.windup_duration,
        )
        self.start_windup(attack_state, hitbox, attack_rect)

    def add_attack_animation_request(
        self,
        ecm,
        enemy_id,
        enemy_position,
        enemy_collider,
        player_position,
        player_collider,
        duration,
    ):
        """Запрашивает visual-only attack animation врага.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            duration: Длительность visual-lock состояния.

        Returns:
            None.
        """
        enemy_center_x, enemy_center_y = self.get_center(enemy_position, enemy_collider)
        player_center_x, player_center_y = self.get_center(player_position, player_collider)
        direction = direction_from_vector(
            player_center_x - enemy_center_x,
            player_center_y - enemy_center_y,
            "down",
        )
        ecm.add_component(
            enemy_id,
            AnimationRequest(
                state="attack",
                direction=direction,
                duration=duration,
                frame_duration=duration / 4,
            ),
        )

    def update_pending_attack(
        self,
        attack_state,
        hitbox,
        attack,
        player_position,
        player_collider,
        player_health,
        dt,
    ):
        """Обновляет отложенное атака.

        Args:
            attack_state: Состояние текущей атаки врага или игрока.
            hitbox: Активный hitbox атаки.
            attack: Компонент атаки с уроном, дальностью и таймерами.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            player_health: Компонент здоровья игрока.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        attack_state.windup_timer = max(0, attack_state.windup_timer - dt)
        hitbox.active = True

        if attack_state.windup_timer > 0:
            return

        hit_landed = self.rects_intersect(
            self.get_hitbox_rect(hitbox),
            player_position,
            player_collider,
        )

        if hit_landed:
            player_health.current = max(0, player_health.current - attack.damage)

        hitbox.hit_landed = hit_landed
        hitbox.timer = hitbox.duration
        hitbox.active = True
        attack_state.pending = False
        attack_state.windup_timer = 0
        attack_state.recovery_timer = hitbox.duration
        attack.cooldown_timer = attack.cooldown

    def update_legacy_attack(
        self,
        enemy_position,
        enemy_collider,
        attack,
        player_position,
        player_collider,
        player_health,
    ):
        """Обновляет legacy атака.

        Args:
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            attack: Компонент атаки с уроном, дальностью и таймерами.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            player_health: Компонент здоровья игрока.

        Returns:
            None.
        """
        if attack.cooldown_timer > 0:
            return

        distance = self.get_distance_between_rects(
            enemy_position,
            enemy_collider,
            player_position,
            player_collider,
        )

        if distance > attack.attack_range:
            return

        player_health.current = max(0, player_health.current - attack.damage)
        attack.cooldown_timer = attack.cooldown

    def update_hitbox_recovery(self, attack_state, hitbox, dt):
        """Обновляет hitbox recovery.

        Args:
            attack_state: Состояние текущей атаки врага или игрока.
            hitbox: Активный hitbox атаки.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        if attack_state.pending:
            return

        if not hitbox.active:
            attack_state.recovery_timer = 0
            return

        if attack_state.recovery_timer <= 0:
            return

        attack_state.recovery_timer = max(0, attack_state.recovery_timer - dt)
        hitbox.timer = attack_state.recovery_timer

        if attack_state.recovery_timer == 0:
            self.deactivate_hitbox(hitbox)

    def start_windup(self, attack_state, hitbox, attack_rect):
        """Запускает фазу подготовки атаки врага.

        Args:
            attack_state: Состояние текущей атаки врага или игрока.
            hitbox: Активный hitbox атаки.
            attack_rect: Прямоугольная область активного удара.

        Returns:
            None.
        """
        attack_state.pending = True
        attack_state.windup_timer = attack_state.windup_duration
        attack_state.recovery_timer = 0
        hitbox.active = True
        hitbox.x = attack_rect["x"]
        hitbox.y = attack_rect["y"]
        hitbox.width = int(attack_rect["width"])
        hitbox.height = int(attack_rect["height"])
        hitbox.timer = attack_state.windup_timer
        hitbox.hit_landed = False

    def cancel_enemy_attacks(self, ecm, enemy_ids):
        """Отменяет враг атаки.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_ids: Список идентификаторов врагов.

        Returns:
            None.
        """
        for enemy_id in enemy_ids:
            self.cancel_enemy_attack(ecm, enemy_id)

    def cancel_enemy_attack(self, ecm, enemy_id):
        """Отменяет враг атака.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.

        Returns:
            None.
        """
        attack_state = ecm.get_component(enemy_id, EnemyAttackState)
        hitbox = ecm.get_component(enemy_id, AttackHitbox)

        if attack_state is not None:
            attack_state.pending = False
            attack_state.windup_timer = 0
            attack_state.recovery_timer = 0

        if hitbox is not None:
            self.deactivate_hitbox(hitbox)

    def deactivate_hitbox(self, hitbox):
        """Деактивирует hitbox атаки врага.

        Args:
            hitbox: Активный hitbox атаки.

        Returns:
            None.
        """
        hitbox.active = False
        hitbox.timer = 0
        hitbox.hit_landed = False

    def has_readable_attack_components(self, ecm, enemy_id):
        """Проверяет выполнение условия: has читаемые атака компоненты.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return (
            ecm.has_component(enemy_id, EnemyAttackState)
            and ecm.has_component(enemy_id, AttackHitbox)
        )

    def get_pending_enemy_ids(self, ecm, enemy_ids):
        """Возвращает отложенное враг ids.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_ids: Список идентификаторов врагов.

        Returns:
            Найденное или вычисленное значение: отложенное враг ids.
        """
        pending_ids = set()

        for enemy_id in enemy_ids:
            attack_state = ecm.get_component(enemy_id, EnemyAttackState)

            if attack_state is not None and attack_state.pending:
                pending_ids.add(enemy_id)

        return pending_ids

    def get_enemy_candidates(
        self,
        ecm,
        enemy_ids,
        player_position,
        player_collider,
        max_attack_range,
        enemy_spatial_index,
    ):
        """Возвращает враг candidates.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_ids: Список идентификаторов врагов.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            max_attack_range: Значение `max атака range`, используемое в логике метода.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            Найденное или вычисленное значение: враг candidates.
        """
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

    def build_enemy_attack_rect(
        self,
        enemy_position,
        enemy_collider,
        player_position,
        player_collider,
    ):
        """Собирает враг атака прямоугольник.

        Args:
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.

        Returns:
            Созданный результат: враг атака прямоугольник.
        """
        hitbox_width = EnemySettings.ATTACK_HITBOX_WIDTH
        hitbox_length = EnemySettings.ATTACK_HITBOX_LENGTH
        enemy_center_x, enemy_center_y = self.get_center(enemy_position, enemy_collider)
        player_center_x, player_center_y = self.get_center(player_position, player_collider)
        dx = player_center_x - enemy_center_x
        dy = player_center_y - enemy_center_y

        if abs(dx) >= abs(dy):
            if dx < 0:
                return self.create_rect(
                    enemy_position.x - hitbox_length,
                    enemy_center_y - hitbox_width / 2,
                    hitbox_length,
                    hitbox_width,
                )

            return self.create_rect(
                enemy_position.x + enemy_collider.width,
                enemy_center_y - hitbox_width / 2,
                hitbox_length,
                hitbox_width,
            )

        if dy < 0:
            return self.create_rect(
                enemy_center_x - hitbox_width / 2,
                enemy_position.y - hitbox_length,
                hitbox_width,
                hitbox_length,
            )

        return self.create_rect(
            enemy_center_x - hitbox_width / 2,
            enemy_position.y + enemy_collider.height,
            hitbox_width,
            hitbox_length,
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

    def get_hitbox_rect(self, hitbox):
        """Возвращает hitbox прямоугольник.

        Args:
            hitbox: Активный hitbox атаки.

        Returns:
            Найденное или вычисленное значение: hitbox прямоугольник.
        """
        return self.create_rect(
            hitbox.x,
            hitbox.y,
            hitbox.width,
            hitbox.height,
        )

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

    def is_attacking_enemy(self, ecm, enemy_id):
        """Проверяет выполнение условия: is attacking враг.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
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
        """Возвращает дистанция between прямоугольники.

        Args:
            first_position: Позиция первого объекта в пикселях.
            first_collider: Коллайдер первого объекта.
            second_position: Позиция второго объекта в пикселях.
            second_collider: Коллайдер второго объекта.

        Returns:
            Найденное или вычисленное значение: дистанция between прямоугольники.
        """
        first_center_x = first_position.x + first_collider.width / 2
        first_center_y = first_position.y + first_collider.height / 2

        second_center_x = second_position.x + second_collider.width / 2
        second_center_y = second_position.y + second_collider.height / 2

        dx = second_center_x - first_center_x
        dy = second_center_y - first_center_y

        return (dx ** 2 + dy ** 2) ** 0.5
