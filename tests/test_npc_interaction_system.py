import unittest

import settings
from src.components.components import (
    NPC,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import NPCSettings, OutpostSettings
from src.events.game_events import QuestCompletedEvent
from src.systems.npc_interaction_system import NPCInteractionSystem


class FakeInteractInputManager:
    def was_pressed(self, action):
        return action == settings.INTERACT


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class TestNPCInteractionSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.event_bus = FakeEventBus()
        self.system = NPCInteractionSystem(self.event_bus)

    def create_player(self, x=0, y=0, defeated=False):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        if defeated:
            self.ecm.add_component(player, PlayerDefeated())
        return player

    def create_outpost(self, cleared=False):
        outpost = self.ecm.create_entity(tag="outpost")
        self.ecm.add_component(outpost, Outpost(radius=OutpostSettings.RADIUS, cleared=cleared))
        return outpost

    def create_npc(self, x=0, y=0, required_outpost_id=None):
        npc = self.ecm.create_entity(tag="npc")
        self.ecm.add_component(npc, Position(x, y))
        self.ecm.add_component(
            npc,
            Renderable(
                width=NPCSettings.SIZE,
                height=NPCSettings.SIZE,
                color=NPCSettings.ACTIVE_COLOR,
            ),
        )
        self.ecm.add_component(
            npc,
            NPC(
                interaction_radius=NPCSettings.INTERACTION_RADIUS,
                quest_id="clear_old_ruins_outpost",
                required_outpost_id=required_outpost_id,
            ),
        )
        return npc

    def test_player_near_npc_with_cleared_outpost_completes_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(len(self.event_bus.events), 1)
        self.assertIsInstance(self.event_bus.events[0], QuestCompletedEvent)
        self.assertEqual(self.event_bus.events[0].quest_id, "clear_old_ruins_outpost")
        self.assertEqual(self.event_bus.events[0].npc_id, npc)
        self.assertEqual(self.event_bus.events[0].region_id, "old_ruins")

    def test_uncleared_outpost_blocks_quest_completion(self):
        outpost = self.create_outpost(cleared=False)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_far_player_does_not_complete_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player(x=NPCSettings.INTERACTION_RADIUS + 20, y=0)

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_defeated_player_does_not_complete_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player(defeated=True)

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_completed_quest_does_not_publish_event_twice(self):
        outpost = self.create_outpost(cleared=True)
        self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")

        self.assertEqual(len(self.event_bus.events), 1)

    def test_npc_color_changes_when_quest_completed(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        renderable = self.ecm.get_component(npc, Renderable)

        self.assertEqual(renderable.color, NPCSettings.COMPLETED_COLOR)

    def test_update_without_player_does_not_crash(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_update_without_event_bus_completes_quest_without_event(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        system = NPCInteractionSystem()

        system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertTrue(npc_component.quest_completed)

    def test_update_without_region_id_completes_quest_without_event(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager())
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_npc_without_required_outpost_completes_by_interaction(self):
        npc = self.create_npc(required_outpost_id=None)
        self.create_player()

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins")
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(len(self.event_bus.events), 1)


if __name__ == "__main__":
    unittest.main()
