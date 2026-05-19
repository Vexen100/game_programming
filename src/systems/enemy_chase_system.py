import pygame

from src.components.components import (
    ChaseBehavior,
    Enemy,
    PlayerControlled,
    Position,
    Velocity,
)


class EnemyChaseSystem:
    """Записывает врагам скорость преследования игрока"""

    def update(self, ecm):
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

            direction = pygame.Vector2(
                player_position.x - enemy_position.x,
                player_position.y - enemy_position.y,
            )
            distance = direction.length()

            if distance == 0 or distance > chase.detection_radius:
                enemy_velocity.x = 0
                enemy_velocity.y = 0
                continue

            direction.normalize_ip()
            enemy_velocity.x = direction.x * chase.speed
            enemy_velocity.y = direction.y * chase.speed

    def stop_enemies(self, ecm):
        for enemy_id in ecm.get_entities_with(Enemy, Velocity):
            enemy_velocity = ecm.get_component(enemy_id, Velocity)
            enemy_velocity.x = 0
            enemy_velocity.y = 0
