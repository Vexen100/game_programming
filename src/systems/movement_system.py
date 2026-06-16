from src.components.components import Position, Velocity


class MovementSystem:
    """Инкапсулирует gameplay-логику системы: movement system.

    """

    def update(self, ecm, dt):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Результат выполнения `update`.
        """
        previous_positions = {}

        for entity in ecm.get_entities_with(Position, Velocity):
            position = ecm.get_component(entity, Position)
            velocity = ecm.get_component(entity, Velocity)

            if velocity.x == 0 and velocity.y == 0:
                continue

            previous_positions[entity] = (position.x, position.y)

            position.x += velocity.x * dt
            position.y += velocity.y * dt

        return previous_positions
