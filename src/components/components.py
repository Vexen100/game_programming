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
class PlayerDefeated:
    pass


@dataclass
class Enemy:
    pass


@dataclass
class Outpost:
    radius: float
    cleared: bool = False


@dataclass
class NPC:
    interaction_radius: float
    quest_id: str
    required_outpost_id: int | None = None
    quest_completed: bool = False


@dataclass
class CapturePoint:
    radius: float
    progress: float = 0
    owner: str = "enemy"
    captured: bool = False


@dataclass
class Dead:
    pass


@dataclass
class ChaseBehavior:
    speed: float
    detection_radius: float


@dataclass
class PatrolRoute:
    patrol_tiles: list[tuple[int, int]]
    current_index: int = 0
    wait_duration: float = 0
    wait_timer: float = 0


@dataclass
class AttackIntent:
    requested: bool = False


@dataclass
class FacingDirection:
    x: int = 1
    y: int = 0


@dataclass
class AttackHitbox:
    active: bool = False
    x: float = 0
    y: float = 0
    width: int = 0
    height: int = 0
    timer: float = 0
    duration: float = 0.12
    hit_landed: bool = False


@dataclass
class MeleeAttack:
    damage: int
    attack_range: float
    cooldown: float
    cooldown_timer: float = 0
    knockback_distance: float = 0
