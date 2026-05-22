import unittest

import settings
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.events.game_events import EnemyKilledEvent, OutpostClearedEvent, QuestCompletedEvent
from src.systems.influence_system import InfluenceSystem


class TestInfluenceSystem(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        self.event_bus = EventBus()
        self.system = InfluenceSystem(self.game_state)
        self.system.subscribe(self.event_bus)

    def test_enemy_killed_increases_player_influence(self):
        self.event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 25)

    def test_enemy_killed_decreases_enemy_influence(self):
        self.event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.enemy_influence, 75)

    def test_influence_values_are_clamped(self):
        for enemy_id in range(1, 8):
            self.event_bus.publish(EnemyKilledEvent(enemy_id=enemy_id, region_id="old_ruins"))

        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 100)
        self.assertEqual(region.enemy_influence, 0)

    def test_low_enemy_influence_unlocks_assault(self):
        self.event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))
        self.event_bus.publish(EnemyKilledEvent(enemy_id=2, region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.assault_unlocked)

    def test_unknown_region_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="missing"))

    def test_outpost_cleared_changes_influence(self):
        self.event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 50)
        self.assertEqual(region.enemy_influence, 50)

    def test_outpost_cleared_unlocks_assault(self):
        self.event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="old_ruins"))
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.assault_unlocked)

    def test_outpost_cleared_unknown_region_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="missing"))

    def test_quest_completed_increases_player_influence(self):
        self.event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_old_ruins_outpost",
                npc_id=1,
                region_id="old_ruins",
            )
        )
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.player_influence, 25)

    def test_quest_completed_decreases_enemy_influence(self):
        self.event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_old_ruins_outpost",
                npc_id=1,
                region_id="old_ruins",
            )
        )
        region = self.game_state.get_region("old_ruins")

        self.assertEqual(region.enemy_influence, 75)

    def test_quest_completed_can_unlock_assault(self):
        self.event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="old_ruins"))
        self.event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_old_ruins_outpost",
                npc_id=1,
                region_id="old_ruins",
            )
        )
        region = self.game_state.get_region("old_ruins")

        self.assertTrue(region.assault_unlocked)

    def test_quest_completed_unknown_region_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.event_bus.publish(
                QuestCompletedEvent(
                    quest_id="clear_old_ruins_outpost",
                    npc_id=1,
                    region_id="missing",
                )
            )


if __name__ == "__main__":
    unittest.main()
