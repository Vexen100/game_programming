import unittest

from src.components.components import Enemy, Health, PlayerControlled, PlayerDefeated
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.player_death_system import PlayerDeathSystem


class TestPlayerDeathSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = PlayerDeathSystem()

    def create_player(self, health):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Health(current=health, maximum=100))
        return player

    def test_zero_health_player_gets_player_defeated(self):
        player = self.create_player(0)

        self.system.update(self.ecm)

        self.assertTrue(self.ecm.has_component(player, PlayerDefeated))

    def test_alive_player_does_not_get_player_defeated(self):
        player = self.create_player(10)

        self.system.update(self.ecm)

        self.assertFalse(self.ecm.has_component(player, PlayerDefeated))

    def test_player_defeated_is_not_added_twice(self):
        player = self.create_player(0)

        self.system.update(self.ecm)
        first_defeated = self.ecm.get_component(player, PlayerDefeated)
        self.system.update(self.ecm)
        second_defeated = self.ecm.get_component(player, PlayerDefeated)

        self.assertIs(first_defeated, second_defeated)

    def test_enemy_does_not_get_player_defeated(self):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Health(current=0, maximum=40))

        self.system.update(self.ecm)

        self.assertFalse(self.ecm.has_component(enemy, PlayerDefeated))


if __name__ == "__main__":
    unittest.main()
