from dataclasses import dataclass


@dataclass
class EnemyKilledEvent:
    """Описывает объект проекта: враг killed событие.

    Attributes:
        enemy_id: Идентификатор сущности врага.
        region_id: Идентификатор региона на карте мира.
    """
    enemy_id: int
    region_id: str


@dataclass
class OutpostClearedEvent:
    """Описывает объект проекта: аванпост cleared событие.

    Attributes:
        outpost_id: Идентификатор сущности аванпоста.
        region_id: Идентификатор региона на карте мира.
    """
    outpost_id: int
    region_id: str


@dataclass
class QuestCompletedEvent:
    """Описывает объект проекта: задание completed событие.

    Attributes:
        quest_id: Идентификатор задания NPC.
        npc_id: Идентификатор сущности NPC.
        region_id: Идентификатор региона на карте мира.
    """
    quest_id: str
    npc_id: int
    region_id: str


@dataclass(frozen=True)
class SupplyCacheDestroyedEvent:
    """Сообщает, что в регионе уничтожен склад снабжения.

    Attributes:
        region_id: Идентификатор региона на карте мира.
        supply_cache_key: Стабильный ключ склада из `RegionLayout`.
    """
    region_id: str
    supply_cache_key: str


@dataclass
class CapturePointTakenEvent:
    """Описывает объект проекта: точка захвата точка taken событие.

    Attributes:
        capture_point_id: Идентификатор сущности точки захвата.
        region_id: Идентификатор региона на карте мира.
    """
    capture_point_id: int
    region_id: str


@dataclass
class RegionLiberatedEvent:
    """Описывает объект проекта: регион liberated событие.

    Attributes:
        region_id: Идентификатор региона на карте мира.
    """
    region_id: str
