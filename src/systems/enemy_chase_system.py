import pygame

from src.algorithms.pathfinding import find_path
from src.components.components import (
    ChaseBehavior,
    Enemy,
    PlayerControlled,
    Position,
    Velocity,
)


class EnemyChaseSystem:
    """Записывает врагам скорость преследования игрока"""

    def __init__(self, path_rebuild_interval=0.25):
        self.path_rebuild_interval = path_rebuild_interval
        self.cached_paths = {}
        self.cached_goal_tiles = {}
        self.path_rebuild_timers = {}

    def update(self, ecm, tile_map=None, dt=0):
        player_entities = ecm.get_entities_with(PlayerControlled, Position)
        enemy_ids = ecm.get_entities_with(Enemy, Position, Velocity, ChaseBehavior)
        self.remove_stale_path_cache(enemy_ids)

        if not player_entities:
            self.clear_path_cache()
            self.stop_enemies(ecm)
            return

        player_id = next(iter(player_entities))
        player_position = ecm.get_component(player_id, Position)

        for enemy_id in enemy_ids:
            enemy_position = ecm.get_component(enemy_id, Position)
            enemy_velocity = ecm.get_component(enemy_id, Velocity)
            chase = ecm.get_component(enemy_id, ChaseBehavior)

            distance = self.get_distance(enemy_position, player_position)

            if distance == 0 or distance > chase.detection_radius:
                self.stop_enemy(enemy_velocity)
                continue

            if tile_map is None:
                self.move_towards_position(
                    enemy_velocity,
                    enemy_position,
                    player_position.x,
                    player_position.y,
                    chase.speed,
                )
                continue

            self.update_enemy_with_pathfinding(
                enemy_id,
                enemy_velocity,
                enemy_position,
                player_position,
                chase.speed,
                tile_map,
                dt,
            )

    def update_enemy_with_pathfinding(
        self,
        enemy_id,
        enemy_velocity,
        enemy_position,
        player_position,
        speed,
        tile_map,
        dt,
    ):
        enemy_tile = tile_map.coord_pixels_to_tile(enemy_position.x, enemy_position.y)
        player_tile = tile_map.coord_pixels_to_tile(player_position.x, player_position.y)

        if enemy_tile == player_tile:
            self.move_towards_position(
                enemy_velocity,
                enemy_position,
                player_position.x,
                player_position.y,
                speed,
            )
            return

        self.path_rebuild_timers[enemy_id] = self.path_rebuild_timers.get(enemy_id, 0) - dt
        path = self.get_cached_or_rebuilt_path(
            enemy_id,
            tile_map,
            enemy_tile,
            player_tile,
        )

        if len(path) < 2:
            self.stop_enemy(enemy_velocity)
            return

        next_tile = self.get_next_tile_from_path(path, enemy_tile)

        if next_tile is None:
            self.cached_paths.pop(enemy_id, None)
            self.cached_goal_tiles.pop(enemy_id, None)
            self.path_rebuild_timers[enemy_id] = 0
            path = self.get_cached_or_rebuilt_path(
                enemy_id,
                tile_map,
                enemy_tile,
                player_tile,
            )

            if len(path) < 2:
                self.stop_enemy(enemy_velocity)
                return

            next_tile = path[1]

        target_x, target_y = self.get_tile_target_position(tile_map, next_tile)
        self.move_towards_position(
            enemy_velocity,
            enemy_position,
            target_x,
            target_y,
            speed,
        )

    def clear_path_cache(self):
        self.cached_paths.clear()
        self.cached_goal_tiles.clear()
        self.path_rebuild_timers.clear()

    def remove_stale_path_cache(self, active_enemy_ids):
        active_enemy_ids = set(active_enemy_ids)

        for enemy_id in list(self.cached_paths.keys()):
            if enemy_id not in active_enemy_ids:
                self.cached_paths.pop(enemy_id, None)
                self.cached_goal_tiles.pop(enemy_id, None)
                self.path_rebuild_timers.pop(enemy_id, None)

    def should_rebuild_path(self, enemy_id, goal_tile):
        if enemy_id not in self.cached_paths:
            return True

        if self.cached_goal_tiles.get(enemy_id) != goal_tile:
            return True

        return self.path_rebuild_timers.get(enemy_id, 0) <= 0

    def rebuild_path(self, enemy_id, tile_map, enemy_tile, goal_tile):
        path = find_path(tile_map, enemy_tile, goal_tile)
        self.cached_paths[enemy_id] = path
        self.cached_goal_tiles[enemy_id] = goal_tile
        self.path_rebuild_timers[enemy_id] = self.path_rebuild_interval
        return path

    def get_cached_or_rebuilt_path(self, enemy_id, tile_map, enemy_tile, goal_tile):
        path = self.cached_paths.get(enemy_id)

        if self.should_rebuild_path(enemy_id, goal_tile):
            return self.rebuild_path(enemy_id, tile_map, enemy_tile, goal_tile)

        if path and enemy_tile not in path:
            return self.rebuild_path(enemy_id, tile_map, enemy_tile, goal_tile)

        return path

    def get_next_tile_from_path(self, path, enemy_tile):
        if enemy_tile not in path:
            return None

        current_index = path.index(enemy_tile)

        if current_index + 1 >= len(path):
            return path[-1]

        return path[current_index + 1]

    def get_tile_target_position(self, tile_map, tile):
        return tile_map.coord_tile_to_pixels(tile[0], tile[1])

    def move_towards_position(self, velocity, position, target_x, target_y, speed):
        direction = pygame.Vector2(
            target_x - position.x,
            target_y - position.y,
        )

        if direction.length() == 0:
            self.stop_enemy(velocity)
            return

        direction.normalize_ip()
        velocity.x = direction.x * speed
        velocity.y = direction.y * speed

    def get_distance(self, first_position, second_position):
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def stop_enemy(self, enemy_velocity):
        enemy_velocity.x = 0
        enemy_velocity.y = 0

    def stop_enemies(self, ecm):
        for enemy_id in ecm.get_entities_with(Enemy, Velocity):
            enemy_velocity = ecm.get_component(enemy_id, Velocity)
            self.stop_enemy(enemy_velocity)
