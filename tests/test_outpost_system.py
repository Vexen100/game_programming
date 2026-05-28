import unittest

from src.algorithms.uniform_grid import UniformGrid
from src.components.components import (
    Collider,
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
import settings


class FakeInputManager:
    def __init__(self, pressed_action=None, held_action=None):
        self.pressed_action = pressed_action
        self.held_action = held_action

    def was_pressed(self, action):
        return action == self.pressed_action

    def is_pressed(self, action):
        return action == self.held_action


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

    def create_enemy_index(self, *enemy_ids):
        enemy_index = UniformGrid(width=400, height=400, cell_size=64)

        for enemy_id in enemy_ids:
            position = self.ecm.get_component(enemy_id, Position)
            collider = self.ecm.get_component(enemy_id, Collider)
            width = collider.width if collider is not None else 1
            height = collider.height if collider is not None else 1
            enemy_index.insert(enemy_id, position.x, position.y, width, height)

        return enemy_index

    def test_player_near_outpost_without_interact_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player()

        self.system.update(self.ecm, FakeInputManager(), region_id="old_ruins", dt=0.5)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_single_interact_press_without_hold_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player()

        self.system.update(
            self.ecm,
            FakeInputManager(pressed_action=settings.INTERACT),
            region_id="old_ruins",
            dt=2,
        )
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_holding_interact_increases_clear_progress(self):
        outpost = self.create_outpost()
        self.create_player()

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=0.4,
        )
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)
        self.assertAlmostEqual(outpost_component.clear_progress, 0.4)

    def test_player_near_outpost_with_held_interact_clears_after_duration(self):
        outpost = self.create_outpost()
        self.create_player()
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )
        renderable = self.ecm.get_component(outpost, Renderable)

        self.assertTrue(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, outpost_component.clear_duration)
        self.assertEqual(renderable.color, OutpostSettings.CLEARED_COLOR)

    def test_player_far_from_outpost_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player(x=200, y=0)
        outpost_component = self.ecm.get_component(outpost, Outpost)
        outpost_component.clear_progress = 0.5

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_living_enemy_near_outpost_blocks_clearing(self):
        outpost = self.create_outpost()
        self.create_player()
        self.create_enemy()
        outpost_component = self.ecm.get_component(outpost, Outpost)
        outpost_component.clear_progress = 0.5

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_living_enemy_near_outpost_blocks_clearing_with_spatial_index(self):
        outpost = self.create_outpost()
        self.create_player()
        enemy = self.create_enemy()
        enemy_index = self.create_enemy_index(enemy)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
            enemy_spatial_index=enemy_index,
        )

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_spatial_index_outpost_keeps_full_scan_boundary_semantics(self):
        outpost = self.create_outpost(radius=40)
        self.create_player()
        enemy = self.create_enemy(x=35, y=0)
        self.ecm.add_component(enemy, Collider(width=28, height=28, solid=True))
        enemy_index = self.create_enemy_index(enemy)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
            enemy_spatial_index=enemy_index,
        )

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(outpost_component.clear_progress, 0)

    def test_dead_enemy_near_outpost_does_not_block_clearing(self):
        outpost = self.create_outpost()
        self.create_player()
        self.create_enemy(dead=True)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )

        self.assertTrue(outpost_component.cleared)

    def test_dead_enemy_near_outpost_does_not_block_with_spatial_index(self):
        outpost = self.create_outpost()
        self.create_player()
        enemy = self.create_enemy(dead=True)
        enemy_index = self.create_enemy_index(enemy)
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
            enemy_spatial_index=enemy_index,
        )

        self.assertTrue(outpost_component.cleared)

    def test_defeated_player_does_not_clear_outpost(self):
        outpost = self.create_outpost()
        self.create_player(defeated=True)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=2,
        )
        outpost_component = self.ecm.get_component(outpost, Outpost)
        renderable = self.ecm.get_component(outpost, Renderable)

        self.assertFalse(outpost_component.cleared)
        self.assertEqual(self.event_bus.events, [])
        self.assertNotEqual(renderable.color, OutpostSettings.CLEARED_COLOR)

    def test_outpost_cleared_event_is_published_once(self):
        outpost = self.create_outpost()
        self.create_player()
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )
        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )

        self.assertEqual(len(self.event_bus.events), 1)
        self.assertIsInstance(self.event_bus.events[0], OutpostClearedEvent)
        self.assertEqual(self.event_bus.events[0].outpost_id, outpost)
        self.assertEqual(self.event_bus.events[0].region_id, "old_ruins")

    def test_already_cleared_outpost_does_not_publish_event_again(self):
        outpost = self.create_outpost()
        self.create_player()
        outpost_component = self.ecm.get_component(outpost, Outpost)
        outpost_component.cleared = True
        outpost_component.clear_progress = outpost_component.clear_duration

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=outpost_component.clear_duration,
        )

        self.assertEqual(self.event_bus.events, [])

    def test_zero_dt_does_not_finish_outpost_by_itself(self):
        outpost = self.create_outpost()
        self.create_player()
        outpost_component = self.ecm.get_component(outpost, Outpost)
        outpost_component.clear_progress = outpost_component.clear_duration - 0.1

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=0,
        )

        self.assertFalse(outpost_component.cleared)
        self.assertAlmostEqual(
            outpost_component.clear_progress,
            outpost_component.clear_duration - 0.1,
        )

    def test_update_without_player_does_not_crash(self):
        outpost = self.create_outpost()

        self.system.update(
            self.ecm,
            FakeInputManager(held_action=settings.INTERACT),
            region_id="old_ruins",
            dt=2,
        )
        outpost_component = self.ecm.get_component(outpost, Outpost)

        self.assertFalse(outpost_component.cleared)


if __name__ == "__main__":
    unittest.main()
