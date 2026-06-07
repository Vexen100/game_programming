import unittest
import tempfile
from pathlib import Path

import pygame
import settings
from src.core.event_bus import EventBus
from src.core.game import Game
from src.core.game_state import GameState
from src.core.save_manager import SaveManager
from src.events.game_events import (
    EnemyKilledEvent,
    OutpostClearedEvent,
    QuestCompletedEvent,
    RegionLiberatedEvent,
)
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem
from src.systems.region_liberation_system import RegionLiberationSystem
from src.world.region import ENEMY_CONTROL, PLAYER_CONTROL


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id


class TestMVPVerticalSlice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def load_game_state(self):
        return GameState.load_from_file(settings.REGIONS_DATA_PATH)

    def test_initial_world_state_supports_first_playable_loop(self):
        game_state = self.load_game_state()
        border_forest = game_state.get_region("border_forest")
        old_ruins = game_state.get_region("old_ruins")
        mountain_mines = game_state.get_region("mountain_mines")

        self.assertTrue(border_forest.liberated)
        self.assertEqual(border_forest.control_state, PLAYER_CONTROL)
        self.assertTrue(old_ruins.unlocked)
        self.assertEqual(old_ruins.control_state, ENEMY_CONTROL)
        self.assertFalse(mountain_mines.unlocked)

        game_state.set_current_region("old_ruins")

        self.assertEqual(game_state.current_region_id, "old_ruins")

    def test_influence_events_unlock_assault_after_full_region_loop(self):
        game_state = self.load_game_state()
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)

        event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="old_ruins"))
        event_bus.publish(OutpostClearedEvent(outpost_id=2, region_id="old_ruins"))
        event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_north_ruins_outpost",
                npc_id=1,
                region_id="old_ruins",
            )
        )
        event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_east_supply_outpost",
                npc_id=2,
                region_id="old_ruins",
            )
        )
        region = game_state.get_region("old_ruins")
        self.assertEqual(region.enemy_influence, 30)
        self.assertFalse(region.assault_unlocked)

        event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))

        self.assertLessEqual(
            region.enemy_influence,
            InfluenceSystem.ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD,
        )
        self.assertTrue(region.assault_unlocked)

    def test_world_map_can_request_assault_after_unlock(self):
        game_state = self.load_game_state()
        old_ruins = game_state.get_region("old_ruins")
        old_ruins.assault_unlocked = True
        scene = WorldMapScene(game_state)
        scene.manager = FakeSceneManager()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.start_selected_assault()

        self.assertEqual(game_state.current_region_id, "old_ruins")
        self.assertEqual(scene.manager.requested_scene_id, settings.CASTLE_ASSAULT_SCENE)

    def test_castle_liberation_updates_game_state_through_event_bus(self):
        game_state = self.load_game_state()
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        liberation_system = RegionLiberationSystem(game_state)
        liberation_system.subscribe(event_bus)

        event_bus.publish(RegionLiberatedEvent("old_ruins"))
        old_ruins = game_state.get_region("old_ruins")
        mountain_mines = game_state.get_region("mountain_mines")

        self.assertTrue(old_ruins.liberated)
        self.assertEqual(old_ruins.control_state, PLAYER_CONTROL)
        self.assertTrue(mountain_mines.unlocked)
        self.assertEqual(mountain_mines.control_state, ENEMY_CONTROL)

    def test_full_event_level_vertical_slice(self):
        game_state = self.load_game_state()
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        liberation_system = RegionLiberationSystem(game_state)
        influence_system.subscribe(event_bus)
        liberation_system.subscribe(event_bus)

        event_bus.publish(OutpostClearedEvent(outpost_id=1, region_id="old_ruins"))
        event_bus.publish(OutpostClearedEvent(outpost_id=2, region_id="old_ruins"))
        event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_north_ruins_outpost",
                npc_id=1,
                region_id="old_ruins",
            )
        )
        event_bus.publish(
            QuestCompletedEvent(
                quest_id="clear_east_supply_outpost",
                npc_id=2,
                region_id="old_ruins",
            )
        )
        event_bus.publish(EnemyKilledEvent(enemy_id=1, region_id="old_ruins"))
        old_ruins = game_state.get_region("old_ruins")
        self.assertTrue(old_ruins.assault_unlocked)

        event_bus.publish(RegionLiberatedEvent("old_ruins"))
        mountain_mines = game_state.get_region("mountain_mines")

        self.assertTrue(game_state.get_region("old_ruins").liberated)
        self.assertTrue(mountain_mines.unlocked)
        self.assertEqual(mountain_mines.control_state, ENEMY_CONTROL)

    def test_save_load_and_continue_keep_liberated_vertical_slice_state(self):
        with tempfile.TemporaryDirectory() as directory:
            game_state = self.load_game_state()
            game_state.set_current_region("old_ruins")
            event_bus = EventBus()
            liberation_system = RegionLiberationSystem(game_state)
            liberation_system.subscribe(event_bus)
            event_bus.publish(RegionLiberatedEvent("old_ruins"))
            save_manager = SaveManager(Path(directory) / "save_1.json")

            save_manager.save(game_state)
            save_data = save_manager.load()

            self.assertTrue(save_data.game_state.get_region("old_ruins").liberated)
            self.assertTrue(save_data.game_state.get_region("mountain_mines").unlocked)

            game = object.__new__(Game)
            game.save_manager = save_manager
            game.scene_manager = FakeSceneManager()

            self.assertTrue(game.continue_game())
            self.assertTrue(game.game_state.get_region("old_ruins").liberated)
            self.assertTrue(game.game_state.get_region("mountain_mines").unlocked)
            self.assertEqual(game.scene_manager.requested_scene_id, settings.WORLD_MAP_SCENE)


if __name__ == "__main__":
    unittest.main()
