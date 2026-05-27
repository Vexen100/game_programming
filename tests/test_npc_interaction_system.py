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
    def __init__(self, pressed=False, held=True):
        self.pressed = pressed
        self.held = held

    def was_pressed(self, action):
        return action == settings.INTERACT and self.pressed

    def is_pressed(self, action):
        return action == settings.INTERACT and self.held


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

    def test_single_interact_press_without_hold_does_not_complete_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(
            self.ecm,
            FakeInteractInputManager(pressed=True, held=False),
            region_id="old_ruins",
            dt=2,
        )
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(npc_component.report_progress, 0)
        self.assertEqual(self.event_bus.events, [])

    def test_holding_interact_increases_report_progress(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=0.4,
        )
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertAlmostEqual(npc_component.report_progress, 0.4)

    def test_player_near_npc_with_cleared_outpost_completes_after_duration(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(npc_component.report_progress, npc_component.report_duration)
        self.assertEqual(len(self.event_bus.events), 1)
        self.assertIsInstance(self.event_bus.events[0], QuestCompletedEvent)
        self.assertEqual(self.event_bus.events[0].quest_id, "clear_old_ruins_outpost")
        self.assertEqual(self.event_bus.events[0].npc_id, npc)
        self.assertEqual(self.event_bus.events[0].region_id, "old_ruins")

    def test_uncleared_outpost_blocks_quest_completion(self):
        outpost = self.create_outpost(cleared=False)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)
        npc_component.report_progress = 0.4

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins", dt=2)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(npc_component.report_progress, 0)
        self.assertEqual(self.event_bus.events, [])

    def test_far_player_does_not_complete_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player(x=NPCSettings.INTERACTION_RADIUS + 20, y=0)
        npc_component = self.ecm.get_component(npc, NPC)
        npc_component.report_progress = 0.4

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins", dt=2)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(npc_component.report_progress, 0)
        self.assertEqual(self.event_bus.events, [])

    def test_defeated_player_does_not_complete_quest(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player(defeated=True)

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins", dt=2)
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_completed_quest_does_not_publish_event_twice(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )
        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )

        self.assertEqual(len(self.event_bus.events), 1)

    def test_already_completed_quest_does_not_publish_event_again(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)
        npc_component.quest_completed = True
        npc_component.report_progress = npc_component.report_duration

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )

        self.assertEqual(self.event_bus.events, [])

    def test_npc_color_changes_when_quest_completed(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )
        renderable = self.ecm.get_component(npc, Renderable)

        self.assertEqual(renderable.color, NPCSettings.COMPLETED_COLOR)

    def test_update_without_player_does_not_crash(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)

        self.system.update(self.ecm, FakeInteractInputManager(), region_id="old_ruins", dt=2)
        npc_component = self.ecm.get_component(npc, NPC)

        self.assertFalse(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_update_without_event_bus_completes_quest_without_event(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        system = NPCInteractionSystem()
        npc_component = self.ecm.get_component(npc, NPC)

        system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )

        self.assertTrue(npc_component.quest_completed)

    def test_update_without_region_id_completes_quest_without_event(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            dt=npc_component.report_duration,
        )

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(self.event_bus.events, [])

    def test_npc_without_required_outpost_completes_by_interaction(self):
        npc = self.create_npc(required_outpost_id=None)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=npc_component.report_duration,
        )

        self.assertTrue(npc_component.quest_completed)
        self.assertEqual(len(self.event_bus.events), 1)

    def test_zero_dt_does_not_finish_quest_by_itself(self):
        outpost = self.create_outpost(cleared=True)
        npc = self.create_npc(required_outpost_id=outpost)
        self.create_player()
        npc_component = self.ecm.get_component(npc, NPC)
        npc_component.report_progress = npc_component.report_duration - 0.1

        self.system.update(
            self.ecm,
            FakeInteractInputManager(),
            region_id="old_ruins",
            dt=0,
        )

        self.assertFalse(npc_component.quest_completed)
        self.assertAlmostEqual(
            npc_component.report_progress,
            npc_component.report_duration - 0.1,
        )


if __name__ == "__main__":
    unittest.main()
