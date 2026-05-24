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

    def update(self, ecm, tile_map=None):
        player_entities = ecm.get_entities_with(PlayerControlled, Position)

        if not player_entities:
            self.stop_enemies(ecm)
            return

        player_id = next(iter(player_entities))
        player_position = ecm.get_component(player_id, Position)

        for enemy_id in ecm.get_entities_with(Enemy, Position, Velocity, ChaseBehavior):
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
                enemy_velocity,
                enemy_position,
                player_position,
                chase.speed,
                tile_map,
            )

    def update_enemy_with_pathfinding(
        self,
        enemy_velocity,
        enemy_position,
        player_position,
        speed,
        tile_map,
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

        path = find_path(tile_map, enemy_tile, player_tile)

        if len(path) < 2:
            self.stop_enemy(enemy_velocity)
            return

        target_x, target_y = self.get_tile_target_position(tile_map, path[1])
        self.move_towards_position(
            enemy_velocity,
            enemy_position,
            target_x,
            target_y,
            speed,
        )

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
