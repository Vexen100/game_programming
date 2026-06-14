import argparse
from pathlib import Path

try:
    from .slice_spritesheet import slice_spritesheet
    from .slice_tilesheet import slice_tilesheet
except ImportError:
    from slice_spritesheet import slice_spritesheet
    from slice_tilesheet import slice_tilesheet


TILE_NAMES = [
    "grass",
    "dirt",
    "road",
    "ruins_floor",
    "forest",
    "water",
    "bridge",
    "wall",
    "castle_floor",
    "castle_wall",
    "cracked_stone_floor",
    "dark_corridor_floor",
    "outpost_marker",
    "npc_camp_marker",
    "capture_point_marker",
    "missing_tile",
]

TILE_FOLDERS = [
    "tiles",
    "tiles",
    "tiles",
    "tiles",
    "tiles",
    "tiles",
    "tiles",
    "tiles",
    "castle",
    "castle",
    "castle",
    "castle",
    "tiles",
    "tiles",
    "tiles",
    "tiles",
]

ENTITY_ICON_NAMES = [
    "player",
    "enemy",
    "enemy_guard",
    "enemy_archer",
    "npc_active",
    "npc_villager",
    "outpost_enemy",
    "supply_cache",
    "capture_point_neutral",
    "capture_point_enemy",
    "capture_point_player",
    "wave_spawn",
    "attack_slash",
    "enemy_attack_warning",
    "health_pickup",
    "missing_entity",
]

PLAYER_WALK_NAMES = [
    "walk_down_0",
    "walk_down_1",
    "walk_down_2",
    "walk_down_3",
    "walk_right_0",
    "walk_right_1",
    "walk_right_2",
    "walk_right_3",
    "walk_up_0",
    "walk_up_1",
    "walk_up_2",
    "walk_up_3",
    "walk_left_0",
    "walk_left_1",
    "walk_left_2",
    "walk_left_3",
]

PLAYER_ATTACK_NAMES = [
    "attack_down_0",
    "attack_down_1",
    "attack_down_2",
    "attack_down_3",
    "attack_right_0",
    "attack_right_1",
    "attack_right_2",
    "attack_right_3",
    "attack_up_0",
    "attack_up_1",
    "attack_up_2",
    "attack_up_3",
    "attack_left_0",
    "attack_left_1",
    "attack_left_2",
    "attack_left_3",
]

ENEMY_WALK_NAMES = [
    "walk_down_0",
    "walk_down_1",
    "walk_down_2",
    "walk_down_3",
    "walk_right_0",
    "walk_right_1",
    "walk_right_2",
    "walk_right_3",
    "walk_up_0",
    "walk_up_1",
    "walk_up_2",
    "walk_up_3",
    "walk_left_0",
    "walk_left_1",
    "walk_left_2",
    "walk_left_3",
]


def process_current_assets(source_root="assets/source", output_root="assets/images"):
    """Обрабатывает текущие исходные ассеты проекта.

    Args:
        source_root: Каталог с исходными пользовательскими ассетами.
        output_root: Каталог для обработанных ассетов.

    Returns:
        Сводка обработки ассетов.
    """
    source_root = Path(source_root)
    output_root = Path(output_root)
    processed = []
    skipped = []
    output_paths = []

    tilesheet = source_root / "tilesets" / "crown_reclaim_tileset_raw.png"
    if tilesheet.is_file():
        output_paths.extend(
            slice_tilesheet(
                input_path=tilesheet,
                output_root=output_root,
                cols=4,
                rows=4,
                grid_mode="proportional",
                output_tile_size=32,
                background_mode="none",
                resample="box",
                names=TILE_NAMES,
                folders=TILE_FOLDERS,
            )
        )
        processed.append(tilesheet)
    else:
        skipped.append(tilesheet)

    entity_icons = source_root / "spritesheets" / "crown_reclaim_entity_icons_raw.png"
    if entity_icons.is_file():
        output_paths.extend(
            slice_spritesheet(
                input_path=entity_icons,
                output_root=output_root,
                cols=4,
                rows=4,
                grid_mode="proportional",
                output_frame_size=32,
                background_mode="top-left",
                tolerance=30,
                trim_mode="per-frame",
                anchor="center",
                resample="box",
                names=ENTITY_ICON_NAMES,
                folders=["entities"] * 16,
            )
        )
        processed.append(entity_icons)
    else:
        skipped.append(entity_icons)

    animation_jobs = [
        (
            source_root / "spritesheets" / "player_knight_walk_raw.png",
            PLAYER_WALK_NAMES,
            ["entities/player"] * 16,
        ),
        (
            source_root / "spritesheets" / "player_knight_attack_raw.png",
            PLAYER_ATTACK_NAMES,
            ["entities/player"] * 16,
        ),
        (
            source_root / "spritesheets" / "enemy_soldier_walk_raw.png",
            ENEMY_WALK_NAMES,
            ["entities/enemy"] * 16,
        ),
    ]

    for animation_source, names, folders in animation_jobs:
        if animation_source.is_file():
            output_paths.extend(
                slice_spritesheet(
                    input_path=animation_source,
                    output_root=output_root,
                    cols=4,
                    rows=4,
                    grid_mode="proportional",
                    output_frame_size=32,
                    background_mode="top-left",
                    tolerance=30,
                    trim_mode="shared",
                    anchor="center-bottom",
                    resample="box",
                    names=names,
                    folders=folders,
                )
            )
            processed.append(animation_source)
        else:
            skipped.append(animation_source)

    print_summary(processed, skipped, output_paths)

    return {
        "processed": processed,
        "skipped": skipped,
        "outputs": output_paths,
    }


def print_summary(processed, skipped, output_paths):
    """Печатает сводку обработки ассетов в терминал.

    Args:
        processed: Количество успешно обработанных файлов.
        skipped: Количество пропущенных файлов.
        output_paths: Список путей к файлам, созданным пайплайном ассетов.

    Returns:
        None.
    """
    print("Asset pipeline summary")
    print("Processed files:")
    for path in processed:
        print(f"- {path}")

    print("Skipped files:")
    for path in skipped:
        print(f"- {path}")

    print(f"Output count: {len(output_paths)}")


def build_parser():
    """Собирает parser.

    Returns:
        Созданный результат: parser.
    """
    parser = argparse.ArgumentParser(description="Process current Crown Reclaim assets.")
    parser.add_argument("--source-root", default="assets/source")
    parser.add_argument("--output-root", default="assets/images")
    return parser


def main(argv=None):
    """Запускает приложение Crown Reclaim из точки входа.

    Args:
        argv: Список аргументов командной строки; если `None`, берется `sys.argv`.

    Returns:
        Результат выполнения `main`.
    """
    args = build_parser().parse_args(argv)
    process_current_assets(
        source_root=args.source_root,
        output_root=args.output_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
