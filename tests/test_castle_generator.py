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
            layout.final_room_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

    def assert_floor_tile(self, layout, tile):
        tile_x, tile_y = tile
        self.assertEqual(layout.matrix[tile_y][tile_x], FLOOR)

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

    def test_entrance_tile_is_floor(self):
        layout = self.create_layout()

        self.assert_floor_tile(layout, layout.entrance_tile)

    def test_final_room_tile_is_floor(self):
        layout = self.create_layout()

        self.assert_floor_tile(layout, layout.final_room_tile)

    def test_capture_point_tiles_are_floor(self):
        layout = self.create_layout()

        self.assertEqual(len(layout.capture_point_tiles), 2)
        for tile in layout.capture_point_tiles:
            self.assert_floor_tile(layout, tile)

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
