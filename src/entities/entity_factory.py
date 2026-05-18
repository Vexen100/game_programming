from src.components.components import (
    ChaseBehavior,
    Collider,
    Enemy,
    Health,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.entities.entities_settings import EnemySettings, PlayerSettings


class EntityFactory:
    """Создаёт сущности с готовым набором компонентов"""

    def __init__(self, ecm) -> None:
        self.ecm = ecm

    def create_player(self, x, y):
        """Создаёт ECS-сущность игрока"""
        player = self.ecm.create_entity(tag="player")

        self.ecm.add_component(player, Position(x, y))
        self.ecm.add_component(player, Velocity())
        self.ecm.add_component(
            player,
            Collider(
                width=PlayerSettings.SIZE,
                height=PlayerSettings.SIZE,
                solid=True,
            ),
        )
        self.ecm.add_component(
            player,
            Renderable(
                width=PlayerSettings.SIZE,
                height=PlayerSettings.SIZE,
                color=PlayerSettings.COLOR,
            ),
        )
        self.ecm.add_component(
            player,
            Health(
                current=PlayerSettings.HEALTH,
                maximum=PlayerSettings.HEALTH,
            ),
        )
        self.ecm.add_component(player, PlayerControlled())

        return player

    def create_enemy(self, x, y):
        """Создаёт ECS-сущность врага"""
        enemy = self.ecm.create_entity(tag="enemy")

        self.ecm.add_component(enemy, Position(x, y))
        self.ecm.add_component(enemy, Velocity())
        self.ecm.add_component(
            enemy,
            Collider(
                width=EnemySettings.SIZE,
                height=EnemySettings.SIZE,
                solid=True,
            ),
        )
        self.ecm.add_component(
            enemy,
            Renderable(
                width=EnemySettings.SIZE,
                height=EnemySettings.SIZE,
                color=EnemySettings.COLOR,
            ),
        )
        self.ecm.add_component(
            enemy,
            Health(
                current=EnemySettings.HEALTH,
                maximum=EnemySettings.HEALTH,
            ),
        )
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(
            enemy,
            ChaseBehavior(
                speed=EnemySettings.SPEED,
                detection_radius=EnemySettings.DETECTION_RADIUS,
            ),
        )

        return enemy
