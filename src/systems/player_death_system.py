from src.components.components import Health, PlayerControlled, PlayerDefeated


class PlayerDeathSystem:
    """Помечает игрока как побеждённого при нулевом здоровье"""

    def update(self, ecm):
        for entity in ecm.get_entities_with(PlayerControlled, Health):
            health = ecm.get_component(entity, Health)

            if health.current <= 0 and not ecm.has_component(entity, PlayerDefeated):
                ecm.add_component(entity, PlayerDefeated())
