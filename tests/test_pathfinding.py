import unittest

from src.algorithms.pathfinding import find_path, manhattan_distance
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


class TestPathfinding(unittest.TestCase):
    def test_manhattan_distance(self):
        self.assertEqual(manhattan_distance((0, 0), (3, 4)), 7)

    def test_find_path_returns_start_when_start_is_goal(self):
        tile_map = FakeTileMap([[FLOOR]])

        self.assertEqual(find_path(tile_map, (0, 0), (0, 0)), [(0, 0)])

    def test_find_path_returns_empty_list_if_start_is_blocked(self):
        tile_map = FakeTileMap([[WALL, FLOOR]])

        self.assertEqual(find_path(tile_map, (0, 0), (1, 0)), [])

    def test_find_path_returns_empty_list_if_goal_is_blocked(self):
        tile_map = FakeTileMap([[FLOOR, WALL]])

        self.assertEqual(find_path(tile_map, (0, 0), (1, 0)), [])

    def test_find_path_returns_empty_list_if_goal_is_out_of_bounds(self):
        tile_map = FakeTileMap([[FLOOR, FLOOR]])

        self.assertEqual(find_path(tile_map, (0, 0), (2, 0)), [])

    def test_find_path_finds_path_on_empty_map(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
            ]
        )

        path = find_path(tile_map, (0, 0), (2, 0))

        self.assertGreater(len(path), 0)

    def test_find_path_starts_with_start_and_ends_with_goal(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
            ]
        )

        path = find_path(tile_map, (0, 0), (2, 2))

        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))

    def test_find_path_does_not_include_wall_tiles(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, WALL, FLOOR],
                [FLOOR, FLOOR, FLOOR],
            ]
        )

        path = find_path(tile_map, (0, 1), (2, 1))

        self.assertNotIn((1, 1), path)

    def test_find_path_goes_around_wall_through_gap(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
                [FLOOR, WALL, WALL, WALL, FLOOR],
                [FLOOR, FLOOR, FLOOR, WALL, FLOOR],
                [WALL, WALL, FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR, WALL, FLOOR],
            ]
        )

        path = find_path(tile_map, (0, 0), (4, 4))

        self.assertGreater(len(path), 0)
        self.assertNotIn((1, 1), path)
        self.assertNotIn((2, 1), path)
        self.assertNotIn((3, 1), path)

    def test_find_path_returns_empty_list_if_goal_is_closed_by_walls(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, WALL, WALL, WALL],
                [FLOOR, FLOOR, WALL, FLOOR, WALL],
                [FLOOR, FLOOR, WALL, WALL, WALL],
                [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
            ]
        )

        self.assertEqual(find_path(tile_map, (0, 0), (3, 2)), [])

    def test_find_path_does_not_use_diagonal_steps(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, WALL],
                [WALL, FLOOR],
            ]
        )

        self.assertEqual(find_path(tile_map, (0, 0), (1, 1)), [])

    def test_find_path_has_expected_length_on_simple_map(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR],
            ]
        )

        path = find_path(tile_map, (0, 0), (2, 2))

        self.assertEqual(len(path), 5)


if __name__ == "__main__":
    unittest.main()
