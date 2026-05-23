from collections import deque


DIRECTIONS_4 = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


def is_blocked(tile_map, tile):
    tile_x, tile_y = tile
    x, y = tile_map.coord_tile_to_pixels(tile_x, tile_y)
    return tile_map.is_blocked(x, y)


def get_reachable_tiles(tile_map, start_tile):
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
    if is_blocked(tile_map, target_tile):
        return False

    return target_tile in get_reachable_tiles(tile_map, start_tile)


def are_tiles_reachable(tile_map, start_tile, target_tiles):
    reachable_tiles = get_reachable_tiles(tile_map, start_tile)

    for target_tile in target_tiles:
        if target_tile not in reachable_tiles:
            return False

    return True
