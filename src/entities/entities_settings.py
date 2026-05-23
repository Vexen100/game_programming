class PlayerSettings:
    SPEED = 150
    HEALTH = 100
    SIZE = 32
    COLOR = (50, 120, 255)
    DAMAGE = 10
    ATTACK_RANGE = 48
    ATTACK_COOLDOWN = 0.4


class EnemySettings:
    HEALTH = 40
    SIZE = 32
    COLOR = (200, 50, 50)
    SPEED = 80
    DETECTION_RADIUS = 220
    DAMAGE = 8
    ATTACK_RANGE = 40
    ATTACK_COOLDOWN = 0.8


class OutpostSettings:
    RADIUS = 96
    SIZE = 28
    ENEMY_COLOR = (110, 70, 40)
    CLEARED_COLOR = (220, 190, 40)


class NPCSettings:
    INTERACTION_RADIUS = 48
    SIZE = 26
    ACTIVE_COLOR = (120, 120, 180)
    COMPLETED_COLOR = (220, 190, 40)


class CapturePointSettings:
    RADIUS = 72
    SIZE = 24
    CAPTURE_SPEED = 50
    ENEMY_COLOR = (120, 40, 40)
    PLAYER_COLOR = (220, 190, 40)
