from dataclasses import dataclass


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Velocity:
    x: float = 0
    y: float = 0


@dataclass
class Collider:
    width: int
    height: int
    solid: bool = True


@dataclass
class Renderable:
    width: int
    height: int
    color: tuple[int, int, int]


@dataclass
class Health:
    current: int
    maximum: int


@dataclass
class PlayerControlled:
    pass


@dataclass
class Enemy:
    pass


@dataclass
class ChaseBehavior:
    speed: float
    detection_radius: float


@dataclass
class AttackIntent:
    requested: bool = False


@dataclass
class MeleeAttack:
    damage: int
    attack_range: float
    cooldown: float
    cooldown_timer: float = 0
