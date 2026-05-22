from src.components.components import Dead, Enemy, Health
from src.events.game_events import EnemyKilledEvent


class EnemyDeathSystem:
    """Помечает врагов с нулевым здоровьем как мёртвых"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus

    def update(self, ecm, region_id=None):
        for entity in ecm.get_entities_with(Enemy, Health):
            health = ecm.get_component(entity, Health)

            if health.current <= 0 and not ecm.has_component(entity, Dead):
                ecm.add_component(entity, Dead())

                if self.event_bus is not None and region_id is not None:
                    self.event_bus.publish(EnemyKilledEvent(entity, region_id))
