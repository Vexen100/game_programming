from src.components.components import Dead


class CleanupSystem:
    """Удаляет сущности, помеченные как Dead"""

    def update(self, ecm):
        dead_entities = list(ecm.get_entities_with(Dead))

        for entity in dead_entities:
            ecm.destroy_entity(entity)
