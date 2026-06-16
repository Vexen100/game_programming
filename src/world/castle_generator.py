import hashlib
import random
from dataclasses import dataclass

from src.algorithms.bsp import BSPGenerator, RectInt
from src.algorithms.flood_fill import are_tiles_reachable
from src.world.tile_types import (
    CASTLE_FLOOR,
    CASTLE_WALL,
    CRACKED_STONE_FLOOR,
    DARK_CORRIDOR_FLOOR,
    WALKABLE_TILES,
)


@dataclass
class CastleLayout:
    """Хранит результат генерации замка и ключевые точки gameplay.

    Attributes:
        matrix: Двумерная матрица тайлов карты.
        rooms: Список прямоугольных комнат BSP-генератора.
        corridors: Значение `corridors`, используемое в логике метода.
        entrance_tile: Координаты входа в замок.
        final_room_tile: Координаты центрального тайла финальной комнаты.
        capture_point_tiles: Список тайлов точек захвата.
        enemy_spawn_tiles: Список тайлов появления врагов.
        wave_spawn_tiles: Список тайлов появления волновых врагов.
        seed: Seed генерации для воспроизводимого результата.
    """
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
        """Создает TileMap из layout замка.

        Returns:
            Результат выполнения `to_tile_map`.
        """
        from src.world.tile_map import TileMap

        return TileMap([row[:] for row in self.matrix])

    def fingerprint(self) -> str:
        """Создает короткий fingerprint layout замка.

        Returns:
            Результат выполнения `fingerprint`.
        """
        digest = hashlib.sha1()

        for row in self.matrix:
            digest.update(",".join(str(tile) for tile in row).encode("ascii"))
            digest.update(b"\n")

        important_parts = [
            self.entrance_tile,
            self.final_room_tile,
            *self.capture_point_tiles,
            *self.enemy_spawn_tiles,
            *self.wave_spawn_tiles,
        ]

        for tile in important_parts:
            digest.update(f"{tile[0]}:{tile[1]}|".encode("ascii"))

        return digest.hexdigest()[:8]


class CastleGenerator:
    """Генерирует тайловый layout замка через BSP-комнаты и коридоры.

    Attributes:
        CAPTURE_POINT_COUNT: Значение `точка захвата точка count`, используемое в логике метода.
    """
    CAPTURE_POINT_COUNT = 3

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
        corridor_width=2,
    ):
        """Инициализирует `CastleGenerator` и сохраняет начальные зависимости.

        Args:
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.
            seed: Seed генерации для воспроизводимого результата.
            min_leaf_size: Минимальный размер листа BSP-разбиения.
            max_depth: Максимальная глубина BSP-разбиения.
            min_room_size: Минимальный размер комнаты.
            room_margin: Отступ комнаты от границ BSP-листа.
            max_attempts: Максимальное число попыток генерации layout.
            corridor_width: Ширина коридора в тайлах.

        Returns:
            None.
        """
        self.width = width
        self.height = height
        self.seed = seed
        self.min_leaf_size = min_leaf_size
        self.max_depth = max_depth
        self.min_room_size = min_room_size
        self.room_margin = room_margin
        self.max_attempts = max_attempts
        self.corridor_width = corridor_width

        self.validate_parameters()

    def validate_parameters(self):
        """Проверяет корректность параметров.

        Returns:
            None.
        """
        if self.max_attempts < 1:
            raise ValueError("CastleGenerator max_attempts must be at least 1")
        if self.corridor_width < 1:
            raise ValueError("CastleGenerator corridor_width must be at least 1")

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
        """Генерирует результат алгоритма.

        Returns:
            Результат выполнения `generate`.
        """
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
        """Выполняет одну попытку генерации layout.

        Args:
            attempt_seed: Seed конкретной попытки генерации.

        Returns:
            Созданный результат: attempt.
        """
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
        """Создает wall matrix.

        Returns:
            Созданный результат: wall matrix.
        """
        return [
            [CASTLE_WALL for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def carve_rooms(self, matrix, rooms):
        """Вырезает комнаты в матрице замка.

        Args:
            matrix: Двумерная матрица тайлов карты.
            rooms: Список прямоугольных комнат BSP-генератора.

        Returns:
            None.
        """
        for room in rooms:
            for tile_y in range(room.y, room.bottom):
                for tile_x in range(room.x, room.right):
                    matrix[tile_y][tile_x] = self.get_room_floor_tile(tile_x, tile_y)

    def get_room_floor_tile(self, tile_x, tile_y):
        """Возвращает комната пол тайл.

        Args:
            tile_x: Координата тайла по оси X.
            tile_y: Координата тайла по оси Y.

        Returns:
            Найденное или вычисленное значение: комната пол тайл.
        """
        seed_value = self.seed or 0
        if (tile_x * 7 + tile_y * 11 + seed_value) % 13 == 0:
            return CRACKED_STONE_FLOOR

        return CASTLE_FLOOR

    def carve_corridors(self, matrix, rooms, rng):
        """Вырезает коридоры между комнатами.

        Args:
            matrix: Двумерная матрица тайлов карты.
            rooms: Список прямоугольных комнат BSP-генератора.
            rng: Генератор случайных чисел для воспроизводимого выбора.

        Returns:
            Результат выполнения `carve_corridors`.
        """
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

            for tile in corridor:
                self.carve_corridor_tile(matrix, tile)

            corridors.append(corridor)

        return corridors

    def carve_corridor_tile(self, matrix, tile):
        """Вырезает один тайл коридора.

        Args:
            matrix: Двумерная матрица тайлов карты.
            tile: Координаты тайла в формате `(x, y)`.

        Returns:
            None.
        """
        for tile_x, tile_y in self.get_widened_corridor_tiles(tile):
            if self.is_in_bounds((tile_x, tile_y)):
                matrix[tile_y][tile_x] = DARK_CORRIDOR_FLOOR

    def get_widened_corridor_tiles(self, tile):
        """Возвращает widened коридор тайлы.

        Args:
            tile: Координаты тайла в формате `(x, y)`.

        Returns:
            Найденное или вычисленное значение: widened коридор тайлы.
        """
        tile_x, tile_y = tile
        tiles = []

        for offset_x in range(self.corridor_width):
            for offset_y in range(self.corridor_width):
                tiles.append((tile_x + offset_x, tile_y + offset_y))

        return tiles

    def create_l_corridor(self, start_tile, end_tile, horizontal_first):
        """Создает L-образный коридор между двумя тайлами.

        Args:
            start_tile: Координаты стартового тайла.
            end_tile: Координаты конечного тайла.
            horizontal_first: Флаг первого горизонтального сегмента L-образного коридора.

        Returns:
            Список тайлов L-образного коридора без дублей.
        """
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
        """Создает диапазон чисел, включающий обе границы.

        Args:
            start: Значение `start`, используемое в логике метода.
            end: Значение `end`, используемое в логике метода.

        Returns:
            Объект `range`, проходящий от `start` до `end` включительно.
        """
        step = 1 if end >= start else -1
        return range(start, end + step, step)

    def choose_entrance_tile(self, rooms):
        """Выбирает entrance тайл.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.

        Returns:
            Выбранное значение: entrance тайл.
        """
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
        """Выбирает финальный комната тайл.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            matrix: Двумерная матрица тайлов карты.
            entrance_tile: Координаты входа в замок.

        Returns:
            Выбранное значение: финальный комната тайл.
        """
        candidate_tiles = [
            room.center
            for room in self.sort_rooms_by_distance(rooms, entrance_tile)
        ]
        candidate_tiles.extend(self.get_walkable_tiles_by_distance(matrix, entrance_tile))
        return self.choose_distinct_tiles(candidate_tiles, {entrance_tile}, 1)[0]

    def choose_capture_point_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
    ):
        """Выбирает точка захвата точка тайлы.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            matrix: Двумерная матрица тайлов карты.
            entrance_tile: Координаты входа в замок.
            final_room_tile: Координаты центрального тайла финальной комнаты.

        Returns:
            Выбранное значение: точка захвата точка тайлы.
        """
        used_tiles = {entrance_tile, final_room_tile}
        intermediate_count = self.CAPTURE_POINT_COUNT - 1
        candidate_tiles = [
            room.center
            for room in self.sort_rooms_by_distance(rooms, entrance_tile)
            if room.center != final_room_tile
        ]
        candidate_tiles.extend(self.get_walkable_tiles_by_distance(matrix, entrance_tile))
        capture_point_tiles = self.choose_distinct_tiles(
            candidate_tiles,
            used_tiles,
            intermediate_count,
        )
        capture_point_tiles.append(final_room_tile)
        return capture_point_tiles

    def choose_enemy_spawn_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
        capture_point_tiles,
    ):
        """Выбирает враг появление тайлы.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            matrix: Двумерная матрица тайлов карты.
            entrance_tile: Координаты входа в замок.
            final_room_tile: Координаты центрального тайла финальной комнаты.
            capture_point_tiles: Список тайлов точек захвата.

        Returns:
            Выбранное значение: враг появление тайлы.
        """
        used_tiles = {
            entrance_tile,
            final_room_tile,
            *capture_point_tiles,
        }
        guard_tiles = self.choose_guard_tiles_near_capture_points(
            matrix,
            capture_point_tiles,
            used_tiles,
        )
        used_tiles.update(guard_tiles)
        candidate_tiles = self.get_near_room_center_tiles(
            rooms,
            matrix,
            entrance_tile,
        )
        candidate_tiles.extend(self.get_walkable_tiles_by_distance(matrix, entrance_tile))
        enemy_spawn_tiles = list(guard_tiles)
        enemy_spawn_tiles.extend(
            self.choose_distinct_tiles(
                candidate_tiles,
                used_tiles,
                max(0, len(capture_point_tiles) - len(enemy_spawn_tiles)),
            )
        )
        return enemy_spawn_tiles

    def choose_guard_tiles_near_capture_points(self, matrix, capture_point_tiles, used_tiles):
        """Выбирает стража тайлы near точка захвата точки.

        Args:
            matrix: Двумерная матрица тайлов карты.
            capture_point_tiles: Список тайлов точек захвата.
            used_tiles: Множество тайлов, уже занятых важными объектами.

        Returns:
            Выбранное значение: стража тайлы near точка захвата точки.
        """
        guard_tiles = []
        used_tiles = set(used_tiles)

        for capture_point_tile in capture_point_tiles:
            candidate_tiles = self.get_nearby_walkable_tiles(
                matrix,
                capture_point_tile,
                max_distance=2,
            )
            guard_tile = self.choose_distinct_tiles(candidate_tiles, used_tiles, 1)[0]
            used_tiles.add(guard_tile)
            guard_tiles.append(guard_tile)

        return guard_tiles

    def choose_wave_spawn_tiles(
        self,
        rooms,
        matrix,
        entrance_tile,
        final_room_tile,
        capture_point_tiles,
        enemy_spawn_tiles,
    ):
        """Выбирает волна появление тайлы.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            matrix: Двумерная матрица тайлов карты.
            entrance_tile: Координаты входа в замок.
            final_room_tile: Координаты центрального тайла финальной комнаты.
            capture_point_tiles: Список тайлов точек захвата.
            enemy_spawn_tiles: Список тайлов появления врагов.

        Returns:
            Выбранное значение: волна появление тайлы.
        """
        used_tiles = {
            entrance_tile,
            final_room_tile,
            *capture_point_tiles,
            *enemy_spawn_tiles,
        }
        candidate_tiles = []

        for capture_point_tile in capture_point_tiles[:-1]:
            candidate_tiles.extend(
                self.get_nearby_walkable_tiles(
                    matrix,
                    capture_point_tile,
                    max_distance=4,
                )
            )

        candidate_tiles.extend(self.get_walkable_tiles_by_distance(matrix, entrance_tile))
        return self.choose_distinct_tiles(candidate_tiles, used_tiles, 2)

    def choose_distinct_tiles(self, candidate_tiles, used_tiles, count):
        """Выбирает distinct тайлы.

        Args:
            candidate_tiles: Список тайлов-кандидатов для выбора.
            used_tiles: Множество тайлов, уже занятых важными объектами.
            count: Требуемое количество элементов.

        Returns:
            Выбранное значение: distinct тайлы.
        """
        if count <= 0:
            return []

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
        """Возвращает near комната центр тайлы.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            matrix: Двумерная матрица тайлов карты.
            entrance_tile: Координаты входа в замок.

        Returns:
            Найденное или вычисленное значение: near комната центр тайлы.
        """
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
                if room.contains_tile(tile) and self.is_walkable_tile(matrix, tile):
                    candidate_tiles.append(tile)

        return self.unique_tiles(candidate_tiles)

    def get_nearby_walkable_tiles(self, matrix, origin_tile, max_distance):
        """Возвращает nearby проходимые тайлы.

        Args:
            matrix: Двумерная матрица тайлов карты.
            origin_tile: Координаты исходного тайла для поиска рядом или расчета расстояния.
            max_distance: Максимальная дистанция поиска или проверки.

        Returns:
            Найденное или вычисленное значение: nearby проходимые тайлы.
        """
        candidate_tiles = []
        origin_x, origin_y = origin_tile

        for distance in range(1, max_distance + 1):
            for tile_y in range(origin_y - distance, origin_y + distance + 1):
                for tile_x in range(origin_x - distance, origin_x + distance + 1):
                    tile = (tile_x, tile_y)

                    if tile == origin_tile:
                        continue

                    if self.manhattan_distance(tile, origin_tile) > distance:
                        continue

                    if self.is_walkable_tile(matrix, tile):
                        candidate_tiles.append(tile)

        return self.unique_tiles(candidate_tiles)

    def get_walkable_tiles_by_distance(self, matrix, origin_tile):
        """Возвращает проходимые тайлы by дистанция.

        Args:
            matrix: Двумерная матрица тайлов карты.
            origin_tile: Координаты исходного тайла для поиска рядом или расчета расстояния.

        Returns:
            Найденное или вычисленное значение: проходимые тайлы by дистанция.
        """
        walkable_tiles = []

        for tile_y, row in enumerate(matrix):
            for tile_x, tile in enumerate(row):
                if tile in WALKABLE_TILES:
                    walkable_tiles.append((tile_x, tile_y))

        return sorted(
            walkable_tiles,
            key=lambda tile: (
                self.manhattan_distance(tile, origin_tile),
                tile[1],
                tile[0],
            ),
            reverse=True,
        )

    def is_layout_valid(self, layout):
        """Проверяет валидность layout.

        Args:
            layout: Сгенерированный layout карты или сцены.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        important_tiles = self.get_important_tiles(layout)

        if layout.capture_point_tiles[-1] != layout.final_room_tile:
            return False

        if len(set(important_tiles)) != len(important_tiles):
            return False

        for tile in [layout.entrance_tile, *important_tiles]:
            if not self.is_walkable_tile(layout.matrix, tile):
                return False

        tile_map = layout.to_tile_map()
        return are_tiles_reachable(
            tile_map,
            layout.entrance_tile,
            important_tiles,
        )

    def get_important_tiles(self, layout):
        """Возвращает важные тайлы.

        Args:
            layout: Сгенерированный layout карты или сцены.

        Returns:
            Найденное или вычисленное значение: важные тайлы.
        """
        return [
            *layout.capture_point_tiles,
            *layout.enemy_spawn_tiles,
            *layout.wave_spawn_tiles,
        ]

    def is_walkable_tile(self, matrix, tile):
        """Проверяет, является ли тайл проходимым.

        Args:
            matrix: Двумерная матрица тайлов карты.
            tile: Координаты тайла в формате `(x, y)`.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        tile_x, tile_y = tile
        return self.is_in_bounds(tile) and matrix[tile_y][tile_x] in WALKABLE_TILES

    def is_floor_tile(self, matrix, tile):
        """Проверяет, является ли тайл полом.

        Args:
            matrix: Двумерная матрица тайлов карты.
            tile: Координаты тайла в формате `(x, y)`.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.is_walkable_tile(matrix, tile)

    def is_in_bounds(self, tile):
        """Проверяет, находится ли тайл в границах карты.

        Args:
            tile: Координаты тайла в формате `(x, y)`.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        tile_x, tile_y = tile
        return 0 <= tile_x < self.width and 0 <= tile_y < self.height

    def sort_rooms(self, rooms):
        """Сортирует комнаты в стабильном порядке.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.

        Returns:
            Результат выполнения `sort_rooms`.
        """
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
        """Сортирует комнаты по расстоянию от тайла.

        Args:
            rooms: Список прямоугольных комнат BSP-генератора.
            origin_tile: Координаты исходного тайла для поиска рядом или расчета расстояния.

        Returns:
            Результат выполнения `sort_rooms_by_distance`.
        """
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
        """Вычисляет манхэттенское расстояние между тайлами.

        Args:
            first_tile: Координаты первого тайла.
            second_tile: Координаты второго тайла.

        Returns:
            Манхэттенское расстояние между двумя тайлами.
        """
        first_x, first_y = first_tile
        second_x, second_y = second_tile
        return abs(first_x - second_x) + abs(first_y - second_y)

    def unique_tiles(self, tiles):
        """Удаляет дубли из списка тайлов с сохранением порядка.

        Args:
            tiles: Список координат тайлов.

        Returns:
            Результат выполнения `unique_tiles`.
        """
        result = []
        seen_tiles = set()

        for tile in tiles:
            if tile in seen_tiles:
                continue

            seen_tiles.add(tile)
            result.append(tile)

        return result
