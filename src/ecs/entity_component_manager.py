class EntityComponentManager:
    def __init__(self) -> None:
        self.next_entity_id = 1
        self.alive_entities = set()
        self.entity_tags = {}
        self.components = {}

    def create_entity(self, tag=None):
        """Создаёт новую сущность и возвращает её id"""
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        self.alive_entities.add(entity_id)
        if tag is not None:
            self.entity_tags[entity_id] = tag
        return entity_id

    def destroy_entity(self, entity_id):
        """Удаляет сущность, её тег и все её компоненты"""
        self.alive_entities.discard(entity_id)
        self.entity_tags.pop(entity_id, None)
        for component_storage in self.components.values():
            component_storage.pop(entity_id, None)

    def add_component(self, entity_id, component):
        """Добавляет компонент существующей сущности"""
        if entity_id not in self.alive_entities:
            raise ValueError(f"Сущность с id '{entity_id}' не существует")

        component_type = type(component)
        if component_type not in self.components:
            self.components[component_type] = {}
        self.components[component_type][entity_id] = component

    def remove_component(self, entity_id, component_type):
        """Удаляет компонент указанного типа у сущности"""
        component_storage = self.components.get(component_type, {})
        component_storage.pop(entity_id, None)

    def get_component(self, entity_id, component_type):
        """Возвращает компонент указанного типа или None"""
        if entity_id not in self.alive_entities:
            return None
        return self.components.get(component_type, {}).get(entity_id)

    def has_component(self, entity_id, component_type):
        """Проверяет, есть ли у сущности компонент указанного типа"""
        return self.get_component(entity_id, component_type) is not None

    def get_entities_with(self, *component_types):
        """Возвращает сущности, у которых есть все перечисленные компоненты"""
        if not component_types:
            return set()

        entity_ids = self.alive_entities.copy()
        for component_type in component_types:
            component_storage = self.components.get(component_type)
            if component_storage is None:
                return set()
            entity_ids = entity_ids & set(component_storage.keys())

        return entity_ids & self.alive_entities

    def clear(self):
        """Очищает все сущности, теги и компоненты"""
        self.next_entity_id = 1
        self.alive_entities.clear()
        self.entity_tags.clear()
        self.components.clear()
