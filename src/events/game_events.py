from dataclasses import dataclass


@dataclass
class EnemyKilledEvent:
    enemy_id: int
    region_id: str


@dataclass
class OutpostClearedEvent:
    outpost_id: int
    region_id: str


@dataclass
class QuestCompletedEvent:
    quest_id: str
    npc_id: int
    region_id: str
