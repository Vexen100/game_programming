import unittest

import pygame

import settings
from src.world.tile_map import TileMap
from src.world.tile_types import (
    BRIDGE,
    DIRT,
    FLOOR,
    FOREST,
    GRASS,
    ROAD,
    RUINS_FLOOR,
    WALL,
    WATER,
)


class FakeResourceManager:
    def __init__(self):
        self.requested_tile_ids = []

    def get_tile_surface(self, tile_id, tile_size):
        self.requested_tile_ids.append(tile_id)
        surface = pygame.Surface((tile_size, tile_size))
        surface.fill(settings.UNKNOWN_TILE_COLOR)
        return surface


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

    def test_is_tile_blocked_returns_false_for_floor(self):
        self.assertFalse(self.tile_map.is_tile_blocked(1, 1))

    def test_floor_is_walkable(self):
        self.assertFalse(TileMap([[FLOOR]]).is_tile_blocked(0, 0))

    def test_new_walkable_tiles_are_not_blocked(self):
        tile_map = TileMap([[GRASS, DIRT, ROAD, RUINS_FLOOR, BRIDGE]])

        for tile_x in range(tile_map.width):
            self.assertFalse(tile_map.is_tile_blocked(tile_x, 0))

    def test_is_tile_blocked_returns_true_for_wall(self):
        self.assertTrue(self.tile_map.is_tile_blocked(0, 0))
        self.assertTrue(self.tile_map.is_tile_blocked(2, 2))

    def test_water_and_forest_are_blocked(self):
        tile_map = TileMap([[WATER, FOREST]])

        self.assertTrue(tile_map.is_tile_blocked(0, 0))
        self.assertTrue(tile_map.is_tile_blocked(1, 0))

    def test_is_tile_blocked_returns_true_for_out_of_bounds(self):
        self.assertTrue(self.tile_map.is_tile_blocked(-1, 1))
        self.assertTrue(self.tile_map.is_tile_blocked(4, 1))

    def test_unknown_out_of_bounds_is_blocked(self):
        self.assertTrue(self.tile_map.is_tile_blocked(-1, 0))
        self.assertTrue(self.tile_map.is_tile_blocked(0, -1))

    def test_is_point_blocked_returns_false_for_point_inside_floor(self):
        self.assertFalse(self.tile_map.is_point_blocked(33, 33))

    def test_is_point_blocked_returns_true_for_point_inside_wall(self):
        self.assertTrue(self.tile_map.is_point_blocked(0, 0))
        self.assertTrue(self.tile_map.is_point_blocked(65, 65))

    def test_is_point_blocked_returns_true_for_out_of_bounds(self):
        self.assertTrue(self.tile_map.is_point_blocked(-1, 0))

    def test_is_blocked_remains_pixel_coordinate_alias(self):
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

    def test_tile_map_draw_supports_new_tile_types(self):
        tile_map = TileMap([
            [GRASS, DIRT, ROAD],
            [RUINS_FLOOR, WATER, FOREST],
            [BRIDGE, WALL, 999],
        ])
        screen = pygame.Surface(
            (
                tile_map.width * settings.TILE_SIZE,
                tile_map.height * settings.TILE_SIZE,
            )
        )

        tile_map.draw(screen)

        self.assertEqual(
            screen.get_at((settings.TILE_SIZE // 2, settings.TILE_SIZE // 2))[:3],
            settings.GRASS_COLOR,
        )
        self.assertEqual(
            screen.get_at(
                (
                    settings.TILE_SIZE * 2 + settings.TILE_SIZE // 2,
                    settings.TILE_SIZE * 2 + settings.TILE_SIZE // 2,
                )
            )[:3],
            settings.UNKNOWN_TILE_COLOR,
        )

    def test_tile_map_draw_supports_resource_manager_fallback(self):
        tile_map = TileMap([[GRASS, ROAD]])
        resource_manager = FakeResourceManager()
        screen = pygame.Surface((settings.TILE_SIZE * 2, settings.TILE_SIZE))

        tile_map.draw(screen, resource_manager=resource_manager)

        self.assertEqual(resource_manager.requested_tile_ids, [GRASS, ROAD])


if __name__ == "__main__":
    unittest.main()
