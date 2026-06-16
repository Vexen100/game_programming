from src.components.components import (
    AttackIntent,
    AttackHitbox,
    CapturePoint,
    ChaseBehavior,
    Collider,
    Enemy,
    EnemyAttackState,
    FacingDirection,
    Health,
    MeleeAttack,
    NPC,
    Outpost,
    PlayerControlled,
    Position,
    Renderable,
    Sprite,
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
    """Создает сущности игры из стандартных ECS-компонентов.

    """

    def __init__(self, ecm) -> None:
        """Инициализирует `EntityFactory` и сохраняет начальные зависимости.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            None.
        """
        self.ecm = ecm

    def create_player(self, x, y):
        """Создает игрок.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Созданный результат: игрок.
        """
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
        self.ecm.add_component(player, Sprite("player"))
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
        """Создает враг.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Созданный результат: враг.
        """
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
        self.ecm.add_component(enemy, Sprite("enemy"))
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
        self.ecm.add_component(
            enemy,
            AttackHitbox(
                duration=EnemySettings.ATTACK_HITBOX_DURATION,
            ),
        )
        self.ecm.add_component(
            enemy,
            EnemyAttackState(
                windup_duration=EnemySettings.ATTACK_WINDUP_DURATION,
            ),
        )

        return enemy

    def create_outpost(self, x, y):
        """Создает аванпост.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Созданный результат: аванпост.
        """
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
        self.ecm.add_component(outpost, Sprite("outpost_enemy"))
        self.ecm.add_component(
            outpost,
            Outpost(
                radius=OutpostSettings.RADIUS,
                cleared=False,
            ),
        )

        return outpost

    def create_npc(self, x, y, quest_id, required_outpost_id=None):
        """Создает NPC.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            quest_id: Идентификатор задания NPC.
            required_outpost_id: Идентификатор аванпоста, необходимого для задания NPC.

        Returns:
            Созданный результат: NPC.
        """
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
        self.ecm.add_component(npc, Sprite("npc_active"))
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
        """Создает точка захвата точка.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Созданный результат: точка захвата точка.
        """
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
        self.ecm.add_component(capture_point, Sprite("capture_point_enemy"))
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
