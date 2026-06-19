import unittest

from src.algorithms.flood_fill import are_tiles_reachable, get_reachable_tiles, is_tile_reachable
from src.algorithms.line_of_sight import get_line_tiles, has_line_of_sight
from src.algorithms.pathfinding import find_path, manhattan_distance
from src.algorithms.uniform_grid import UniformGrid
from src.world.castle_generator import CastleGenerator
from src.world.region_layout import create_old_ruins_region_layout
from src.world.tile_map import TileMap
from src.world.tile_types import (
    BRIDGE,
    CASTLE_FLOOR,
    CASTLE_WALL,
    FLOOR,
    FOREST,
    GRASS,
    ROAD,
    WALKABLE_TILES,
    WALL,
    WATER,
)


class TestCoreWorldAlgorithms(unittest.TestCase):
    """Проверяет ключевое поведение: test core мир algorithms.

    """

    def make_path_map(self):
        """Создает тестовую карту для pathfinding.

        Returns:
            Результат выполнения `make_path_map`.
        """
        return TileMap(
            [
                [FLOOR, FLOOR, FLOOR, FLOOR],
                [FLOOR, WALL, WALL, FLOOR],
                [FLOOR, FLOOR, FLOOR, FLOOR],
            ]
        )

    def test_tile_map_converts_tile_and_pixel_coordinates(self):
        """Проверяет сценарий: тайл карта converts тайл and pixel coordinates.

        Returns:
            None.
        """
        tile_map = TileMap([[FLOOR, FLOOR]])

        x, y = tile_map.coord_tile_to_pixels(1, 0)

        self.assertEqual(tile_map.coord_pixels_to_tile(x, y), (1, 0))

    def test_tile_map_blocks_walls_and_out_of_bounds(self):
        """Проверяет сценарий: тайл карта blocks walls and out of bounds.

        Returns:
            None.
        """
        tile_map = TileMap([[FLOOR, WALL]])

        self.assertFalse(tile_map.is_tile_blocked(0, 0))
        self.assertTrue(tile_map.is_tile_blocked(1, 0))
        self.assertTrue(tile_map.is_tile_blocked(-1, 0))

    def test_tile_map_rect_blocking_detects_wall_overlap(self):
        """Проверяет сценарий: тайл карта прямоугольник blocking detects wall overlap.

        Returns:
            None.
        """
        tile_map = TileMap([[FLOOR, WALL]])

        self.assertTrue(tile_map.is_rect_blocked(31, 0, 4, 4))

    def test_a_star_finds_path_around_wall(self):
        """Проверяет сценарий: a star finds путь around wall.

        Returns:
            None.
        """
        path = find_path(self.make_path_map(), (0, 0), (3, 0))

        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (3, 0))
        self.assertNotIn((1, 1), path)

    def test_a_star_returns_empty_when_goal_blocked(self):
        """Проверяет сценарий: a star returns empty when goal blocked.

        Returns:
            None.
        """
        path = find_path(self.make_path_map(), (0, 0), (1, 1))

        self.assertEqual(path, [])

    def test_manhattan_distance_counts_tile_steps(self):
        """Проверяет сценарий: manhattan дистанция counts тайл steps.

        Returns:
            None.
        """
        self.assertEqual(manhattan_distance((1, 2), (4, 6)), 7)

    def test_flood_fill_finds_reachable_area(self):
        """Проверяет сценарий: flood fill finds reachable area.

        Returns:
            None.
        """
        reachable = get_reachable_tiles(self.make_path_map(), (0, 0))

        self.assertIn((3, 2), reachable)
        self.assertNotIn((1, 1), reachable)

    def test_flood_fill_reports_unreachable_target(self):
        """Проверяет сценарий: flood fill reports unreachable target.

        Returns:
            None.
        """
        tile_map = TileMap([[FLOOR, WALL, FLOOR]])

        self.assertFalse(is_tile_reachable(tile_map, (0, 0), (2, 0)))

    def test_flood_fill_validates_multiple_targets(self):
        """Проверяет сценарий: flood fill validates multiple targets.

        Returns:
            None.
        """
        tile_map = self.make_path_map()

        self.assertTrue(are_tiles_reachable(tile_map, (0, 0), [(3, 0), (3, 2)]))

    def test_line_of_sight_lists_line_tiles(self):
        """Проверяет сценарий: линия of sight lists линия тайлы.

        Returns:
            None.
        """
        self.assertEqual(get_line_tiles((0, 0), (2, 0)), [(0, 0), (1, 0), (2, 0)])

    def test_line_of_sight_is_blocked_by_wall(self):
        """Проверяет сценарий: линия of sight is blocked by wall.

        Returns:
            None.
        """
        tile_map = TileMap([[FLOOR, WALL, FLOOR]])

        self.assertFalse(has_line_of_sight(tile_map, (0, 0), (2, 0)))

    def test_uniform_grid_query_rect_finds_inserted_objects(self):
        """Проверяет сценарий: uniform сетка query прямоугольник finds inserted objects.

        Returns:
            None.
        """
        grid = UniformGrid(width=100, height=100, cell_size=20)
        grid.insert(1, 10, 10, 8, 8)
        grid.insert(2, 80, 80, 8, 8)

        self.assertEqual(grid.query_rect(0, 0, 30, 30), {1})

    def test_uniform_grid_query_radius_filters_by_distance(self):
        """Проверяет сценарий: uniform сетка query радиус filters by дистанция.

        Returns:
            None.
        """
        grid = UniformGrid(width=100, height=100, cell_size=20)
        grid.insert(1, 10, 10, 4, 4)
        grid.insert(2, 50, 50, 4, 4)

        self.assertEqual(grid.query_radius(12, 12, 10), {1})

    def test_uniform_grid_rejects_invalid_size(self):
        """Проверяет сценарий: uniform сетка rejects invalid size.

        Returns:
            None.
        """
        with self.assertRaises(ValueError):
            UniformGrid(width=0, height=100, cell_size=20)

    def test_castle_generator_is_deterministic_for_seed(self):
        """Проверяет сценарий: замок generator is deterministic for seed.

        Returns:
            None.
        """
        first = CastleGenerator(48, 36, seed=42).generate()
        second = CastleGenerator(48, 36, seed=42).generate()

        self.assertEqual(first.fingerprint(), second.fingerprint())

    def test_castle_generator_places_important_tiles_on_floor(self):
        """Проверяет сценарий: замок generator places важные тайлы on пол.

        Returns:
            None.
        """
        layout = CastleGenerator(48, 36, seed=7).generate()
        important_tiles = [
            layout.entrance_tile,
            layout.final_room_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

        for tile_x, tile_y in important_tiles:
            self.assertIn(layout.matrix[tile_y][tile_x], WALKABLE_TILES)

    def test_castle_layout_to_tile_map_copies_matrix(self):
        """Проверяет сценарий: замок layout to тайл карта copies matrix.

        Returns:
            None.
        """
        layout = CastleGenerator(48, 36, seed=11).generate()

        tile_map = layout.to_tile_map()
        tile_map.matrix[layout.entrance_tile[1]][layout.entrance_tile[0]] = CASTLE_WALL

        self.assertNotEqual(
            layout.matrix[layout.entrance_tile[1]][layout.entrance_tile[0]],
            CASTLE_WALL,
        )

    def test_old_ruins_layout_contains_core_content(self):
        """Проверяет сценарий: old ruins layout contains core content.

        Returns:
            None.
        """
        layout = create_old_ruins_region_layout()
        tile_values = {tile for row in layout.matrix for tile in row}

        self.assertEqual(layout.player_spawn_tile, (5, 5))
        self.assertGreaterEqual(len(layout.enemy_spawns), 6)
        self.assertEqual(len(layout.outposts), 2)
        self.assertEqual(len(layout.npcs), 2)
        self.assertTrue({GRASS, ROAD, WATER, FOREST}.issubset(tile_values))

    def test_old_ruins_important_tiles_are_reachable(self):
        """Проверяет сценарий: old ruins важные тайлы are reachable.

        Returns:
            None.
        """
        layout = create_old_ruins_region_layout()
        tile_map = TileMap(layout.matrix)
        important_tiles = (
            [spawn.tile for spawn in layout.enemy_spawns]
            + [outpost.tile for outpost in layout.outposts]
            + [npc.tile for npc in layout.npcs]
        )

        self.assertTrue(are_tiles_reachable(tile_map, layout.player_spawn_tile, important_tiles))
