from pathlib import Path

from PIL import Image


EXPECTED_SURFACE_TILE_PATHS = (
    "tiles/grass.png",
    "tiles/dirt.png",
    "tiles/road.png",
    "tiles/ruins_floor.png",
    "tiles/forest.png",
    "tiles/water.png",
    "tiles/bridge.png",
    "tiles/wall.png",
    "castle/castle_floor.png",
    "castle/castle_wall.png",
    "castle/cracked_stone_floor.png",
    "castle/dark_corridor_floor.png",
    "tiles/outpost_marker.png",
    "tiles/npc_camp_marker.png",
    "tiles/capture_point_marker.png",
    "tiles/missing_tile.png",
)


def validate_surface_tiles(image_root="assets/images", expected_paths=None):
    """Проверяет готовые surface tile PNG после нарезки.

    Args:
        image_root: Корневой каталог game-ready изображений.
        expected_paths: Относительные пути ожидаемых tile PNG.

    Returns:
        Список абсолютных путей к проверенным PNG.
    """
    image_root = Path(image_root)
    expected_paths = expected_paths or EXPECTED_SURFACE_TILE_PATHS
    validated_paths = []

    for relative_path in expected_paths:
        image_path = image_root / relative_path

        if not image_path.is_file():
            raise ValueError(f"Missing surface tile PNG: {image_path}")

        if image_path.suffix.lower() != ".png":
            raise ValueError(f"Surface tile must be a PNG file: {image_path}")

        with Image.open(image_path) as image:
            if image.mode != "RGBA":
                raise ValueError(
                    f"Surface tile must be RGBA: {image_path} mode={image.mode}"
                )

            if image.size != (32, 32):
                raise ValueError(
                    f"Surface tile must be 32x32: {image_path} size={image.size}"
                )

            alpha_channel = image.getchannel("A")
            if alpha_channel.getbbox() is None:
                raise ValueError(f"Surface tile is fully transparent: {image_path}")

            if image.getbbox() is None:
                raise ValueError(f"Surface tile is empty: {image_path}")

        validated_paths.append(image_path)

    return validated_paths


def main(argv=None):
    """Запускает validator surface tiles из командной строки.

    Args:
        argv: Список аргументов командной строки; сейчас не используется.

    Returns:
        Код завершения процесса.
    """
    validated_paths = validate_surface_tiles()

    for image_path in validated_paths:
        print(image_path)

    print(f"Validated surface tiles: {len(validated_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
