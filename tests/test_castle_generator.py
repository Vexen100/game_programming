import unittest

from src.algorithms.flood_fill import are_tiles_reachable
from src.world.castle_generator import CastleGenerator, CastleLayout
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class AlwaysInvalidCastleGenerator(CastleGenerator):
    def is_layout_valid(self, layout):
        return False


class TestCastleGenerator(unittest.TestCase):
    def create_layout(self, seed=1):
        return CastleGenerator(50, 35, seed=seed).generate()

    def important_tiles(self, layout):
        return [
            layout.entrance_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

    def assert_floor_tile(self, layout, tile):
        tile_x, tile_y = tile
        self.assertEqual(layout.matrix[tile_y][tile_x], FLOOR)

    def get_final_room(self, layout):
        for room in layout.rooms:
            if room.contains_tile(layout.final_room_tile):
                return room

        self.fail("Final room tile is not inside any room")

    def get_tile_distance(self, first_tile, second_tile):
        first_x, first_y = first_tile
        second_x, second_y = second_tile
        return abs(first_x - second_x) + abs(first_y - second_y)

    def test_castle_generator_returns_layout(self):
        layout = self.create_layout()

        self.assertIsInstance(layout, CastleLayout)

    def test_layout_matrix_has_requested_size(self):
        layout = self.create_layout()

        self.assertEqual(len(layout.matrix), 35)
        self.assertEqual(len(layout.matrix[0]), 50)

    def test_layout_contains_floor_and_walls(self):
        layout = self.create_layout()
        tiles = [
            tile
            for row in layout.matrix
            for tile in row
        ]

        self.assertIn(FLOOR, tiles)
        self.assertIn(WALL, tiles)

    def test_all_rooms_are_carved_as_floor(self):
        layout = self.create_layout()

        for room in layout.rooms:
            for tile_y in range(room.y, room.bottom):
                for tile_x in range(room.x, room.right):
                    self.assertEqual(layout.matrix[tile_y][tile_x], FLOOR)

    def test_corridors_are_carved_as_floor(self):
        layout = self.create_layout()

        for corridor in layout.corridors:
            for tile in corridor:
                self.assert_floor_tile(layout, tile)

    def test_corridors_are_wider_than_one_tile_by_default(self):
        layout = self.create_layout()

        has_widened_corridor_tile = False
        for corridor in layout.corridors:
            for tile_x, tile_y in corridor:
                widened_neighbors = (
                    (tile_x + 1, tile_y),
                    (tile_x, tile_y + 1),
                    (tile_x + 1, tile_y + 1),
                )
                for neighbor_x, neighbor_y in widened_neighbors:
                    if (
                        0 <= neighbor_y < len(layout.matrix)
                        and 0 <= neighbor_x < len(layout.matrix[0])
                        and layout.matrix[neighbor_y][neighbor_x] == FLOOR
                    ):
                        has_widened_corridor_tile = True
                        break

        self.assertTrue(has_widened_corridor_tile)

    def test_corridor_width_one_is_still_supported(self):
        layout = CastleGenerator(50, 35, seed=1, corridor_width=1).generate()

        for corridor in layout.corridors:
            for tile in corridor:
                self.assert_floor_tile(layout, tile)

    def test_invalid_corridor_width_raises_value_error(self):
        with self.assertRaises(ValueError):
            CastleGenerator(50, 35, corridor_width=0)

    def test_entrance_tile_is_floor(self):
        layout = self.create_layout()

        self.assert_floor_tile(layout, layout.entrance_tile)

    def test_final_room_tile_is_floor(self):
        layout = self.create_layout()

        self.assert_floor_tile(layout, layout.final_room_tile)

    def test_capture_point_tiles_are_floor(self):
        layout = self.create_layout()

        self.assertEqual(len(layout.capture_point_tiles), 3)
        for tile in layout.capture_point_tiles:
            self.assert_floor_tile(layout, tile)

    def test_final_room_tile_is_last_capture_point(self):
        layout = self.create_layout()

        self.assertEqual(layout.capture_point_tiles[-1], layout.final_room_tile)

    def test_enemy_spawn_tiles_are_floor(self):
        layout = self.create_layout()

        self.assertEqual(len(layout.enemy_spawn_tiles), 3)
        for tile in layout.enemy_spawn_tiles:
            self.assert_floor_tile(layout, tile)

    def test_wave_spawn_tiles_are_floor(self):
        layout = self.create_layout()

        self.assertEqual(len(layout.wave_spawn_tiles), 2)
        for tile in layout.wave_spawn_tiles:
            self.assert_floor_tile(layout, tile)

    def test_important_tiles_are_distinct(self):
        layout = self.create_layout()
        important_tiles = self.important_tiles(layout)

        self.assertEqual(len(important_tiles), len(set(important_tiles)))

    def test_important_tiles_are_reachable_from_entrance(self):
        layout = self.create_layout()
        target_tiles = [
            layout.final_room_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

        self.assertTrue(
            are_tiles_reachable(
                layout.to_tile_map(),
                layout.entrance_tile,
                target_tiles,
            )
        )

    def test_final_room_tile_is_still_reachable(self):
        layout = self.create_layout()

        self.assertTrue(
            are_tiles_reachable(
                layout.to_tile_map(),
                layout.entrance_tile,
                [layout.final_room_tile],
            )
        )

    def test_widened_corridors_keep_important_tiles_reachable(self):
        layout = self.create_layout()

        self.assertTrue(
            are_tiles_reachable(
                layout.to_tile_map(),
                layout.entrance_tile,
                self.important_tiles(layout),
            )
        )

    def test_each_capture_point_has_nearby_enemy_spawn(self):
        layout = self.create_layout()

        for capture_point_tile in layout.capture_point_tiles:
            self.assertTrue(
                any(
                    self.get_tile_distance(capture_point_tile, enemy_tile) <= 2
                    for enemy_tile in layout.enemy_spawn_tiles
                )
            )

    def test_final_capture_point_has_nearby_enemy_spawn(self):
        layout = self.create_layout()
        final_capture_point = layout.capture_point_tiles[-1]

        self.assertTrue(
            any(
                self.get_tile_distance(final_capture_point, enemy_tile) <= 2
                for enemy_tile in layout.enemy_spawn_tiles
            )
        )

    def test_enemy_spawns_are_not_all_in_final_room(self):
        layout = self.create_layout()
        final_room = self.get_final_room(layout)

        self.assertFalse(
            all(
                final_room.contains_tile(enemy_tile)
                for enemy_tile in layout.enemy_spawn_tiles
            )
        )

    def test_wave_spawn_tiles_are_reachable(self):
        layout = self.create_layout()

        self.assertTrue(
            are_tiles_reachable(
                layout.to_tile_map(),
                layout.entrance_tile,
                layout.wave_spawn_tiles,
            )
        )

    def test_wave_spawn_tiles_do_not_overlap_important_tiles(self):
        layout = self.create_layout()
        used_tiles = {
            layout.entrance_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
        }

        for wave_spawn_tile in layout.wave_spawn_tiles:
            self.assertNotIn(wave_spawn_tile, used_tiles)

    def test_wave_spawn_tiles_are_not_all_in_final_room(self):
        layout = self.create_layout()
        final_room = self.get_final_room(layout)

        self.assertFalse(
            all(
                final_room.contains_tile(wave_spawn_tile)
                for wave_spawn_tile in layout.wave_spawn_tiles
            )
        )

    def test_same_seed_generates_same_layout(self):
        first_layout = self.create_layout(seed=10)
        second_layout = self.create_layout(seed=10)

        self.assertEqual(first_layout.matrix, second_layout.matrix)
        self.assertEqual(first_layout.rooms, second_layout.rooms)
        self.assertEqual(first_layout.corridors, second_layout.corridors)
        self.assertEqual(
            self.important_tiles(first_layout),
            self.important_tiles(second_layout),
        )

    def test_different_seeds_can_generate_different_layouts(self):
        first_layout = self.create_layout(seed=10)
        second_layout = self.create_layout(seed=11)

        self.assertNotEqual(first_layout.matrix, second_layout.matrix)

    def test_layout_can_be_wrapped_in_tile_map(self):
        layout = self.create_layout()

        tile_map = layout.to_tile_map()

        self.assertIsInstance(tile_map, TileMap)
        self.assertEqual(tile_map.width, 50)
        self.assertEqual(tile_map.height, 35)

    def test_generator_raises_value_error_when_layout_cannot_be_generated(self):
        generator = AlwaysInvalidCastleGenerator(
            50,
            35,
            seed=1,
            max_attempts=2,
        )

        with self.assertRaises(ValueError):
            generator.generate()


if __name__ == "__main__":
    unittest.main()
