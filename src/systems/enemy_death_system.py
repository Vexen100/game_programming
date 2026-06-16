from src.components.components import Dead, Enemy, Health
from src.events.game_events import EnemyKilledEvent


class EnemyDeathSystem:
    """Инкапсулирует gameplay-логику системы: враг death system.

    """

    def __init__(self, event_bus=None):
        """Инициализирует `EnemyDeathSystem` и сохраняет начальные зависимости.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        self.event_bus = event_bus

    def update(self, ecm, region_id=None):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        for entity in ecm.get_entities_with(Enemy, Health):
            health = ecm.get_component(entity, Health)

            if health.current <= 0 and not ecm.has_component(entity, Dead):
                ecm.add_component(entity, Dead())

                if self.event_bus is not None and region_id is not None:
                    self.event_bus.publish(EnemyKilledEvent(entity, region_id))
