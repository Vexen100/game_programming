from src.components.components import Health, PlayerControlled, PlayerDefeated


class PlayerDeathSystem:
    """Инкапсулирует gameplay-логику системы: игрок death system.

    """

    def update(self, ecm):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            None.
        """
        for entity in ecm.get_entities_with(PlayerControlled, Health):
            health = ecm.get_component(entity, Health)

            if health.current <= 0 and not ecm.has_component(entity, PlayerDefeated):
                ecm.add_component(entity, PlayerDefeated())
