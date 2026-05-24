import unittest

from src.components.components import CapturePoint, Enemy, Position
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.systems.castle_wave_system import CastleWaveSystem
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class TestCastleWaveSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        self.tile_map = TileMap(
            [
                [WALL, WALL, WALL, WALL, WALL],
                [WALL, FLOOR, FLOOR, FLOOR, WALL],
                [WALL, FLOOR, FLOOR, FLOOR, WALL],
                [WALL, WALL, WALL, WALL, WALL],
            ]
        )
        self.system = CastleWaveSystem(
            spawn_tiles=[
                (1, 1),
                (2, 1),
            ],
            enemies_per_wave=2,
        )

    def create_capture_point(self, captured=False):
        capture_point_id = self.entity_factory.create_capture_point(32, 32)
        capture_point = self.ecm.get_component(capture_point_id, CapturePoint)
        capture_point.captured = captured
        capture_point.owner = "player" if captured else "enemy"
        return capture_point_id

    def test_update_without_captured_points_does_not_spawn_enemies(self):
        capture_point_ids = [
            self.create_capture_point(captured=False),
            self.create_capture_point(captured=False),
        ]

        spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(spawned_enemy_ids, [])
        self.assertEqual(self.ecm.get_entities_with(Enemy), set())

    def test_update_with_one_captured_point_spawns_wave(self):
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=False),
        ]

        spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(len(spawned_enemy_ids), 2)
        for enemy_id in spawned_enemy_ids:
            self.assertTrue(self.ecm.has_component(enemy_id, Enemy))
            self.assertTrue(self.ecm.has_component(enemy_id, Position))

    def test_repeated_update_for_same_capture_point_does_not_spawn_again(self):
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=False),
        ]

        first_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )
        second_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(len(first_spawned_enemy_ids), 2)
        self.assertEqual(second_spawned_enemy_ids, [])

    def test_update_with_all_capture_points_already_captured_does_not_spawn_wave(self):
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=True),
        ]

        spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(spawned_enemy_ids, [])

    def test_first_captured_point_spawns_wave_if_second_is_not_captured(self):
        first_capture_point_id = self.create_capture_point(captured=True)
        second_capture_point_id = self.create_capture_point(captured=False)

        spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            [first_capture_point_id, second_capture_point_id],
        )

        self.assertEqual(len(spawned_enemy_ids), 2)

    def test_later_final_capture_point_does_not_spawn_second_wave(self):
        first_capture_point_id = self.create_capture_point(captured=True)
        second_capture_point_id = self.create_capture_point(captured=False)
        capture_point_ids = [first_capture_point_id, second_capture_point_id]

        first_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )
        second_capture_point = self.ecm.get_component(second_capture_point_id, CapturePoint)
        second_capture_point.captured = True
        second_capture_point.owner = "player"
        second_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(len(first_spawned_enemy_ids), 2)
        self.assertEqual(second_spawned_enemy_ids, [])

    def test_reset_allows_wave_after_restart(self):
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=False),
        ]

        first_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )
        self.system.reset()
        second_spawned_enemy_ids = self.system.update(
            self.ecm,
            self.entity_factory,
            self.tile_map,
            capture_point_ids,
        )

        self.assertEqual(len(first_spawned_enemy_ids), 2)
        self.assertEqual(len(second_spawned_enemy_ids), 2)

    def test_update_raises_if_spawn_tile_is_blocked(self):
        system = CastleWaveSystem(spawn_tiles=[(0, 0)])
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=False),
        ]

        with self.assertRaisesRegex(ValueError, "No valid castle wave spawn tile"):
            system.update(
                self.ecm,
                self.entity_factory,
                self.tile_map,
                capture_point_ids,
            )

    def test_update_raises_if_spawn_tiles_are_empty(self):
        system = CastleWaveSystem(spawn_tiles=[])
        capture_point_ids = [
            self.create_capture_point(captured=True),
            self.create_capture_point(captured=False),
        ]

        with self.assertRaisesRegex(ValueError, "spawn tiles are not configured"):
            system.update(
                self.ecm,
                self.entity_factory,
                self.tile_map,
                capture_point_ids,
            )


if __name__ == "__main__":
    unittest.main()
