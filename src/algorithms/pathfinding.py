import heapq


DIRECTIONS_4 = (
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
)


def manhattan_distance(start_tile, goal_tile):
    return abs(goal_tile[0] - start_tile[0]) + abs(goal_tile[1] - start_tile[1])


def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()
    return path


def find_path(tile_map, start_tile, goal_tile):
    if tile_map.is_tile_blocked(start_tile[0], start_tile[1]):
        return []

    if tile_map.is_tile_blocked(goal_tile[0], goal_tile[1]):
        return []

    if start_tile == goal_tile:
        return [start_tile]

    open_tiles = []
    heapq.heappush(open_tiles, (0, start_tile))
    came_from = {}
    cost_so_far = {start_tile: 0}

    while open_tiles:
        _, current_tile = heapq.heappop(open_tiles)

        if current_tile == goal_tile:
            return reconstruct_path(came_from, current_tile)

        current_cost = cost_so_far[current_tile]

        for dx, dy in DIRECTIONS_4:
            next_tile = (current_tile[0] + dx, current_tile[1] + dy)

            if tile_map.is_tile_blocked(next_tile[0], next_tile[1]):
                continue

            new_cost = current_cost + 1

            if next_tile in cost_so_far and new_cost >= cost_so_far[next_tile]:
                continue

            cost_so_far[next_tile] = new_cost
            priority = new_cost + manhattan_distance(next_tile, goal_tile)
            came_from[next_tile] = current_tile
            heapq.heappush(open_tiles, (priority, next_tile))

    return []
