import argparse
from pathlib import Path

from PIL import Image

try:
    from .grid_slicing import get_grid_boxes, parse_csv, remove_background
except ImportError:
    from grid_slicing import get_grid_boxes, parse_csv, remove_background


RESAMPLE_MODES = {
    "nearest": Image.Resampling.NEAREST,
    "box": Image.Resampling.BOX,
    "lanczos": Image.Resampling.LANCZOS,
}


def slice_tilesheet(
    input_path,
    output_root,
    cols,
    rows,
    names,
    folders=None,
    output_tile_size=32,
    margin_x=0,
    margin_y=0,
    gutter_x=0,
    gutter_y=0,
    grid_mode="exact",
    background_mode="none",
    background_color=None,
    tolerance=0,
    resample="box",
    validate_only=False,
):
    """Нарезает tilesheet на отдельные тайлы.

    Args:
        input_path: Значение `ввод путь`, используемое в логике метода.
        output_root: Каталог для обработанных ассетов.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        names: Имена кадров или тайлов, заданные пользователем.
        folders: Папки для раскладки нарезанных кадров или тайлов.
        output_tile_size: Размер итогового тайла после нарезки.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.
        grid_mode: Режим расчета сетки нарезки.
        background_mode: Значение `фон mode`, используемое в логике метода.
        background_color: Цвет `фон цвет` в формате PyGame.
        tolerance: Порог прозрачности или цвета при обработке изображения.
        resample: Алгоритм масштабирования изображения.
        validate_only: Флаг режима проверки без записи файлов.

    Returns:
        Список путей к созданным тайлам.
    """
    input_path = Path(input_path)
    output_root = Path(output_root)
    names = list(names)

    if folders is None:
        folders = ["tiles"] * len(names)
    else:
        folders = list(folders)

    expected_count = cols * rows
    if len(names) != expected_count:
        raise ValueError(
            f"Expected {expected_count} names for {cols}x{rows} grid, got {len(names)}"
        )

    if len(folders) != expected_count:
        raise ValueError(
            f"Expected {expected_count} folders for {cols}x{rows} grid, got {len(folders)}"
        )

    if resample not in RESAMPLE_MODES:
        raise ValueError(f"Unsupported resample mode: {resample}")

    with Image.open(input_path) as source_image:
        source_image = source_image.convert("RGBA")
        boxes = get_grid_boxes(
            source_image.size,
            cols,
            rows,
            margin_x=margin_x,
            margin_y=margin_y,
            gutter_x=gutter_x,
            gutter_y=gutter_y,
            grid_mode=grid_mode,
        )

        output_paths = []

        for box, name, folder in zip(boxes, names, folders):
            output_path = output_root / folder / f"{name}.png"
            output_paths.append(output_path)

            if validate_only:
                continue

            tile_image = source_image.crop(box)
            tile_image = remove_background(
                tile_image,
                mode=background_mode,
                background_color=background_color,
                tolerance=tolerance,
            )
            tile_image = tile_image.resize(
                (output_tile_size, output_tile_size),
                RESAMPLE_MODES[resample],
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tile_image.save(output_path)
            print(output_path)

    return output_paths


def build_parser():
    """Собирает parser.

    Returns:
        Созданный результат: parser.
    """
    parser = argparse.ArgumentParser(description="Slice a full-cell tile sheet.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--names", required=True)
    parser.add_argument("--folders")
    parser.add_argument("--output-tile-size", type=int, default=32)
    parser.add_argument("--margin-x", type=int, default=0)
    parser.add_argument("--margin-y", type=int, default=0)
    parser.add_argument("--gutter-x", type=int, default=0)
    parser.add_argument("--gutter-y", type=int, default=0)
    parser.add_argument(
        "--grid-mode",
        choices=("exact", "proportional"),
        default="exact",
    )
    parser.add_argument(
        "--background-mode",
        choices=("none", "top-left", "color"),
        default="none",
    )
    parser.add_argument("--background-color")
    parser.add_argument("--tolerance", type=int, default=0)
    parser.add_argument(
        "--resample",
        choices=tuple(RESAMPLE_MODES),
        default="box",
    )
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main(argv=None):
    """Запускает приложение Crown Reclaim из точки входа.

    Args:
        argv: Список аргументов командной строки; если `None`, берется `sys.argv`.

    Returns:
        Результат выполнения `main`.
    """
    args = build_parser().parse_args(argv)
    slice_tilesheet(
        input_path=args.input,
        output_root=args.output_root,
        cols=args.cols,
        rows=args.rows,
        names=parse_csv(args.names),
        folders=parse_csv(args.folders) if args.folders else None,
        output_tile_size=args.output_tile_size,
        margin_x=args.margin_x,
        margin_y=args.margin_y,
        gutter_x=args.gutter_x,
        gutter_y=args.gutter_y,
        grid_mode=args.grid_mode,
        background_mode=args.background_mode,
        background_color=args.background_color,
        tolerance=args.tolerance,
        resample=args.resample,
        validate_only=args.validate_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
