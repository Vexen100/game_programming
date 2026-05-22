import unittest

from src.core.event_bus import EventBus
from src.events.game_events import EnemyKilledEvent, OutpostClearedEvent


class TestEventBus(unittest.TestCase):
    def test_subscriber_receives_event(self):
        event_bus = EventBus()
        received = []

        event_bus.subscribe(EnemyKilledEvent, received.append)
        event = EnemyKilledEvent(enemy_id=1, region_id="old_ruins")
        event_bus.publish(event)

        self.assertEqual(received, [event])

    def test_unsubscribe_removes_subscriber(self):
        event_bus = EventBus()
        received = []

        event_bus.subscribe(EnemyKilledEvent, received.append)
        event_bus.unsubscribe(EnemyKilledEvent, received.append)
        event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))

        self.assertEqual(received, [])

    def test_multiple_subscribers_receive_event(self):
        event_bus = EventBus()
        first_received = []
        second_received = []

        event_bus.subscribe(EnemyKilledEvent, first_received.append)
        event_bus.subscribe(EnemyKilledEvent, second_received.append)
        event = EnemyKilledEvent(enemy_id=1, region_id="old_ruins")
        event_bus.publish(event)

        self.assertEqual(first_received, [event])
        self.assertEqual(second_received, [event])

    def test_publish_without_subscribers_does_not_crash(self):
        event_bus = EventBus()

        event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))

    def test_outpost_cleared_event_is_delivered_to_subscriber(self):
        event_bus = EventBus()
        received = []

        event_bus.subscribe(OutpostClearedEvent, received.append)
        event = OutpostClearedEvent(outpost_id=1, region_id="old_ruins")
        event_bus.publish(event)

        self.assertEqual(received, [event])


if __name__ == "__main__":
    unittest.main()
