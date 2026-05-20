import unittest

from src.components.components import Dead, Enemy, Health, PlayerControlled
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.enemy_death_system import EnemyDeathSystem


class TestEnemyDeathSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = EnemyDeathSystem()

    def create_enemy(self, health):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Health(current=health, maximum=40))
        return enemy

    def test_dead_enemy_gets_dead_component(self):
        enemy = self.create_enemy(0)

        self.system.update(self.ecm)

        self.assertTrue(self.ecm.has_component(enemy, Dead))

    def test_alive_enemy_does_not_get_dead_component(self):
        enemy = self.create_enemy(10)

        self.system.update(self.ecm)

        self.assertFalse(self.ecm.has_component(enemy, Dead))

    def test_dead_component_is_not_added_twice(self):
        enemy = self.create_enemy(0)

        self.system.update(self.ecm)
        first_dead = self.ecm.get_component(enemy, Dead)
        self.system.update(self.ecm)
        second_dead = self.ecm.get_component(enemy, Dead)

        self.assertIs(first_dead, second_dead)

    def test_player_is_not_marked_dead_yet(self):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Health(current=0, maximum=100))

        self.system.update(self.ecm)

        self.assertFalse(self.ecm.has_component(player, Dead))


if __name__ == "__main__":
    unittest.main()
