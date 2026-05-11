from src.ecs.entity_componet_manager import EntityComponentManager

class EntityFactory:
    """Создаёт все сущности с готовыми компонентами"""
    def __init__(self) -> None:
        self.ecm = EntityComponentManager()

    def create_player(self, position):
        self.ecm.create_entity("player")
        self.ecm.add_component()