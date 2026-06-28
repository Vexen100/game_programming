from src.components.components import Animation, AnimationRequest, FacingDirection, Velocity


DEFAULT_WALK_FRAME_COUNT = 4
DEFAULT_ATTACK_FRAME_COUNT = 4
MOVEMENT_EPSILON = 0.01


def direction_from_vector(x, y, default="down"):
    """Возвращает направление по вектору.

    Args:
        x: Компонента X вектора.
        y: Компонента Y вектора.
        default: Направление, если вектор нулевой.

    Returns:
        `left`, `right`, `up` или `down`.
    """
    if abs(x) <= MOVEMENT_EPSILON and abs(y) <= MOVEMENT_EPSILON:
        return default

    if abs(x) > abs(y):
        return "right" if x > 0 else "left"

    return "down" if y > 0 else "up"


class AnimationSystem:
    """Обновляет runtime idle/walk/attack анимацию сущностей через deltaTime.

    """

    def update(self, ecm, dt):
        """Обновляет состояние анимаций за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        for entity_id in ecm.get_entities_with(Animation):
            animation = ecm.get_component(entity_id, Animation)
            self.consume_animation_request(ecm, entity_id, animation)

            if animation.lock_timer > 0:
                self.update_locked_animation(animation, dt)

                if animation.lock_timer > 0:
                    continue

            velocity = ecm.get_component(entity_id, Velocity)
            facing = ecm.get_component(entity_id, FacingDirection)
            self.update_idle_walk(animation, velocity, facing, dt)

    def consume_animation_request(self, ecm, entity_id, animation):
        """Применяет и удаляет `AnimationRequest`, если он есть.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            entity_id: Идентификатор сущности в EntityComponentManager.
            animation: Компонент runtime-анимации.

        Returns:
            None.
        """
        request = ecm.get_component(entity_id, AnimationRequest)

        if request is None:
            return

        animation.state = request.state
        animation.direction = request.direction
        animation.frame_index = 0
        animation.frame_timer = 0
        animation.frame_duration = request.frame_duration
        animation.lock_timer = request.duration
        animation.lock_duration = request.duration
        ecm.remove_component(entity_id, AnimationRequest)

    def update_locked_animation(self, animation, dt):
        """Обновляет visual-lock анимацию без влияния скорости.

        Args:
            animation: Компонент runtime-анимации.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        animation.lock_timer = max(0, animation.lock_timer - dt)
        self.advance_frame(animation, dt, self.get_frame_count(animation.state))

        if animation.lock_timer == 0:
            animation.lock_duration = 0

    def update_idle_walk(self, animation, velocity, facing, dt):
        """Обновляет обычные idle/walk состояния.

        Args:
            animation: Компонент runtime-анимации.
            velocity: Компонент скорости сущности или `None`.
            facing: Компонент направления взгляда или `None`.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        state = "idle"
        direction = self.get_idle_direction(animation, facing)

        if self.is_moving(velocity):
            state = "walk"
            direction = self.get_direction_from_velocity(velocity)

        changed = state != animation.state or direction != animation.direction
        if changed:
            animation.frame_index = 0
            animation.frame_timer = 0

        animation.state = state
        animation.direction = direction
        animation.lock_timer = 0
        animation.lock_duration = 0

        if animation.state == "idle":
            animation.frame_index = 0
            animation.frame_timer = 0
            return

        self.advance_frame(animation, dt, DEFAULT_WALK_FRAME_COUNT)

    def is_moving(self, velocity):
        """Проверяет, есть ли значимое движение.

        Args:
            velocity: Компонент скорости сущности или `None`.

        Returns:
            `True`, если скорость не нулевая, иначе `False`.
        """
        if velocity is None:
            return False

        return (
            abs(velocity.x) > MOVEMENT_EPSILON
            or abs(velocity.y) > MOVEMENT_EPSILON
        )

    def get_idle_direction(self, animation, facing):
        """Возвращает направление idle-анимации.

        Args:
            animation: Компонент runtime-анимации.
            facing: Компонент направления взгляда или `None`.

        Returns:
            Текстовое направление idle-анимации.
        """
        if facing is None:
            return animation.direction

        return direction_from_vector(facing.x, facing.y, animation.direction)

    def get_direction_from_velocity(self, velocity):
        """Возвращает направление анимации по скорости.

        Args:
            velocity: Компонент скорости сущности.

        Returns:
            Текстовое направление движения.
        """
        return direction_from_vector(velocity.x, velocity.y, "down")

    def advance_walk_frame(self, animation, dt):
        """Продвигает кадр walk-анимации через deltaTime.

        Args:
            animation: Компонент runtime-анимации.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        self.advance_frame(animation, dt, DEFAULT_WALK_FRAME_COUNT)

    def advance_frame(self, animation, dt, frame_count):
        """Продвигает кадр анимации через deltaTime.

        Args:
            animation: Компонент runtime-анимации.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            frame_count: Количество кадров в текущем состоянии.

        Returns:
            None.
        """
        frame_count = max(1, frame_count)

        if animation.frame_duration <= 0:
            animation.frame_timer = 0
            animation.frame_index %= frame_count
            return

        animation.frame_timer += dt

        while animation.frame_timer >= animation.frame_duration:
            animation.frame_timer -= animation.frame_duration
            animation.frame_index += 1

        animation.frame_index %= frame_count

    def get_frame_count(self, state):
        """Возвращает количество кадров для состояния анимации.

        Args:
            state: Текущее состояние анимации.

        Returns:
            Количество кадров.
        """
        if state == "attack":
            return DEFAULT_ATTACK_FRAME_COUNT

        if state == "walk":
            return DEFAULT_WALK_FRAME_COUNT

        return 1
