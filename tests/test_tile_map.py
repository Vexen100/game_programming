import unittest

from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class TestTileMap(unittest.TestCase):
    def setUp(self):
        matrix = [
            [WALL, WALL, WALL, WALL],
            [WALL, FLOOR, FLOOR, WALL],
            [WALL, FLOOR, WALL, WALL],
            [WALL, WALL, WALL, WALL],
        ]
        self.tile_map = TileMap(matrix)

    def test_coord_tile_to_pixels(self):
        self.assertEqual(self.tile_map.coord_tile_to_pixels(0, 0), (0, 0))
        self.assertEqual(self.tile_map.coord_tile_to_pixels(2, 3), (64, 96))

    def test_coord_pixels_to_tile(self):
        self.assertEqual(self.tile_map.coord_pixels_to_tile(0, 0), (0, 0))
        self.assertEqual(self.tile_map.coord_pixels_to_tile(33, 65), (1, 2))

    def test_is_blocked(self):
        self.assertTrue(self.tile_map.is_blocked(0, 0))
        self.assertFalse(self.tile_map.is_blocked(33, 33))
        self.assertTrue(self.tile_map.is_blocked(-1, 0))

    def test_is_rect_blocked(self):
        self.assertFalse(self.tile_map.is_rect_blocked(32, 32, 16, 16))
        self.assertTrue(self.tile_map.is_rect_blocked(64, 64, 16, 16))
        self.assertTrue(self.tile_map.is_rect_blocked(-1, 32, 16, 16))

    def test_is_rect_blocked_checks_tiles_inside_rect(self):
        matrix = [
            [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
            [FLOOR, FLOOR, WALL, FLOOR, FLOOR],
            [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
        ]
        tile_map = TileMap(matrix)

        self.assertTrue(tile_map.is_rect_blocked(32, 0, 96, 96))


if __name__ == "__main__":
    unittest.main()
