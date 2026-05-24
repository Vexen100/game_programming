import unittest

from src.algorithms import line_of_sight
from src.algorithms.line_of_sight import get_line_tiles, has_line_of_sight
from src.world.tile_types import FLOOR, WALL


class FakeTileMap:
    def __init__(self, matrix):
        self.matrix = matrix
        self.height = len(matrix)
        self.width = len(matrix[0])

    def is_tile_blocked(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return True

        return self.matrix[tile_y][tile_x] == WALL


class TestLineOfSight(unittest.TestCase):
    def test_get_line_tiles_returns_start_and_end(self):
        line = get_line_tiles((0, 0), (3, 0))

        self.assertEqual(line[0], (0, 0))
        self.assertEqual(line[-1], (3, 0))

    def test_get_line_tiles_horizontal_line(self):
        self.assertEqual(
            get_line_tiles((0, 0), (3, 0)),
            [(0, 0), (1, 0), (2, 0), (3, 0)],
        )

    def test_get_line_tiles_vertical_line(self):
        self.assertEqual(
            get_line_tiles((2, 0), (2, 3)),
            [(2, 0), (2, 1), (2, 2), (2, 3)],
        )

    def test_get_line_tiles_diagonal_line(self):
        self.assertEqual(
            get_line_tiles((0, 0), (3, 3)),
            [(0, 0), (1, 1), (2, 2), (3, 3)],
        )

    def test_has_line_of_sight_returns_true_for_same_free_tile(self):
        tile_map = FakeTileMap([[FLOOR]])

        self.assertTrue(has_line_of_sight(tile_map, (0, 0), (0, 0)))

    def test_has_line_of_sight_returns_false_if_start_is_blocked(self):
        tile_map = FakeTileMap([[WALL, FLOOR]])

        self.assertFalse(has_line_of_sight(tile_map, (0, 0), (1, 0)))

    def test_has_line_of_sight_returns_false_if_end_is_blocked(self):
        tile_map = FakeTileMap([[FLOOR, WALL]])

        self.assertFalse(has_line_of_sight(tile_map, (0, 0), (1, 0)))

    def test_has_line_of_sight_returns_false_if_wall_is_between_tiles(self):
        tile_map = FakeTileMap([[FLOOR, WALL, FLOOR]])

        self.assertFalse(has_line_of_sight(tile_map, (0, 0), (2, 0)))

    def test_has_line_of_sight_ignores_walls_next_to_line(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, WALL, FLOOR],
                [FLOOR, FLOOR, FLOOR],
            ]
        )

        self.assertTrue(has_line_of_sight(tile_map, (0, 0), (2, 0)))

    def test_has_line_of_sight_returns_false_if_end_is_out_of_bounds(self):
        tile_map = FakeTileMap([[FLOOR, FLOOR]])

        self.assertFalse(has_line_of_sight(tile_map, (0, 0), (2, 0)))

    def test_has_line_of_sight_does_not_depend_on_pygame(self):
        self.assertNotIn("pygame", line_of_sight.__dict__)


if __name__ == "__main__":
    unittest.main()
