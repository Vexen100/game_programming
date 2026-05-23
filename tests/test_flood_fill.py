import unittest

from src.algorithms.flood_fill import (
    are_tiles_reachable,
    get_reachable_tiles,
    is_tile_reachable,
)
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class TestFloodFill(unittest.TestCase):
    def setUp(self):
        matrix = [
            [WALL, WALL, WALL, WALL, WALL, WALL],
            [WALL, FLOOR, FLOOR, WALL, FLOOR, WALL],
            [WALL, WALL, FLOOR, WALL, WALL, WALL],
            [WALL, FLOOR, FLOOR, FLOOR, FLOOR, WALL],
            [WALL, WALL, WALL, WALL, WALL, WALL],
        ]
        self.tile_map = TileMap(matrix)
        self.start_tile = (1, 1)

    def test_get_reachable_tiles_includes_start_tile(self):
        reachable_tiles = get_reachable_tiles(self.tile_map, self.start_tile)

        self.assertIn(self.start_tile, reachable_tiles)

    def test_get_reachable_tiles_does_not_include_walls(self):
        reachable_tiles = get_reachable_tiles(self.tile_map, self.start_tile)

        self.assertNotIn((3, 1), reachable_tiles)
        self.assertNotIn((0, 0), reachable_tiles)

    def test_get_reachable_tiles_does_not_pass_through_walls(self):
        reachable_tiles = get_reachable_tiles(self.tile_map, self.start_tile)

        self.assertNotIn((4, 1), reachable_tiles)

    def test_is_tile_reachable_returns_true_for_reachable_target(self):
        self.assertTrue(is_tile_reachable(self.tile_map, self.start_tile, (4, 3)))

    def test_is_tile_reachable_returns_false_for_target_behind_wall(self):
        self.assertFalse(is_tile_reachable(self.tile_map, self.start_tile, (4, 1)))

    def test_is_tile_reachable_returns_false_for_blocked_target(self):
        self.assertFalse(is_tile_reachable(self.tile_map, self.start_tile, (3, 1)))

    def test_get_reachable_tiles_returns_empty_set_for_blocked_start(self):
        reachable_tiles = get_reachable_tiles(self.tile_map, (0, 0))

        self.assertEqual(reachable_tiles, set())

    def test_get_reachable_tiles_returns_empty_set_for_out_of_bounds_start(self):
        reachable_tiles = get_reachable_tiles(self.tile_map, (-1, 1))

        self.assertEqual(reachable_tiles, set())

    def test_are_tiles_reachable_returns_true_if_all_targets_are_reachable(self):
        self.assertTrue(
            are_tiles_reachable(self.tile_map, self.start_tile, [(2, 1), (4, 3)])
        )

    def test_are_tiles_reachable_returns_false_if_any_target_is_unreachable(self):
        self.assertFalse(
            are_tiles_reachable(self.tile_map, self.start_tile, [(2, 1), (4, 1)])
        )


if __name__ == "__main__":
    unittest.main()
