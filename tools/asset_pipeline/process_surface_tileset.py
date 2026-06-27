from pathlib import Path

from PIL import Image

try:
    from .slice_tilesheet import slice_tilesheet
    from .validate_surface_tiles import (
        EXPECTED_SURFACE_TILE_PATHS,
        validate_surface_tiles,
    )
except ImportError:
    from slice_tilesheet import slice_tilesheet
    from validate_surface_tiles import (
        EXPECTED_SURFACE_TILE_PATHS,
        validate_surface_tiles,
    )


SOURCE_PATH = Path("assets/source/tilesets/crown_reclaim_surface_tileset_raw.png")
OUTPUT_ROOT = Path("assets/images")
PREVIEW_PATH = Path("assets/tmp/previews/surface_tiles_preview.png")

SURFACE_TILE_NAMES = (
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
)

SURFACE_TILE_FOLDERS = (
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
)

GRID_COLS = 4
GRID_ROWS = 4
MARGIN_X = 3
MARGIN_Y = 3
GUTTER_X = 5
GUTTER_Y = 5
OUTPUT_TILE_SIZE = 32


def ensure_directories():
    """Создает каталоги, нужные surface tileset pipeline.

    Returns:
        None.
    """
    SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "tiles").mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "castle").mkdir(parents=True, exist_ok=True)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)


def process_surface_tileset():
    """Нарезает текущий user-provided surface tileset и валидирует результат.

    Returns:
        Список путей к финальным tile PNG или пустой список, если source отсутствует.
    """
    ensure_directories()

    if not SOURCE_PATH.is_file():
        print(f"Surface tileset source is missing: {SOURCE_PATH}")
        print("Put the raw 4x4 tileset there and rerun this script.")
        return []

    output_paths = slice_tilesheet(
        input_path=SOURCE_PATH,
        output_root=OUTPUT_ROOT,
        cols=GRID_COLS,
        rows=GRID_ROWS,
        names=SURFACE_TILE_NAMES,
        folders=SURFACE_TILE_FOLDERS,
        output_tile_size=OUTPUT_TILE_SIZE,
        margin_x=MARGIN_X,
        margin_y=MARGIN_Y,
        gutter_x=GUTTER_X,
        gutter_y=GUTTER_Y,
        grid_mode="proportional",
        background_mode="none",
        resample="box",
    )

    create_preview(output_paths, PREVIEW_PATH)
    validated_paths = validate_surface_tiles(OUTPUT_ROOT, EXPECTED_SURFACE_TILE_PATHS)
    print(f"Preview saved: {PREVIEW_PATH}")
    print(f"Validated surface tiles: {len(validated_paths)}")
    print(
        "Grid values used: "
        f"margin_x={MARGIN_X}, margin_y={MARGIN_Y}, "
        f"gutter_x={GUTTER_X}, gutter_y={GUTTER_Y}"
    )
    return output_paths


def create_preview(tile_paths, preview_path):
    """Создает локальный preview из 16 финальных 32x32 tile PNG.

    Args:
        tile_paths: Пути к финальным tile PNG в порядке 4x4 сетки.
        preview_path: Путь, по которому нужно сохранить preview.

    Returns:
        Путь к созданному preview PNG.
    """
    preview_path = Path(preview_path)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview = Image.new(
        "RGBA",
        (GRID_COLS * OUTPUT_TILE_SIZE, GRID_ROWS * OUTPUT_TILE_SIZE),
        (0, 0, 0, 0),
    )

    for index, tile_path in enumerate(tile_paths):
        with Image.open(tile_path) as tile_image:
            tile_image = tile_image.convert("RGBA")
            tile_x = index % GRID_COLS
            tile_y = index // GRID_COLS
            preview.paste(
                tile_image,
                (tile_x * OUTPUT_TILE_SIZE, tile_y * OUTPUT_TILE_SIZE),
            )

    preview.save(preview_path)
    return preview_path


def main(argv=None):
    """Запускает surface tileset pipeline из командной строки.

    Args:
        argv: Список аргументов командной строки; сейчас не используется.

    Returns:
        Код завершения процесса.
    """
    process_surface_tileset()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
