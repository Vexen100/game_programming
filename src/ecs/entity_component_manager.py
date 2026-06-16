class EntityComponentManager:
    """Хранит сущности, компоненты и теги ECS-слоя.

    """
    def __init__(self) -> None:
        """Инициализирует `EntityComponentManager` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.next_entity_id = 1
        self.alive_entities = set()
        self.entity_tags = {}
        self.components = {}

    def create_entity(self, tag=None):
        """Создает новую ECS-сущность и при необходимости назначает ей тег.

        Args:
            tag: Текстовая метка сущности.

        Returns:
            Идентификатор созданной сущности.
        """
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        self.alive_entities.add(entity_id)
        if tag is not None:
            self.entity_tags[entity_id] = tag
        return entity_id

    def destroy_entity(self, entity_id):
        """Удаляет сущность, ее компоненты и тег из ECS-хранилища.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.

        Returns:
            None.
        """
        self.alive_entities.discard(entity_id)
        self.entity_tags.pop(entity_id, None)
        for component_storage in self.components.values():
            component_storage.pop(entity_id, None)

    def add_component(self, entity_id, component):
        """Добавляет компонент к сущности.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            component: Компонент, который нужно добавить, проверить или обновить.

        Returns:
            None.
        """
        if entity_id not in self.alive_entities:
            raise ValueError(f"Сущность с id '{entity_id}' не существует")

        component_type = type(component)
        if component_type not in self.components:
            self.components[component_type] = {}
        self.components[component_type][entity_id] = component

    def remove_component(self, entity_id, component_type):
        """Удаляет компонент указанного типа у сущности.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            component_type: Класс компонента, по которому выполняется поиск.

        Returns:
            None.
        """
        component_storage = self.components.get(component_type, {})
        component_storage.pop(entity_id, None)

    def get_component(self, entity_id, component_type):
        """Возвращает компонент указанного типа у сущности.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            component_type: Класс компонента, по которому выполняется поиск.

        Returns:
            Компонент нужного типа или `None`, если он отсутствует.
        """
        if entity_id not in self.alive_entities:
            return None
        return self.components.get(component_type, {}).get(entity_id)

    def has_component(self, entity_id, component_type):
        """Проверяет, есть ли у сущности компонент указанного типа.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            component_type: Класс компонента, по которому выполняется поиск.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.get_component(entity_id, component_type) is not None

    def get_entities_with(self, *component_types):
        """Находит сущности, у которых есть все указанные компоненты.

        Args:
            *component_types: Типы компонентов, наличие которых нужно проверить.

        Returns:
            Список идентификаторов сущностей с нужными компонентами.
        """
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
        """Очищает накопленное состояние объекта.

        Returns:
            None.
        """
        self.next_entity_id = 1
        self.alive_entities.clear()
        self.entity_tags.clear()
        self.components.clear()
