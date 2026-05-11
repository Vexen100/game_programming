class EntityComponentManager:
    def __init__(self) -> None:
        self.next_eid = 0
        self.components = {}  # {comp_type: {eid: component}}
        self.tags = {}

    def create_entity(self, tag=None):
        eid = self.next_eid
        self.next_eid += 1
        self.tags[eid] = tag
        return eid

    def delete_entity(self, eid):
        for comp_type in self.components:
            self.components.get(comp_type, {}).pop(eid, None)
        self.tags.pop(eid, None)

    def add_component(self, eid, component):
        if eid not in self.tags:
            raise ValueError(f"Нет такой действующей сущности с eid = {eid}")
        comp_type = type(component)
        if comp_type not in self.components:
            self.components[comp_type] = {}
        self.components[comp_type][eid] = component

    def remove_component(self, eid, comp_type):
        eids = self.components.get(comp_type, {})  # словарь eid с этим компонентом
        eids.pop(eid, None)

    def get_component(self, eid, comp_type):
        component = self.components.get(comp_type, {}).get(eid)
        return component

    def get_all_with_comp_types(self, *comp_types):
        if not comp_types:
            return []
        result = set(self.components.get(comp_types[0], {}).keys())
        for comp_type in comp_types[1:]:
            eids = self.components.get(comp_type, {}).keys()  # set-like объект, пересекать можно
            if not eids:  # нет такого компонента вообще ни у кого
                return []
            result = result & eids
        return sorted(result)

    def clear_all_entities(self):
        """Очищает все сущности"""
        self.next_eid = 0
        self.components.clear()
        self.tags.clear()
