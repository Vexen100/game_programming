from dataclasses import dataclass

from src.world.tile_types import BRIDGE, DIRT, FOREST, GRASS, ROAD, RUINS_FLOOR, WATER


@dataclass(frozen=True)
class EnemySpawn:
    """Описывает объект проекта: враг появление.

    Attributes:
        key: Ключ словаря, ресурса или игровой сущности.
        tile: Координаты тайла в формате `(x, y)`.
        patrol_tiles: Маршрут патруля как список тайлов.
    """
    key: str
    tile: tuple[int, int]
    patrol_tiles: list[tuple[int, int]]


@dataclass(frozen=True)
class OutpostSpawn:
    """Описывает объект проекта: аванпост появление.

    Attributes:
        key: Ключ словаря, ресурса или игровой сущности.
        tile: Координаты тайла в формате `(x, y)`.
    """
    key: str
    tile: tuple[int, int]


@dataclass(frozen=True)
class NPCSpawn:
    """Описывает объект проекта: NPC появление.

    Attributes:
        key: Ключ словаря, ресурса или игровой сущности.
        tile: Координаты тайла в формате `(x, y)`.
        quest_id: Идентификатор задания NPC.
        required_outpost_key: Ключ аванпоста, необходимого для задания NPC.
    """
    key: str
    tile: tuple[int, int]
    quest_id: str
    required_outpost_key: str | None = None


@dataclass
class RegionLayout:
    """Описывает объект проекта: регион layout.

    Attributes:
        matrix: Двумерная матрица тайлов карты.
        player_spawn_tile: Координаты тайла `игрок появление тайл` в формате `(x, y)`.
        enemy_spawns: Значение `враг spawns`, используемое в логике метода.
        outposts: Значение `outposts`, используемое в логике метода.
        npcs: Значение `npcs`, используемое в логике метода.
    """
    matrix: list[list[int]]
    player_spawn_tile: tuple[int, int]
    enemy_spawns: list[EnemySpawn]
    outposts: list[OutpostSpawn]
    npcs: list[NPCSpawn]


def create_old_ruins_region_layout():
    """Создает layout региона старых руин.

    Returns:
        Готовый layout региона старых руин.
    """
    width = 96
    height = 56
    matrix = [
        [GRASS for _ in range(width)]
        for _ in range(height)
    ]

    fill_rect(matrix, 0, 0, width, 1, FOREST)
    fill_rect(matrix, 0, height - 1, width, 1, FOREST)
    fill_rect(matrix, 0, 0, 1, height, FOREST)
    fill_rect(matrix, width - 1, 0, 1, height, FOREST)

    fill_rect(matrix, 44, 1, 3, height - 2, WATER)
    fill_rect(matrix, 44, 19, 3, 3, BRIDGE)
    fill_rect(matrix, 44, 42, 3, 3, BRIDGE)

    fill_rect(matrix, 8, 22, 14, 9, FOREST)
    fill_rect(matrix, 52, 8, 16, 10, FOREST)
    fill_rect(matrix, 80, 20, 10, 16, FOREST)
    fill_rect(matrix, 28, 38, 12, 10, FOREST)

    fill_rect(matrix, 12, 6, 20, 11, DIRT)
    fill_rect(matrix, 26, 12, 15, 12, RUINS_FLOOR)
    fill_rect(matrix, 66, 34, 17, 13, DIRT)
    fill_rect(matrix, 50, 40, 17, 10, DIRT)

    fill_rect(matrix, 4, 4, 28, 3, ROAD)
    fill_rect(matrix, 17, 5, 3, 10, ROAD)
    fill_rect(matrix, 22, 10, 9, 5, ROAD)
    fill_rect(matrix, 24, 15, 18, 5, ROAD)
    fill_rect(matrix, 32, 19, 49, 3, ROAD)
    fill_rect(matrix, 44, 19, 3, 3, BRIDGE)
    fill_rect(matrix, 71, 20, 3, 24, ROAD)
    fill_rect(matrix, 56, 42, 19, 3, ROAD)
    fill_rect(matrix, 56, 44, 5, 4, ROAD)
    fill_rect(matrix, 44, 42, 15, 3, ROAD)
    fill_rect(matrix, 44, 42, 3, 3, BRIDGE)

    return RegionLayout(
        matrix=matrix,
        player_spawn_tile=(5, 5),
        enemy_spawns=[
            EnemySpawn(
                key="road_patrol_west",
                tile=(14, 7),
                patrol_tiles=[(10, 5), (18, 5), (18, 8), (10, 8)],
            ),
            EnemySpawn(
                key="road_patrol_ruins",
                tile=(24, 12),
                patrol_tiles=[(22, 10), (28, 10), (28, 14), (22, 14)],
            ),
            EnemySpawn(
                key="north_ruins_guard_a",
                tile=(30, 15),
                patrol_tiles=[(30, 15), (34, 15), (34, 18), (30, 18)],
            ),
            EnemySpawn(
                key="north_ruins_guard_b",
                tile=(34, 17),
                patrol_tiles=[(31, 16), (36, 16), (36, 20), (31, 20)],
            ),
            EnemySpawn(
                key="north_ruins_guard_c",
                tile=(32, 19),
                patrol_tiles=[(29, 18), (35, 18), (35, 21), (29, 21)],
            ),
            EnemySpawn(
                key="east_supply_guard_a",
                tile=(70, 37),
                patrol_tiles=[(68, 36), (74, 36), (74, 40), (68, 40)],
            ),
            EnemySpawn(
                key="east_supply_guard_b",
                tile=(74, 39),
                patrol_tiles=[(70, 38), (78, 38), (78, 42), (70, 42)],
            ),
            EnemySpawn(
                key="east_supply_guard_c",
                tile=(72, 41),
                patrol_tiles=[(69, 40), (76, 40), (76, 44), (69, 44)],
            ),
            EnemySpawn(
                key="roaming_bridge_patrol",
                tile=(52, 42),
                patrol_tiles=[(48, 42), (58, 42), (58, 46), (48, 46)],
            ),
        ],
        outposts=[
            OutpostSpawn(key="north_ruins_outpost", tile=(32, 16)),
            OutpostSpawn(key="east_supply_outpost", tile=(72, 38)),
        ],
        npcs=[
            NPCSpawn(
                key="scout_npc",
                tile=(18, 12),
                quest_id="clear_north_ruins_outpost",
                required_outpost_key="north_ruins_outpost",
            ),
            NPCSpawn(
                key="villager_npc",
                tile=(58, 46),
                quest_id="clear_east_supply_outpost",
                required_outpost_key="east_supply_outpost",
            ),
        ],
    )


def fill_rect(matrix, x, y, width, height, tile_type):
    """Заполняет прямоугольную область выбранным цветом или тайлом.

    Args:
        matrix: Двумерная матрица тайлов карты.
        x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
        y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
        width: Ширина области, карты или изображения.
        height: Высота области, карты или изображения.
        tile_type: Тип тайла, который нужно разместить или проверить.

    Returns:
        None.
    """
    for tile_y in range(y, y + height):
        for tile_x in range(x, x + width):
            matrix[tile_y][tile_x] = tile_type
