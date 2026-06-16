from collections import deque


DIRECTIONS_4 = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


def is_blocked(tile_map, tile):
    """Проверяет, заблокирована ли точка на карте.

    Args:
        tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
        tile: Координаты тайла в формате `(x, y)`.

    Returns:
        `True`, если условие выполнено, иначе `False`.
    """
    tile_x, tile_y = tile
    return tile_map.is_tile_blocked(tile_x, tile_y)


def get_reachable_tiles(tile_map, start_tile):
    """Находит все достижимые тайлы через flood fill.

    Args:
        tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
        start_tile: Координаты стартового тайла.

    Returns:
        Множество координат достижимых тайлов.
    """
    if is_blocked(tile_map, start_tile):
        return set()

    visited = {start_tile}
    queue = deque([start_tile])

    while queue:
        tile_x, tile_y = queue.popleft()

        for dx, dy in DIRECTIONS_4:
            next_tile = (tile_x + dx, tile_y + dy)

            if next_tile in visited:
                continue

            if is_blocked(tile_map, next_tile):
                continue

            visited.add(next_tile)
            queue.append(next_tile)

    return visited


def is_tile_reachable(tile_map, start_tile, target_tile):
    """Проверяет, достижим ли целевой тайл.

    Args:
        tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
        start_tile: Координаты стартового тайла.
        target_tile: Координаты тайла, к которому нужно двигаться.

    Returns:
        `True`, если условие выполнено, иначе `False`.
    """
    if is_blocked(tile_map, target_tile):
        return False

    return target_tile in get_reachable_tiles(tile_map, start_tile)


def are_tiles_reachable(tile_map, start_tile, target_tiles):
    """Проверяет, достижимы ли все целевые тайлы.

    Args:
        tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
        start_tile: Координаты стартового тайла.
        target_tiles: Список целевых тайлов для проверки достижимости.

    Returns:
        `True`, если условие выполнено, иначе `False`.
    """
    reachable_tiles = get_reachable_tiles(tile_map, start_tile)

    for target_tile in target_tiles:
        if target_tile not in reachable_tiles:
            return False

    return True
