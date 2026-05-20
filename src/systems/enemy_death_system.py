from src.components.components import Dead, Enemy, Health


class EnemyDeathSystem:
    """Помечает врагов с нулевым здоровьем как мёртвых"""

    def update(self, ecm):
        for entity in ecm.get_entities_with(Enemy, Health):
            health = ecm.get_component(entity, Health)

            if health.current <= 0 and not ecm.has_component(entity, Dead):
                ecm.add_component(entity, Dead())
