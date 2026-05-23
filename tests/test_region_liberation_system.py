import unittest

import settings
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.events.game_events import RegionLiberatedEvent
from src.systems.region_liberation_system import RegionLiberationSystem
from src.world.region import PLAYER_CONTROL


class TestRegionLiberationSystem(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        self.event_bus = EventBus()
        self.system = RegionLiberationSystem(self.game_state)

    def test_region_liberated_event_marks_region_liberated(self):
        self.system.on_region_liberated(RegionLiberatedEvent(region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.liberated)

    def test_region_liberated_event_sets_player_control(self):
        self.system.on_region_liberated(RegionLiberatedEvent(region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.control_state, PLAYER_CONTROL)
        self.assertEqual(region.player_influence, 100)
        self.assertEqual(region.enemy_influence, 0)

    def test_unknown_region_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.system.on_region_liberated(RegionLiberatedEvent(region_id="missing"))

    def test_system_subscribes_to_event_bus(self):
        self.system.subscribe(self.event_bus)

        self.event_bus.publish(RegionLiberatedEvent(region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.liberated)


if __name__ == "__main__":
    unittest.main()
