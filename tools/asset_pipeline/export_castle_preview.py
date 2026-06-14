import argparse
from pathlib import Path

from PIL import Image

from src.world.castle_generator import CastleGenerator
from src.world.tile_types import (
    CASTLE_FLOOR,
    CASTLE_WALL,
    CRACKED_STONE_FLOOR,
    DARK_CORRIDOR_FLOOR,
)


TILE_COLORS = {
    CASTLE_WALL: (40, 40, 48),
    CASTLE_FLOOR: (105, 105, 112),
    CRACKED_STONE_FLOOR: (128, 124, 120),
    DARK_CORRIDOR_FLOOR: (64, 60, 72),
}


def export_castle_preview(
    seed,
    output,
    width=72,
    height=48,
    tile_size=8,
):
    """Экспортирует preview сгенерированного замка в изображение.

    Args:
        seed: Seed генерации для воспроизводимого результата.
        output: Путь к выходному файлу.
        width: Ширина области, карты или изображения.
        height: Высота области, карты или изображения.
        tile_size: Значение `тайл size`, используемое в логике метода.

    Returns:
        Путь к созданному preview-файлу.
    """
    layout = CastleGenerator(
        width,
        height,
        seed=seed,
        min_leaf_size=10,
        max_depth=5,
        min_room_size=5,
        corridor_width=2,
    ).generate()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new(
        "RGBA",
        (len(layout.matrix[0]) * tile_size, len(layout.matrix) * tile_size),
        (0, 0, 0, 255),
    )
    pixels = image.load()

    for tile_y, row in enumerate(layout.matrix):
        for tile_x, tile_id in enumerate(row):
            color = TILE_COLORS.get(tile_id, (255, 0, 255))
            fill_rect(pixels, tile_x, tile_y, tile_size, color)

    image.save(output)
    print(output)
    return output


def fill_rect(pixels, tile_x, tile_y, tile_size, color):
    """Заполняет прямоугольную область выбранным цветом или тайлом.

    Args:
        pixels: Пиксельные данные изображения.
        tile_x: Координата тайла по оси X.
        tile_y: Координата тайла по оси Y.
        tile_size: Значение `тайл size`, используемое в логике метода.
        color: Цвет `цвет` в формате PyGame.

    Returns:
        None.
    """
    start_x = tile_x * tile_size
    start_y = tile_y * tile_size

    for y in range(start_y, start_y + tile_size):
        for x in range(start_x, start_x + tile_size):
            pixels[x, y] = (*color, 255)


def build_parser():
    """Собирает parser.

    Returns:
        Созданный результат: parser.
    """
    parser = argparse.ArgumentParser(description="Export a diagnostic castle layout preview.")
    parser.add_argument("--seed", type=int, default=41042)
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=72)
    parser.add_argument("--height", type=int, default=48)
    parser.add_argument("--tile-size", type=int, default=8)
    return parser


def main(argv=None):
    """Запускает приложение Crown Reclaim из точки входа.

    Args:
        argv: Список аргументов командной строки; если `None`, берется `sys.argv`.

    Returns:
        Результат выполнения `main`.
    """
    args = build_parser().parse_args(argv)
    export_castle_preview(
        seed=args.seed,
        output=args.output,
        width=args.width,
        height=args.height,
        tile_size=args.tile_size,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
