import unittest

from src.components.components import (
    Collider,
    Enemy,
    Health,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory


class TestEntityFactory(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)

    def test_create_player(self):
        player = self.entity_factory.create_player(x=100, y=100)

        self.assertIn(player, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(player, Position))
        self.assertTrue(self.ecm.has_component(player, Velocity))
        self.assertTrue(self.ecm.has_component(player, Collider))
        self.assertTrue(self.ecm.has_component(player, Renderable))
        self.assertTrue(self.ecm.has_component(player, Health))
        self.assertTrue(self.ecm.has_component(player, PlayerControlled))

    def test_create_enemy(self):
        enemy = self.entity_factory.create_enemy(x=200, y=200)

        self.assertIn(enemy, self.ecm.alive_entities)
        self.assertTrue(self.ecm.has_component(enemy, Position))
        self.assertTrue(self.ecm.has_component(enemy, Velocity))
        self.assertTrue(self.ecm.has_component(enemy, Collider))
        self.assertTrue(self.ecm.has_component(enemy, Renderable))
        self.assertTrue(self.ecm.has_component(enemy, Health))
        self.assertTrue(self.ecm.has_component(enemy, Enemy))
        self.assertFalse(self.ecm.has_component(enemy, PlayerControlled))


if __name__ == "__main__":
    unittest.main()
