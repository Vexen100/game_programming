def get_line_tiles(start_tile, end_tile):
    """Возвращает тайлы линии между двумя точками.

    Args:
        start_tile: Координаты стартового тайла.
        end_tile: Координаты конечного тайла.

    Returns:
        Найденное или вычисленное значение: линия тайлы.
    """
    x0, y0 = start_tile
    x1, y1 = end_tile
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    error = dx - dy
    tiles = []

    while True:
        tiles.append((x0, y0))

        if x0 == x1 and y0 == y1:
            return tiles

        double_error = error * 2

        if double_error > -dy:
            error -= dy
            x0 += step_x

        if double_error < dx:
            error += dx
            y0 += step_y


def has_line_of_sight(tile_map, start_tile, end_tile):
    """Проверяет прямую видимость между двумя тайлами.

    Args:
        tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
        start_tile: Координаты стартового тайла.
        end_tile: Координаты конечного тайла.

    Returns:
        `True`, если между тайлами нет стены, иначе `False`.
    """
    for tile_x, tile_y in get_line_tiles(start_tile, end_tile):
        if tile_map.is_tile_blocked(tile_x, tile_y):
            return False

    return True
