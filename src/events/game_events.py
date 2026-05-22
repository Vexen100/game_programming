from dataclasses import dataclass


@dataclass
class EnemyKilledEvent:
    enemy_id: int
    region_id: str
