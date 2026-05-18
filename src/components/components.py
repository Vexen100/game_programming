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
