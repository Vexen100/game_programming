import unittest

from src.components.components import Dead, Health, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.cleanup_system import CleanupSystem


class TestCleanupSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = CleanupSystem()

    def test_dead_entity_is_destroyed(self):
        entity = self.ecm.create_entity(tag="test")
        self.ecm.add_component(entity, Dead())
        self.ecm.add_component(entity, Position(10, 20))
        self.ecm.add_component(entity, Health(current=0, maximum=10))

        self.system.update(self.ecm)

        self.assertNotIn(entity, self.ecm.alive_entities)
        self.assertIsNone(self.ecm.get_component(entity, Dead))
        self.assertIsNone(self.ecm.get_component(entity, Position))
        self.assertIsNone(self.ecm.get_component(entity, Health))

    def test_alive_entity_is_not_destroyed(self):
        entity = self.ecm.create_entity(tag="test")
        self.ecm.add_component(entity, Position(10, 20))

        self.system.update(self.ecm)

        self.assertIn(entity, self.ecm.alive_entities)

    def test_no_dead_entities_does_not_crash(self):
        self.system.update(self.ecm)


if __name__ == "__main__":
    unittest.main()
