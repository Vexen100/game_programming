import unittest

from src.components.components import Collider, Dead, Enemy, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.spatial_index_system import SpatialIndexSystem


class TestSpatialIndexSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = SpatialIndexSystem()

    def create_enemy(self, x=0, y=0, dead=False, with_position=True, with_collider=True):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())

        if with_position:
            self.ecm.add_component(enemy, Position(x, y))

        if with_collider:
            self.ecm.add_component(enemy, Collider(width=16, height=16, solid=True))

        if dead:
            self.ecm.add_component(enemy, Dead())

        return enemy

    def test_build_enemy_index_adds_living_enemies(self):
        enemy = self.create_enemy(10, 10)

        enemy_index = self.system.build_enemy_index(self.ecm, 200, 200, 32)

        self.assertIn(enemy, enemy_index.query_rect(10, 10, 16, 16))

    def test_build_enemy_index_skips_dead_enemies(self):
        enemy = self.create_enemy(10, 10, dead=True)

        enemy_index = self.system.build_enemy_index(self.ecm, 200, 200, 32)

        self.assertNotIn(enemy, enemy_index.query_rect(10, 10, 16, 16))

    def test_build_enemy_index_skips_enemy_without_collider(self):
        enemy = self.create_enemy(10, 10, with_collider=False)

        enemy_index = self.system.build_enemy_index(self.ecm, 200, 200, 32)

        self.assertNotIn(enemy, enemy_index.query_rect(10, 10, 16, 16))

    def test_build_enemy_index_skips_enemy_without_position(self):
        enemy = self.create_enemy(with_position=False)

        enemy_index = self.system.build_enemy_index(self.ecm, 200, 200, 32)

        self.assertNotIn(enemy, enemy_index.query_rect(0, 0, 200, 200))

    def test_query_empty_area_does_not_return_enemy(self):
        enemy = self.create_enemy(10, 10)

        enemy_index = self.system.build_enemy_index(self.ecm, 200, 200, 32)

        self.assertNotIn(enemy, enemy_index.query_rect(100, 100, 16, 16))


if __name__ == "__main__":
    unittest.main()
