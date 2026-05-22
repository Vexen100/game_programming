import unittest

from src.components.components import (
    Dead,
    Enemy,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import OutpostSettings
from src.events.game_events import OutpostClearedEvent
from src.systems.outpost_system import OutpostSystem


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class TestOutpostSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.event_bus = FakeEventBus()
        self.system = OutpostSystem(self.event_bus)

    def create_player(self, x=0, y=0, defeated=False):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        if defeated:
            self.ecm.add_component(player, PlayerDefeated())
        return player

    def create_enemy(self, x=0, y=0, dead=False):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Position(x, y))
        if dead:
            self.ecm.add_component(enemy, Dead())
        return enemy

    def create_outpost(self, x=0, y=0, radius=96):
        outpost = self.ecm.create_entity(tag="outpost")
        self.ecm.add_component(outpost, Position(x, y))
        self.ecm.add_component(
            outpost,
            Renderable(
                width=OutpostSettings.SIZE,
                height=OutpostSettings.SIZE,
                color=OutpostSettings.ENEMY_COLOR,
            ),
        )
        self.ecm.add_component(outpost, Outpost(radius=radius))
        return outpost

    def test_player_near_outpost_without_living_enemies_clears_outpost(self):
        outpost = self.create_outpost()
        self.create_player()

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)
        renderable = self.ecm.get_component(outpost, Renderable)

        self.assertTrue(outpost_component.cleared)
        self.assertEqual(renderable.color, OutpostSettings.CLEARED_COLOR)

    def test_player_far_from_outpost_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player(x=200, y=0)

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)

    def test_living_enemy_near_outpost_blocks_clearing(self):
        outpost = self.create_outpost()
        self.create_player()
        self.create_enemy()

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)

    def test_dead_enemy_near_outpost_does_not_block_clearing(self):
        outpost = self.create_outpost()
        self.create_player()
        self.create_enemy(dead=True)

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertTrue(outpost_component.cleared)

    def test_defeated_player_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player(defeated=True)

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)
        renderable = self.ecm.get_component(outpost, Renderable)

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(self.event_bus.events, [])
        self.assertNotEqual(renderable.color, OutpostSettings.CLEARED_COLOR)

    def test_outpost_cleared_event_is_published_once(self):
        outpost = self.create_outpost()
        self.create_player()

        self.system.update(self.ecm, region_id="old_ruins")
        self.system.update(self.ecm, region_id="old_ruins")

        self.assertEqual(len(self.event_bus.events), 1)
        self.assertIsInstance(self.event_bus.events[0], OutpostClearedEvent)
        self.assertEqual(self.event_bus.events[0].outpost_id, outpost)
        self.assertEqual(self.event_bus.events[0].region_id, "old_ruins")

    def test_update_without_player_does_not_crash(self):
        outpost = self.create_outpost()

        self.system.update(self.ecm, region_id="old_ruins")
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)


if __name__ == "__main__":
    unittest.main()
