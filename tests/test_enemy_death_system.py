import unittest

from src.components.components import Dead, Enemy, Health, PlayerControlled
from src.ecs.entity_component_manager import EntityComponentManager
from src.events.game_events import EnemyKilledEvent
from src.systems.enemy_death_system import EnemyDeathSystem


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


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

    def test_enemy_death_system_publishes_enemy_killed_event_once(self):
        event_bus = FakeEventBus()
        system = EnemyDeathSystem(event_bus)
        enemy = self.create_enemy(0)

        system.update(self.ecm, region_id="old_ruins")
        system.update(self.ecm, region_id="old_ruins")

        self.assertEqual(len(event_bus.events), 1)
        self.assertIsInstance(event_bus.events[0], EnemyKilledEvent)
        self.assertEqual(event_bus.events[0].enemy_id, enemy)
        self.assertEqual(event_bus.events[0].region_id, "old_ruins")


if __name__ == "__main__":
    unittest.main()
