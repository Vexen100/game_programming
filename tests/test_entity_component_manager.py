import unittest

from src.components.components import Health, Position, Velocity
from src.ecs.entity_component_manager import EntityComponentManager


class TestEntityComponentManager(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()

    def test_create_entity(self):
        entity = self.ecm.create_entity(tag="player")

        self.assertIsInstance(entity, int)
        self.assertIn(entity, self.ecm.alive_entities)
        self.assertEqual(self.ecm.entity_tags[entity], "player")

    def test_add_component_and_get_component(self):
        entity = self.ecm.create_entity()
        position = Position(10, 20)

        self.ecm.add_component(entity, position)

        self.assertIs(self.ecm.get_component(entity, Position), position)
        self.assertIsNone(self.ecm.get_component(entity, Velocity))

    def test_has_component(self):
        entity = self.ecm.create_entity()
        self.ecm.add_component(entity, Position(10, 20))

        self.assertTrue(self.ecm.has_component(entity, Position))
        self.assertFalse(self.ecm.has_component(entity, Velocity))

    def test_get_entities_with(self):
        entity_with_all = self.ecm.create_entity()
        entity_without_health = self.ecm.create_entity()

        self.ecm.add_component(entity_with_all, Position(10, 20))
        self.ecm.add_component(entity_with_all, Health(100, 100))
        self.ecm.add_component(entity_without_health, Position(30, 40))

        self.assertIn(entity_with_all, self.ecm.get_entities_with(Position, Health))
        self.assertNotIn(entity_without_health, self.ecm.get_entities_with(Position, Health))
        self.assertEqual(self.ecm.get_entities_with(), set())

    def test_destroy_entity(self):
        entity = self.ecm.create_entity(tag="test")
        self.ecm.add_component(entity, Position(10, 20))

        self.ecm.destroy_entity(entity)

        self.assertNotIn(entity, self.ecm.alive_entities)
        self.assertNotIn(entity, self.ecm.entity_tags)
        self.assertIsNone(self.ecm.get_component(entity, Position))
        self.assertNotIn(entity, self.ecm.get_entities_with(Position))

    def test_clear(self):
        entity = self.ecm.create_entity(tag="test")
        self.ecm.add_component(entity, Position(10, 20))

        self.ecm.clear()

        self.assertEqual(self.ecm.next_entity_id, 1)
        self.assertEqual(self.ecm.alive_entities, set())
        self.assertEqual(self.ecm.entity_tags, {})
        self.assertEqual(self.ecm.components, {})


if __name__ == "__main__":
    unittest.main()
