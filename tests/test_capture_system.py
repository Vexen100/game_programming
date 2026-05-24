import unittest

from src.components.components import (
    CapturePoint,
    Dead,
    Enemy,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import CapturePointSettings
from src.events.game_events import CapturePointTakenEvent, RegionLiberatedEvent
from src.systems.capture_system import CaptureSystem


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class TestCaptureSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.event_bus = FakeEventBus()
        self.system = CaptureSystem(self.event_bus)

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

    def create_capture_point(self, x=0, y=0, progress=0, captured=False):
        capture_point = self.ecm.create_entity(tag="capture_point")
        self.ecm.add_component(capture_point, Position(x, y))
        self.ecm.add_component(
            capture_point,
            Renderable(
                width=CapturePointSettings.SIZE,
                height=CapturePointSettings.SIZE,
                color=CapturePointSettings.ENEMY_COLOR,
            ),
        )
        self.ecm.add_component(
            capture_point,
            CapturePoint(
                radius=CapturePointSettings.RADIUS,
                progress=progress,
                owner="player" if captured else "enemy",
                captured=captured,
            ),
        )
        return capture_point

    def test_player_near_capture_point_increases_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, CapturePointSettings.CAPTURE_SPEED)

    def test_far_player_does_not_increase_progress(self):
        capture_point = self.create_capture_point()
        self.create_player(x=CapturePointSettings.RADIUS + 20, y=0)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_living_enemy_near_capture_point_blocks_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_dead_enemy_near_capture_point_does_not_block_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy(dead=True)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, CapturePointSettings.CAPTURE_SPEED)

    def test_one_living_enemy_from_many_near_capture_point_blocks_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy(x=CapturePointSettings.RADIUS + 50, y=0)
        self.create_enemy(x=0, y=0)
        self.create_enemy(x=CapturePointSettings.RADIUS + 80, y=0, dead=True)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_many_dead_enemies_near_capture_point_do_not_block_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy(x=0, y=0, dead=True)
        self.create_enemy(x=20, y=0, dead=True)
        self.create_enemy(x=0, y=20, dead=True)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, CapturePointSettings.CAPTURE_SPEED)

    def test_near_enemy_blocks_progress_even_if_another_enemy_is_far(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy(x=CapturePointSettings.RADIUS + 100, y=0)
        self.create_enemy(x=0, y=0)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_many_far_enemies_do_not_block_progress(self):
        capture_point = self.create_capture_point()
        self.create_player()
        self.create_enemy(x=CapturePointSettings.RADIUS + 20, y=0)
        self.create_enemy(x=0, y=CapturePointSettings.RADIUS + 20)
        self.create_enemy(x=CapturePointSettings.RADIUS + 30, y=CapturePointSettings.RADIUS + 30)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, CapturePointSettings.CAPTURE_SPEED)

    def test_capture_point_becomes_captured_at_full_progress(self):
        capture_point = self.create_capture_point(progress=90)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertTrue(capture_point_component.captured)
        self.assertEqual(capture_point_component.owner, "player")
        self.assertEqual(capture_point_component.progress, 100)

    def test_capture_point_color_changes_when_captured(self):
        capture_point = self.create_capture_point(progress=90)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        renderable = self.ecm.get_component(capture_point, Renderable)

        self.assertEqual(renderable.color, CapturePointSettings.PLAYER_COLOR)

    def test_capture_point_taken_event_is_published_once(self):
        capture_point = self.create_capture_point(progress=90)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_events = [
            event for event in self.event_bus.events
            if isinstance(event, CapturePointTakenEvent)
        ]

        self.assertEqual(len(capture_events), 1)
        self.assertEqual(capture_events[0].capture_point_id, capture_point)
        self.assertEqual(capture_events[0].region_id, "old_ruins")

    def test_without_event_bus_or_region_id_captures_without_event(self):
        capture_point = self.create_capture_point(progress=90)
        self.create_player()
        system = CaptureSystem()

        system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertTrue(capture_point_component.captured)

    def test_without_region_id_captures_without_event(self):
        capture_point = self.create_capture_point(progress=90)
        self.create_player()

        self.system.update(self.ecm, dt=1)
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertTrue(capture_point_component.captured)
        self.assertEqual(self.event_bus.events, [])

    def test_update_without_player_does_not_crash(self):
        capture_point = self.create_capture_point()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_defeated_player_does_not_increase_progress(self):
        capture_point = self.create_capture_point()
        self.create_player(defeated=True)

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        capture_point_component = self.ecm.get_component(capture_point, CapturePoint)

        self.assertEqual(capture_point_component.progress, 0)

    def test_all_captured_points_publish_region_liberated_event(self):
        self.create_capture_point(captured=True)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")

        self.assertTrue(
            any(isinstance(event, RegionLiberatedEvent) for event in self.event_bus.events)
        )

    def test_region_liberated_event_is_published_once(self):
        self.create_capture_point(captured=True)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        self.system.update(self.ecm, dt=1, region_id="old_ruins")
        liberation_events = [
            event for event in self.event_bus.events
            if isinstance(event, RegionLiberatedEvent)
        ]

        self.assertEqual(len(liberation_events), 1)

    def test_uncaptured_point_blocks_region_liberated_event(self):
        self.create_capture_point(captured=True)
        self.create_capture_point(x=200, captured=False)
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")

        self.assertFalse(
            any(isinstance(event, RegionLiberatedEvent) for event in self.event_bus.events)
        )

    def test_no_capture_points_does_not_publish_region_liberated_event(self):
        self.create_player()

        self.system.update(self.ecm, dt=1, region_id="old_ruins")

        self.assertEqual(self.event_bus.events, [])


if __name__ == "__main__":
    unittest.main()
