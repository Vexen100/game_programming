from src.events.game_events import RegionLiberatedEvent


class RegionLiberationSystem:
    """Инкапсулирует gameplay-логику системы: регион liberation system.

    """

    def __init__(self, game_state):
        """Инициализирует `RegionLiberationSystem` и сохраняет начальные зависимости.

        Args:
            game_state: Глобальное состояние мира, регионов и прогресса игрока.

        Returns:
            None.
        """
        self.game_state = game_state

    def subscribe(self, event_bus):
        """Подписывает обработчик на события указанного типа.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        event_bus.subscribe(RegionLiberatedEvent, self.on_region_liberated)

    def on_region_liberated(self, event):
        """Обрабатывает событие освобождения региона.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        region = self.game_state.get_region(event.region_id)

        if region is None:
            raise ValueError(f"Регион с id '{event.region_id}' не найден")

        self.game_state.mark_liberated(event.region_id)
