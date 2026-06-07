import unittest

import settings
from src.algorithms.flood_fill import are_tiles_reachable
from src.entities.entities_settings import OutpostSettings
from src.world.region_layout import create_old_ruins_region_layout
from src.world.tile_map import TileMap
from src.world.tile_types import BLOCKING_TILES


class TestRegionLayout(unittest.TestCase):
    def setUp(self):
        self.layout = create_old_ruins_region_layout()
        self.tile_map = TileMap(self.layout.matrix)

    def test_old_ruins_layout_is_larger_than_viewport(self):
        screen_tiles_width = settings.SCREEN_WIDTH // settings.TILE_SIZE
        screen_tiles_height = settings.SCREEN_HEIGHT // settings.TILE_SIZE

        self.assertGreater(self.tile_map.width, screen_tiles_width)
        self.assertGreater(self.tile_map.height, screen_tiles_height)

    def test_old_ruins_layout_uses_multiple_tile_types(self):
        tile_types = {tile for row in self.layout.matrix for tile in row}

        self.assertGreaterEqual(len(tile_types), 5)

    def test_old_ruins_layout_has_two_outposts(self):
        self.assertEqual(len(self.layout.outposts), 2)

    def test_old_ruins_layout_has_two_npcs(self):
        self.assertEqual(len(self.layout.npcs), 2)

    def test_old_ruins_layout_has_at_least_seven_enemies(self):
        self.assertGreaterEqual(len(self.layout.enemy_spawns), 7)

    def test_old_ruins_layout_important_tiles_are_reachable(self):
        target_tiles = []

        for enemy_spawn in self.layout.enemy_spawns:
            target_tiles.append(enemy_spawn.tile)
            target_tiles.extend(enemy_spawn.patrol_tiles)

        for outpost in self.layout.outposts:
            target_tiles.append(outpost.tile)

        for npc in self.layout.npcs:
            target_tiles.append(npc.tile)

        self.assertTrue(
            are_tiles_reachable(
                self.tile_map,
                self.layout.player_spawn_tile,
                target_tiles,
            )
        )

    def test_old_ruins_layout_outposts_are_not_near_spawn(self):
        for outpost in self.layout.outposts:
            self.assertGreater(
                self.get_tile_distance(outpost.tile, self.layout.player_spawn_tile),
                4,
            )

    def test_old_ruins_layout_npcs_are_not_near_spawn(self):
        for npc in self.layout.npcs:
            self.assertGreater(
                self.get_tile_distance(npc.tile, self.layout.player_spawn_tile),
                4,
            )

    def test_old_ruins_layout_outposts_have_guard_enemies(self):
        guard_radius_tiles = OutpostSettings.RADIUS // settings.TILE_SIZE

        for outpost in self.layout.outposts:
            has_guard = any(
                self.get_tile_distance(outpost.tile, enemy_spawn.tile)
                <= guard_radius_tiles
                for enemy_spawn in self.layout.enemy_spawns
            )

            self.assertTrue(has_guard)

    def test_old_ruins_layout_patrol_routes_are_reachable(self):
        for enemy_spawn in self.layout.enemy_spawns:
            for tile_x, tile_y in enemy_spawn.patrol_tiles:
                self.assertNotIn(self.layout.matrix[tile_y][tile_x], BLOCKING_TILES)
                self.assertTrue(
                    are_tiles_reachable(
                        self.tile_map,
                        self.layout.player_spawn_tile,
                        [enemy_spawn.tile, (tile_x, tile_y)],
                    )
                )

    def get_tile_distance(self, first_tile, second_tile):
        first_x, first_y = first_tile
        second_x, second_y = second_tile
        return abs(first_x - second_x) + abs(first_y - second_y)


if __name__ == "__main__":
    unittest.main()
