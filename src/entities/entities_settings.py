class PlayerSettings:
    """Хранит настройки и константы: игрок settings.

    Attributes:
        SPEED: Значение `speed`, используемое в логике метода.
        HEALTH: Значение `health`, используемое в логике метода.
        SIZE: Значение `size`, используемое в логике метода.
        COLOR: Цвет `цвет` в формате PyGame.
        DAMAGE: Значение `урон`, используемое в логике метода.
        ATTACK_RANGE: Значение `атака range`, используемое в логике метода.
        ATTACK_COOLDOWN: Значение `атака cooldown`, используемое в логике метода.
        ATTACK_HITBOX_WIDTH: Значение `атака hitbox width`, используемое в логике метода.
        ATTACK_HITBOX_LENGTH: Значение `атака hitbox length`, используемое в логике метода.
        ATTACK_HITBOX_DURATION: Значение `атака hitbox duration`, используемое в логике метода.
        KNOCKBACK_DISTANCE: Значение `отталкивание дистанция`, используемое в логике метода.
    """
    SPEED = 150
    HEALTH = 100
    SIZE = 28
    COLOR = (50, 120, 255)
    DAMAGE = 10
    ATTACK_RANGE = 48
    ATTACK_COOLDOWN = 0.4
    ATTACK_HITBOX_WIDTH = 36
    ATTACK_HITBOX_LENGTH = 48
    ATTACK_HITBOX_DURATION = 0.12
    KNOCKBACK_DISTANCE = 28


class EnemySettings:
    """Хранит настройки и константы: враг settings.

    Attributes:
        HEALTH: Значение `health`, используемое в логике метода.
        SIZE: Значение `size`, используемое в логике метода.
        COLOR: Цвет `цвет` в формате PyGame.
        SPEED: Значение `speed`, используемое в логике метода.
        DETECTION_RADIUS: Значение `detection радиус`, используемое в логике метода.
        DAMAGE: Значение `урон`, используемое в логике метода.
        ATTACK_RANGE: Значение `атака range`, используемое в логике метода.
        ATTACK_COOLDOWN: Значение `атака cooldown`, используемое в логике метода.
        ATTACK_WINDUP_DURATION: Значение `атака подготовка duration`, используемое в логике метода.
        ATTACK_HITBOX_WIDTH: Значение `атака hitbox width`, используемое в логике метода.
        ATTACK_HITBOX_LENGTH: Значение `атака hitbox length`, используемое в логике метода.
        ATTACK_HITBOX_DURATION: Значение `атака hitbox duration`, используемое в логике метода.
    """
    HEALTH = 40
    SIZE = 28
    COLOR = (200, 50, 50)
    SPEED = 80
    DETECTION_RADIUS = 220
    DAMAGE = 8
    ATTACK_RANGE = 40
    ATTACK_COOLDOWN = 0.8
    ATTACK_WINDUP_DURATION = 0.35
    ATTACK_HITBOX_WIDTH = 34
    ATTACK_HITBOX_LENGTH = 44
    ATTACK_HITBOX_DURATION = 0.12


class OutpostSettings:
    """Хранит настройки и константы: аванпост settings.

    Attributes:
        RADIUS: Значение `радиус`, используемое в логике метода.
        SIZE: Значение `size`, используемое в логике метода.
        ENEMY_COLOR: Цвет `враг цвет` в формате PyGame.
        CLEARED_COLOR: Цвет `cleared цвет` в формате PyGame.
    """
    RADIUS = 96
    SIZE = 28
    ENEMY_COLOR = (110, 70, 40)
    CLEARED_COLOR = (220, 190, 40)


class NPCSettings:
    """Хранит настройки и константы: NPC settings.

    Attributes:
        INTERACTION_RADIUS: Значение `interaction радиус`, используемое в логике метода.
        SIZE: Значение `size`, используемое в логике метода.
        ACTIVE_COLOR: Цвет `активное цвет` в формате PyGame.
        COMPLETED_COLOR: Цвет `completed цвет` в формате PyGame.
    """
    INTERACTION_RADIUS = 48
    SIZE = 26
    ACTIVE_COLOR = (120, 120, 180)
    COMPLETED_COLOR = (220, 190, 40)


class SupplyCacheSettings:
    """Хранит настройки и цвета склада снабжения.

    Attributes:
        SIZE: Размер ECS-сущности склада в пикселях.
        ENEMY_COLOR: Цвет активного вражеского склада.
        DESTROYED_COLOR: Цвет уничтоженного склада.
    """
    SIZE = 32
    ENEMY_COLOR = (165, 95, 35)
    DESTROYED_COLOR = (85, 70, 55)


class CapturePointSettings:
    """Хранит настройки и константы: точка захвата точка settings.

    Attributes:
        RADIUS: Значение `радиус`, используемое в логике метода.
        SIZE: Значение `size`, используемое в логике метода.
        CAPTURE_SPEED: Значение `точка захвата speed`, используемое в логике метода.
        ENEMY_COLOR: Цвет `враг цвет` в формате PyGame.
        PLAYER_COLOR: Цвет `игрок цвет` в формате PyGame.
    """
    RADIUS = 72
    SIZE = 24
    CAPTURE_SPEED = 50
    ENEMY_COLOR = (120, 40, 40)
    PLAYER_COLOR = (220, 190, 40)
