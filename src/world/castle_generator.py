import random
from dataclasses import dataclass

from src.algorithms.bsp import BSPGenerator, RectInt
from src.algorithms.flood_fill import are_tiles_reachable
from src.world.tile_types import FLOOR, WALL


@dataclass
class CastleLayout:
    matrix: list[list[int]]
    rooms: list[RectInt]
    corridors: list[list[tuple[int, int]]]
    entrance_tile: tuple[int, int]
    final_room_tile: tuple[int, int]
    capture_point_tiles: list[tuple[int, int]]
    enemy_spawn_tiles: list[tuple[int, int]]
    wave_spawn_tiles: list[tuple[int, int]]
    seed: int | None = None

    def to_tile_map(self):
        from src.world.tile_map import TileMap

        return TileMap(self.matrix)


class CastleGenerator:
    def __init__(
        self,
        width,
        height,
        seed=None,
        min_leaf_size=8,
        max_depth=4,
        min_room_size=4,
        room_margin=1,
        max_attempts=20,
    ):
        self.width = width
        self.height = height
        self.seed = seed
        self.min_leaf_size = min_leaf_size
        self.max_depth = max_depth
        self.min_room_size = min_room_size
        self.room_margin = room_margin
        self.max_attempts = max_attempts

        self.validate_parameters()

    def validate_parameters(self):
        if self.max_attempts < 1:
            raise ValueError("CastleGenerator max_attempts must be at least 1")

        BSPGenerator(
            self.width,
            self.height,
            min_leaf_size=self.min_leaf_size,
            max_depth=self.max_depth,
            min_room_size=self.min_room_size,
            room_margin=self.room_margin,
            seed=self.seed,
        )

    def generate(self):
        attempt_rng = random.Random(self.seed)
        last_error = None

        for _ in range(self.max_attempts):
            attempt_seed = attempt_rng.randrange(1_000_000_000)

            try:
                layout = self.generate_attempt(attempt_seed)
            except ValueError as error:
                last_error = error
                continue

            if self.is_layout_valid(layout):
                return layout

        raise ValueError("Unable to generate valid castle layout") from last_error

    def generate_attempt(self, attempt_seed):
        rng = random.Random(attempt_seed)
        bsp = BSPGenerator(
            self.width,
            self.height,
            min_leaf_size=self.min_leaf_size,
            max_depth=self.max_depth,
            min_room_size=self.min_room_size,
            room_margin=self.room_margin,
            seed=attempt_seed,
        )
        root = bsp.generate_tree()
        bsp.create_rooms(root)

        rooms = self.sort_rooms(bsp.get_rooms(root))
        if not rooms:
            raise ValueError("Castle layout has no rooms")

        matrix = self.create_wall_matrix()
        self.carve_rooms(matrix, rooms)
        corridors = self.carve_corridors(matrix, rooms, rng)

        entrance_tile = self.choose_entrance_tile(rooms)
        final_room_tile = self.choose_final_room_tile(
            rooms,
            matrix,
            entrance_tile,
        )
        capture_point_tiles = self.choose_capture_point_tiles(
            rooms,
            matrix,
            entrance_tile,
            final_room_tile,
        )
        enemy_spawn_tiles = self.choose_enemy_spawn_tiles(
            rooms,
            matrix,
            entrance_tile,
            final_room_tile,
            capture_point_tiles,
        )
        wave_spawn_tiles = self.choose_wave_spawn_tiles(
            rooms,
            matrix,
            entrance_tile,
            final_room_tile,
            capture_point_tiles,
            enemy_spawn_tiles,
        )

        return CastleLayout(
            matrix=matrix,
            rooms=rooms,
            corridors=corridors,
            entrance_tile=entrance_tile,
            final_room_tile=final_room_tile,
            capture_point_tiles=capture_point_tiles,
            enemy_spawn_tiles=enemy_spawn_tiles,
            wave_spawn_tiles=wave_spawn_tiles,
            seed=self.seed,
        )

    def create_wall_matrix(self):
        return [
            [WALL for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def carve_rooms(self, matrix, rooms):
        for room in rooms:
            for tile_y in range(room.y, room.bottom):
                for tile_x in range(room.x, room.right):
                    matrix[tile_y][tile_x] = FLOOR

    def carve_corridors(self, matrix, rooms, rng):
        corridors = []

        for index in range(len(rooms) - 1):
            start_tile = rooms[index].center
            end_tile = rooms[index + 1].center
            horizontal_first = rng.choice([True, False])
            corridor = self.create_l_corridor(
                start_tile,
                end_tile,
                horizontal_first,
            )

            for tile_x, tile_y in corridor:
                if self.is_in_bounds((tile_x, tile_y)):
                    matrix[tile_y][tile_x] = FLOOR

            corridors.append(corridor)

        return corridors

    def create_l_corridor(self, start_tile, end_tile, horizontal_first):
        start_x, start_y = start_tile
        end_x, end_y = end_tile

        if horizontal_first:
            tiles = [
                (tile_x, start_y)
                for tile_x in self.range_inclusive(start_x, end_x)
            ]
            tiles.extend(
                (end_x, tile_y)
                for tile_y in self.range_inclusive(start_y, end_y)
            )
        else:
            tiles = [
                (start_x, tile_y)
                for tile_y in self.range_inclusive(start_y, end_y)
            ]
            tiles.extend(
                (tile_x, end_y)
                for tile_x in self.range_inclusive(start_x, end_x)
            )

        return self.unique_tiles(tiles)

    def range_inclusive(self, start, end):
        step = 1 if end >= start else -1
        return range(start, end + step, step)

    def choose_entrance_tile(self, rooms):
        room = min(
            rooms,
            key=lambda room: (
                room.center[0] + room.center[1],
                room.center[1],
                room.center[0],
            ),
        )
        return room.center

    def choose_final_room_tile(self, rooms, matrix, entrance_tile):
        candidate_tiles = [
            room.center
            for room in self.sort_rooms_by_distance(rooms, entrance_tile)
        ]
        candidate_tiles.extend(self.get_floor_tiles_by_distance(matrix, entrance_tile))
        return self.choose_distinct_tiles(candidate_tiles, {entrance_tile}, 1)[0]

    def choose_capture_point_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
    ):
        used_tiles = {entrance_tile, final_room_tile}
        candidate_tiles = [
            room.center
            for room in self.sort_rooms_by_distance(rooms, entrance_tile)
        ]
        candidate_tiles.extend(self.get_floor_tiles_by_distance(matrix, entrance_tile))
        return self.choose_distinct_tiles(candidate_tiles, used_tiles, 2)

    def choose_enemy_spawn_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
        capture_point_tiles,
    ):
        used_tiles = {
            entrance_tile,
            final_room_tile,
            *capture_point_tiles,
        }
        candidate_tiles = self.get_near_room_center_tiles(
            rooms,
            matrix,
            entrance_tile,
        )
        candidate_tiles.extend(self.get_floor_tiles_by_distance(matrix, entrance_tile))
        return self.choose_distinct_tiles(candidate_tiles, used_tiles, 3)

    def choose_wave_spawn_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
        capture_point_tiles,
        enemy_spawn_tiles,
    ):
        used_tiles = {
            entrance_tile,
            final_room_tile,
            *capture_point_tiles,
            *enemy_spawn_tiles,
        }
        candidate_tiles = self.get_floor_tiles_by_distance(matrix, entrance_tile)
        return self.choose_distinct_tiles(candidate_tiles, used_tiles, 2)

    def choose_distinct_tiles(self, candidate_tiles, used_tiles, count):
        used_tiles = set(used_tiles)
        chosen_tiles = []

        for tile in candidate_tiles:
            if tile in used_tiles:
                continue

            used_tiles.add(tile)
            chosen_tiles.append(tile)

            if len(chosen_tiles) == count:
                return chosen_tiles

        raise ValueError("Not enough distinct castle floor tiles")

    def get_near_room_center_tiles(self, rooms, matrix, entrance_tile):
        offsets = (
            (0, 0),
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
        )
        candidate_tiles = []

        for room in self.sort_rooms_by_distance(rooms, entrance_tile):
            center_x, center_y = room.center
            for offset_x, offset_y in offsets:
                tile = (center_x + offset_x, center_y + offset_y)
                if room.contains_tile(tile) and self.is_floor_tile(matrix, tile):
                    candidate_tiles.append(tile)

        return self.unique_tiles(candidate_tiles)

    def get_floor_tiles_by_distance(self, matrix, origin_tile):
        floor_tiles = []

        for tile_y, row in enumerate(matrix):
            for tile_x, tile in enumerate(row):
                if tile == FLOOR:
                    floor_tiles.append((tile_x, tile_y))

        return sorted(
            floor_tiles,
            key=lambda tile: (
                self.manhattan_distance(tile, origin_tile),
                tile[1],
                tile[0],
            ),
            reverse=True,
        )

    def is_layout_valid(self, layout):
        important_tiles = self.get_important_tiles(layout)

        if len(set(important_tiles)) != len(important_tiles):
            return False

        for tile in [layout.entrance_tile, *important_tiles]:
            if not self.is_floor_tile(layout.matrix, tile):
                return False

        tile_map = layout.to_tile_map()
        return are_tiles_reachable(
            tile_map,
            layout.entrance_tile,
            important_tiles,
        )

    def get_important_tiles(self, layout):
        return [
            layout.final_room_tile,
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

    def is_floor_tile(self, matrix, tile):
        tile_x, tile_y = tile
        return self.is_in_bounds(tile) and matrix[tile_y][tile_x] == FLOOR

    def is_in_bounds(self, tile):
        tile_x, tile_y = tile
        return 0 <= tile_x < self.width and 0 <= tile_y < self.height

    def sort_rooms(self, rooms):
        return sorted(
            rooms,
            key=lambda room: (
                room.center[0],
                room.center[1],
                room.x,
                room.y,
            ),
        )

    def sort_rooms_by_distance(self, rooms, origin_tile):
        return sorted(
            rooms,
            key=lambda room: (
                self.manhattan_distance(room.center, origin_tile),
                room.center[1],
                room.center[0],
            ),
            reverse=True,
        )

    def manhattan_distance(self, first_tile, second_tile):
        first_x, first_y = first_tile
        second_x, second_y = second_tile
        return abs(first_x - second_x) + abs(first_y - second_y)

    def unique_tiles(self, tiles):
        result = []
        seen_tiles = set()

        for tile in tiles:
            if tile in seen_tiles:
                continue

            seen_tiles.add(tile)
            result.append(tile)

        return result
