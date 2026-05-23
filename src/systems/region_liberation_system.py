from src.events.game_events import RegionLiberatedEvent


class RegionLiberationSystem:
    """Обновляет GameState после освобождения региона"""

    def __init__(self, game_state):
        self.game_state = game_state

    def subscribe(self, event_bus):
        event_bus.subscribe(RegionLiberatedEvent, self.on_region_liberated)

    def on_region_liberated(self, event):
        region = self.game_state.get_region(event.region_id)

        if region is None:
            raise ValueError(f"Регион с id '{event.region_id}' не найден")

        self.game_state.mark_liberated(event.region_id)
