from src.components.components import (
    AttackIntent,
    AttackHitbox,
    CapturePoint,
    ChaseBehavior,
    Collider,
    Enemy,
    FacingDirection,
    Health,
    MeleeAttack,
    NPC,
    Outpost,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.entities.entities_settings import (
    CapturePointSettings,
    EnemySettings,
    NPCSettings,
    OutpostSettings,
    PlayerSettings,
)


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
        self.ecm.add_component(player, AttackIntent())
        self.ecm.add_component(player, FacingDirection())
        self.ecm.add_component(
            player,
            AttackHitbox(
                duration=PlayerSettings.ATTACK_HITBOX_DURATION,
            ),
        )
        self.ecm.add_component(
            player,
            MeleeAttack(
                damage=PlayerSettings.DAMAGE,
                attack_range=PlayerSettings.ATTACK_RANGE,
                cooldown=PlayerSettings.ATTACK_COOLDOWN,
                knockback_distance=PlayerSettings.KNOCKBACK_DISTANCE,
            ),
        )

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
        self.ecm.add_component(
            enemy,
            MeleeAttack(
                damage=EnemySettings.DAMAGE,
                attack_range=EnemySettings.ATTACK_RANGE,
                cooldown=EnemySettings.ATTACK_COOLDOWN,
            ),
        )

        return enemy

    def create_outpost(self, x, y):
        """Создаёт ECS-сущность аванпоста"""
        outpost = self.ecm.create_entity(tag="outpost")

        self.ecm.add_component(outpost, Position(x, y))
        self.ecm.add_component(
            outpost,
            Renderable(
                width=OutpostSettings.SIZE,
                height=OutpostSettings.SIZE,
                color=OutpostSettings.ENEMY_COLOR,
            ),
        )
        self.ecm.add_component(
            outpost,
            Outpost(
                radius=OutpostSettings.RADIUS,
                cleared=False,
            ),
        )

        return outpost

    def create_npc(self, x, y, quest_id, required_outpost_id=None):
        """Создаёт ECS-сущность NPC с простым заданием"""
        npc = self.ecm.create_entity(tag="npc")

        self.ecm.add_component(npc, Position(x, y))
        self.ecm.add_component(
            npc,
            Renderable(
                width=NPCSettings.SIZE,
                height=NPCSettings.SIZE,
                color=NPCSettings.ACTIVE_COLOR,
            ),
        )
        self.ecm.add_component(
            npc,
            NPC(
                interaction_radius=NPCSettings.INTERACTION_RADIUS,
                quest_id=quest_id,
                required_outpost_id=required_outpost_id,
                quest_completed=False,
            ),
        )

        return npc

    def create_capture_point(self, x, y):
        """Создаёт ECS-сущность точки захвата"""
        capture_point = self.ecm.create_entity(tag="capture_point")

        self.ecm.add_component(capture_point, Position(x, y))
        self.ecm.add_component(
            capture_point,
            Renderable(
                width=CapturePointSettings.SIZE,
                height=CapturePointSettings.SIZE,
                color=CapturePointSettings.ENEMY_COLOR,
            ),
        )
        self.ecm.add_component(
            capture_point,
            CapturePoint(
                radius=CapturePointSettings.RADIUS,
                progress=0,
                owner="enemy",
                captured=False,
            ),
        )

        return capture_point
