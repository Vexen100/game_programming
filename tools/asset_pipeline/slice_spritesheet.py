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


def slice_spritesheet(
    input_path,
    output_root,
    cols,
    rows,
    names,
    folders=None,
    output_frame_size=32,
    margin_x=0,
    margin_y=0,
    gutter_x=0,
    gutter_y=0,
    grid_mode="exact",
    background_mode="top-left",
    background_color=None,
    tolerance=30,
    trim_mode="shared",
    padding=2,
    anchor="center-bottom",
    resample="box",
    validate_only=False,
):
    """Нарезает spritesheet на отдельные кадры.

    Args:
        input_path: Значение `ввод путь`, используемое в логике метода.
        output_root: Каталог для обработанных ассетов.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        names: Имена кадров или тайлов, заданные пользователем.
        folders: Папки для раскладки нарезанных кадров или тайлов.
        output_frame_size: Размер итогового кадра спрайта.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.
        grid_mode: Режим расчета сетки нарезки.
        background_mode: Значение `фон mode`, используемое в логике метода.
        background_color: Цвет `фон цвет` в формате PyGame.
        tolerance: Порог прозрачности или цвета при обработке изображения.
        trim_mode: Режим обрезки прозрачных краев кадра.
        padding: Дополнительный отступ вокруг видимого содержимого.
        anchor: Точка выравнивания содержимого внутри итогового кадра.
        resample: Алгоритм масштабирования изображения.
        validate_only: Флаг режима проверки без записи файлов.

    Returns:
        Список путей к созданным кадрам.
    """
    input_path = Path(input_path)
    output_root = Path(output_root)
    names = list(names)

    if folders is None:
        folders = ["entities"] * len(names)
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

    if trim_mode not in ("none", "per-frame", "shared"):
        raise ValueError(f"Unsupported trim mode: {trim_mode}")

    if anchor not in ("center", "center-bottom"):
        raise ValueError(f"Unsupported anchor: {anchor}")

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
        frames = [
            remove_background(
                source_image.crop(box),
                mode=background_mode,
                background_color=background_color,
                tolerance=tolerance,
            )
            for box in boxes
        ]

    shared_bbox = None
    if trim_mode == "shared":
        shared_bbox = get_union_bbox(frames)

    output_paths = []

    for frame, name, folder in zip(frames, names, folders):
        output_path = output_root / folder / f"{name}.png"
        output_paths.append(output_path)

        if validate_only:
            continue

        output_frame = prepare_output_frame(
            frame,
            output_frame_size=output_frame_size,
            trim_mode=trim_mode,
            shared_bbox=shared_bbox,
            padding=padding,
            anchor=anchor,
            resample=resample,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_frame.save(output_path)
        print(output_path)

    return output_paths


def prepare_output_frame(
    frame,
    output_frame_size,
    trim_mode,
    shared_bbox,
    padding,
    anchor,
    resample,
):
    """Готовит кадр спрайта к записи в итоговый файл.

    Args:
        frame: Кадр спрайта, который нужно обработать.
        output_frame_size: Размер итогового кадра спрайта.
        trim_mode: Режим обрезки прозрачных краев кадра.
        shared_bbox: Общая граница, применяемая к нескольким кадрам.
        padding: Дополнительный отступ вокруг видимого содержимого.
        anchor: Точка выравнивания содержимого внутри итогового кадра.
        resample: Алгоритм масштабирования изображения.

    Returns:
        Результат выполнения `prepare_output_frame`.
    """
    if trim_mode == "none":
        return frame.resize(
            (output_frame_size, output_frame_size),
            RESAMPLE_MODES[resample],
        )

    if trim_mode == "shared":
        bbox = shared_bbox
    else:
        bbox = get_visible_bbox(frame)

    if bbox is None:
        return Image.new("RGBA", (output_frame_size, output_frame_size), (0, 0, 0, 0))

    cropped = frame.crop(bbox)
    return fit_into_canvas(
        cropped,
        output_frame_size=output_frame_size,
        padding=padding,
        anchor=anchor,
        resample=resample,
    )


def get_visible_bbox(image):
    """Возвращает видимые границы.

    Args:
        image: Изображение PIL или поверхность, которую нужно обработать.

    Returns:
        Найденное или вычисленное значение: видимые границы.
    """
    return image.getchannel("A").getbbox()


def get_union_bbox(frames):
    """Возвращает объединенные границы.

    Args:
        frames: Список кадров спрайта.

    Returns:
        Найденное или вычисленное значение: объединенные границы.
    """
    union_bbox = None

    for frame in frames:
        bbox = get_visible_bbox(frame)

        if bbox is None:
            continue

        if union_bbox is None:
            union_bbox = bbox
            continue

        left, top, right, bottom = union_bbox
        frame_left, frame_top, frame_right, frame_bottom = bbox
        union_bbox = (
            min(left, frame_left),
            min(top, frame_top),
            max(right, frame_right),
            max(bottom, frame_bottom),
        )

    return union_bbox


def fit_into_canvas(
    image,
    output_frame_size,
    padding,
    anchor,
    resample,
):
    """Размещает изображение внутри canvas нужного размера.

    Args:
        image: Изображение PIL или поверхность, которую нужно обработать.
        output_frame_size: Размер итогового кадра спрайта.
        padding: Дополнительный отступ вокруг видимого содержимого.
        anchor: Точка выравнивания содержимого внутри итогового кадра.
        resample: Алгоритм масштабирования изображения.

    Returns:
        Результат выполнения `fit_into_canvas`.
    """
    canvas = Image.new("RGBA", (output_frame_size, output_frame_size), (0, 0, 0, 0))
    max_size = max(1, output_frame_size - padding * 2)
    scale = min(max_size / image.width, max_size / image.height)
    resized_width = max(1, round(image.width * scale))
    resized_height = max(1, round(image.height * scale))
    resized = image.resize((resized_width, resized_height), RESAMPLE_MODES[resample])

    paste_x = (output_frame_size - resized_width) // 2
    if anchor == "center":
        paste_y = (output_frame_size - resized_height) // 2
    else:
        paste_y = output_frame_size - padding - resized_height

    canvas.alpha_composite(resized, (paste_x, paste_y))
    return canvas


def build_parser():
    """Собирает parser.

    Returns:
        Созданный результат: parser.
    """
    parser = argparse.ArgumentParser(description="Slice a chroma-key sprite sheet.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--names", required=True)
    parser.add_argument("--folders")
    parser.add_argument("--output-frame-size", type=int, default=32)
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
        default="top-left",
    )
    parser.add_argument("--background-color")
    parser.add_argument("--tolerance", type=int, default=30)
    parser.add_argument(
        "--trim-mode",
        choices=("none", "per-frame", "shared"),
        default="shared",
    )
    parser.add_argument("--padding", type=int, default=2)
    parser.add_argument(
        "--anchor",
        choices=("center", "center-bottom"),
        default="center-bottom",
    )
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
    slice_spritesheet(
        input_path=args.input,
        output_root=args.output_root,
        cols=args.cols,
        rows=args.rows,
        names=parse_csv(args.names),
        folders=parse_csv(args.folders) if args.folders else None,
        output_frame_size=args.output_frame_size,
        margin_x=args.margin_x,
        margin_y=args.margin_y,
        gutter_x=args.gutter_x,
        gutter_y=args.gutter_y,
        grid_mode=args.grid_mode,
        background_mode=args.background_mode,
        background_color=args.background_color,
        tolerance=args.tolerance,
        trim_mode=args.trim_mode,
        padding=args.padding,
        anchor=args.anchor,
        resample=args.resample,
        validate_only=args.validate_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
