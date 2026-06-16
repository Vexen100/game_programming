from src.components.components import Dead


class CleanupSystem:
    """Инкапсулирует gameplay-логику системы: cleanup system.

    """

    def update(self, ecm):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            None.
        """
        dead_entities = list(ecm.get_entities_with(Dead))

        for entity in dead_entities:
            ecm.destroy_entity(entity)
