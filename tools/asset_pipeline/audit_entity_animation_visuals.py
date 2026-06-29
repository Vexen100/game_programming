import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

try:
    from .sprite_normalization import (
        analyze_runtime_scaled_artifacts,
        analyze_sprite_artifacts,
        get_alpha_bbox,
        get_sprite_footprint,
        is_dark_tinted_pixel,
        is_weak_green_or_olive_artifact_pixel,
        is_yellow_beige_pixel,
    )
except ImportError:
    from sprite_normalization import (
        analyze_runtime_scaled_artifacts,
        analyze_sprite_artifacts,
        get_alpha_bbox,
        get_sprite_footprint,
        is_dark_tinted_pixel,
        is_weak_green_or_olive_artifact_pixel,
        is_yellow_beige_pixel,
    )


FRAME_PATTERNS = (
    "entities/player/walk_*_*.png",
    "entities/player/attack_*_*.png",
    "entities/enemy/walk_*_*.png",
)
PREVIEW_SEQUENCES = (
    "player/walk_down",
    "player/walk_right",
    "player/attack_right",
    "enemy/walk_down",
    "enemy/walk_right",
)


@dataclass(frozen=True)
class TemporalReport:
    """Хранит sequence-level diagnostics.

    Attributes:
        sequence_id: Человекочитаемый id sequence.
        frame_count: Количество кадров в sequence.
        union_palette_size: Размер объединённой visible palette.
        max_color_churn: Максимальный churn RGB palette между соседями.
        max_alpha_mask_churn: Максимальный churn alpha mask между соседями.
        max_single_frame_pixels: Максимум pixels, появившихся только в одном кадре.
        suspicious_color_churn: Максимальный churn suspicious category counts.
        runtime28_max_color_churn: Максимальный runtime28 palette churn.
        runtime28_weak_green_or_olive: Суммарные runtime28 weak remnants.
    """
    sequence_id: str
    frame_count: int
    union_palette_size: int
    max_color_churn: int
    max_alpha_mask_churn: int
    max_single_frame_pixels: int
    suspicious_color_churn: int
    runtime28_max_color_churn: int
    runtime28_weak_green_or_olive: int


def collect_frame_paths(image_root):
    """Собирает player/enemy animation frames для visual audit.

    Args:
        image_root: Корень final image assets.

    Returns:
        Отсортированный список путей кадров.
    """
    image_root = Path(image_root)
    frame_paths = []

    for pattern in FRAME_PATTERNS:
        frame_paths.extend(sorted(image_root.glob(pattern)))

    return sorted(frame_paths)


def get_sequence_id(frame_path):
    """Возвращает sequence id для animation frame.

    Args:
        frame_path: Путь PNG кадра.

    Returns:
        Id вида `player/walk_down`.
    """
    entity = frame_path.parent.name
    state_direction = frame_path.stem.rsplit("_", 1)[0]
    return f"{entity}/{state_direction}"


def get_visible_palette(image):
    """Возвращает set видимых RGB-цветов.

    Args:
        image: PIL-изображение.

    Returns:
        Set RGB tuples.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size
    palette = set()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 0:
                palette.add((red, green, blue))

    return palette


def get_alpha_mask(image):
    """Возвращает set координат видимых pixels.

    Args:
        image: PIL-изображение.

    Returns:
        Set `(x, y)` для pixels с `alpha > 0`.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size
    mask = set()

    for y in range(height):
        for x in range(width):
            if pixels[x, y][3] > 0:
                mask.add((x, y))

    return mask


def count_single_frame_pixels(masks):
    """Считает pixels, появляющиеся только в одном кадре sequence.

    Args:
        masks: Список alpha mask sets.

    Returns:
        Количество координат, видимых ровно в одном кадре.
    """
    counts = {}

    for mask in masks:
        for point in mask:
            counts[point] = counts.get(point, 0) + 1

    return sum(1 for count in counts.values() if count == 1)


def get_suspicious_counts(image):
    """Возвращает category counts для suspicious color diagnostics.

    Args:
        image: PIL-изображение.

    Returns:
        Tuple `(weak_green, dark_tinted, yellow_beige)`.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size
    weak_green = 0
    dark_tinted = 0
    yellow_beige = 0

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if is_weak_green_or_olive_artifact_pixel(red, green, blue, alpha):
                weak_green += 1
            if is_dark_tinted_pixel(red, green, blue, alpha):
                dark_tinted += 1
            if is_yellow_beige_pixel(red, green, blue, alpha):
                yellow_beige += 1

    return weak_green, dark_tinted, yellow_beige


def analyze_temporal_flicker(sequence_id, frame_paths):
    """Считает sequence-level flicker diagnostics.

    Args:
        sequence_id: Id sequence.
        frame_paths: Пути кадров sequence.

    Returns:
        `TemporalReport`.
    """
    images = []
    runtime_images = []
    for frame_path in frame_paths:
        with Image.open(frame_path) as image:
            rgba_image = image.convert("RGBA")
            images.append(rgba_image)
            runtime_images.append(
                rgba_image.resize((28, 28), Image.Resampling.NEAREST)
            )

    palettes = [get_visible_palette(image) for image in images]
    runtime_palettes = [get_visible_palette(image) for image in runtime_images]
    masks = [get_alpha_mask(image) for image in images]
    suspicious_counts = [get_suspicious_counts(image) for image in images]
    union_palette = set()
    for palette in palettes:
        union_palette.update(palette)

    max_color_churn = 0
    max_alpha_mask_churn = 0
    max_suspicious_churn = 0
    max_runtime_color_churn = 0

    for index in range(1, len(images)):
        max_color_churn = max(
            max_color_churn,
            len(palettes[index - 1] ^ palettes[index]),
        )
        max_alpha_mask_churn = max(
            max_alpha_mask_churn,
            len(masks[index - 1] ^ masks[index]),
        )
        max_runtime_color_churn = max(
            max_runtime_color_churn,
            len(runtime_palettes[index - 1] ^ runtime_palettes[index]),
        )
        previous = suspicious_counts[index - 1]
        current = suspicious_counts[index]
        max_suspicious_churn = max(
            max_suspicious_churn,
            sum(abs(current[item] - previous[item]) for item in range(3)),
        )

    runtime_weak = sum(
        analyze_sprite_artifacts(image).weak_green_or_olive_pixels
        for image in runtime_images
    )

    return TemporalReport(
        sequence_id=sequence_id,
        frame_count=len(frame_paths),
        union_palette_size=len(union_palette),
        max_color_churn=max_color_churn,
        max_alpha_mask_churn=max_alpha_mask_churn,
        max_single_frame_pixels=count_single_frame_pixels(masks),
        suspicious_color_churn=max_suspicious_churn,
        runtime28_max_color_churn=max_runtime_color_churn,
        runtime28_weak_green_or_olive=runtime_weak,
    )


def audit_frames(image_root):
    """Запускает visual diagnostics для всех player/enemy animation frames.

    Args:
        image_root: Корень final image assets.

    Returns:
        Tuple `(diagnostics, errors, temporal_reports)`.
    """
    frame_paths = collect_frame_paths(image_root)
    diagnostics = []
    errors = []
    sequences = {}

    for frame_path in frame_paths:
        sequences.setdefault(get_sequence_id(frame_path), []).append(frame_path)
        with Image.open(frame_path) as image:
            rgba_image = image.convert("RGBA")
            bbox = get_alpha_bbox(rgba_image)
            footprint = get_sprite_footprint(rgba_image)
            report = analyze_sprite_artifacts(rgba_image)
            runtime28_report = analyze_runtime_scaled_artifacts(rgba_image)

        baseline = None if footprint is None else footprint.baseline_y
        relative_path = Path(frame_path).as_posix()
        diagnostics.append(
            (
                f"{relative_path}: size={rgba_image.size} mode={rgba_image.mode} "
                f"bbox={bbox} baseline={baseline} "
                f"visible_pixels={report.visible_pixel_count} "
                f"unique_colors={report.unique_visible_colors} "
                f"visible_chroma={report.visible_chroma_pixels} "
                f"green_dominant={report.green_dominant_artifact_pixels} "
                f"weak_green_or_olive={report.weak_green_or_olive_pixels} "
                f"transparent_rgb={report.transparent_nonzero_rgb} "
                f"semi_alpha={report.semi_transparent_pixels} "
                f"low_alpha={report.low_alpha_pixels} "
                f"isolated_suspicious={report.isolated_suspicious_pixels} "
                f"dark_tinted={report.dark_tinted_pixels} "
                f"yellow_beige={report.yellow_beige_pixels} "
                f"runtime28_unique_colors={runtime28_report.unique_visible_colors} "
                f"runtime28_weak_green_or_olive="
                f"{runtime28_report.weak_green_or_olive_pixels}"
            )
        )

        if report.suspicious_colors:
            diagnostics.append(
                f"{relative_path}: suspicious_colors={report.suspicious_colors}"
            )

        if report.weak_green_or_olive_pixels > 0:
            errors.append(
                f"{relative_path}: weak_green_or_olive="
                f"{report.weak_green_or_olive_pixels}"
            )

        if report.unique_visible_colors > 64:
            errors.append(
                f"{relative_path}: unique_visible_colors="
                f"{report.unique_visible_colors} above 64"
            )

        if runtime28_report.weak_green_or_olive_pixels > 0:
            errors.append(
                f"{relative_path}: runtime28_weak_green_or_olive="
                f"{runtime28_report.weak_green_or_olive_pixels}"
            )

    temporal_reports = [
        analyze_temporal_flicker(sequence_id, sorted(paths))
        for sequence_id, paths in sorted(sequences.items())
    ]

    return diagnostics, errors, temporal_reports


def draw_checkerboard(draw, left, top, width, height, tile_size=8):
    """Рисует checkerboard background.

    Args:
        draw: `ImageDraw.Draw`.
        left: Левая координата области.
        top: Верхняя координата области.
        width: Ширина области.
        height: Высота области.
        tile_size: Размер checker tile.

    Returns:
        None.
    """
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            color = (
                (92, 92, 92, 255)
                if ((x // tile_size + y // tile_size) % 2)
                else (152, 152, 152, 255)
            )
            draw.rectangle(
                (
                    left + x,
                    top + y,
                    left + x + tile_size - 1,
                    top + y + tile_size - 1,
                ),
                fill=color,
            )


def create_preview_sheet(frame_paths, output_path, source_size=(32, 32), scale=8):
    """Создаёт scaled preview sheet для sequence.

    Args:
        frame_paths: Пути кадров sequence.
        output_path: Путь итогового PNG preview.
        source_size: Размер кадра перед увеличением.
        scale: Масштаб preview.

    Returns:
        Путь итогового PNG.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame_paths = list(frame_paths)
    label_height = 14
    cell_width = source_size[0] * scale
    cell_height = source_size[1] * scale
    sheet = Image.new(
        "RGBA",
        (cell_width * len(frame_paths), cell_height + label_height),
        (0, 0, 0, 0),
    )
    draw = ImageDraw.Draw(sheet)

    for index, frame_path in enumerate(frame_paths):
        left = index * cell_width
        draw_checkerboard(draw, left, label_height, cell_width, cell_height)
        with Image.open(frame_path) as image:
            frame = image.convert("RGBA").resize(source_size, Image.Resampling.NEAREST)
            scaled = frame.resize((cell_width, cell_height), Image.Resampling.NEAREST)
        sheet.alpha_composite(scaled, (left, label_height))
        draw.text((left + 3, 1), str(index), fill=(255, 255, 255, 255))

    sheet.save(output_path)
    return output_path


def create_preview_sheets(image_root, preview_root):
    """Создаёт обязательные 32x32 и 28x28 preview sheets.

    Args:
        image_root: Корень final image assets.
        preview_root: Каталог preview output.

    Returns:
        Список созданных путей.
    """
    image_root = Path(image_root)
    preview_root = Path(preview_root)
    created_paths = []

    for sequence_id in PREVIEW_SEQUENCES:
        entity, state_direction = sequence_id.split("/")
        frame_paths = sorted(
            (image_root / "entities" / entity).glob(f"{state_direction}_*.png")
        )
        if not frame_paths:
            continue

        output_stem = f"{entity}_{state_direction}"
        created_paths.append(
            create_preview_sheet(
                frame_paths,
                preview_root / f"{output_stem}_32.png",
                source_size=(32, 32),
            )
        )
        created_paths.append(
            create_preview_sheet(
                frame_paths,
                preview_root / f"{output_stem}_28.png",
                source_size=(28, 28),
            )
        )

    return created_paths


def build_parser():
    """Собирает CLI parser.

    Returns:
        `argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        description="Audit Crown Reclaim entity animation visual stability.",
    )
    parser.add_argument("--image-root", default="assets/images")
    parser.add_argument(
        "--preview-root",
        default="assets/tmp/previews/animation_audit",
    )
    parser.add_argument("--no-previews", action="store_true")
    return parser


def main(argv=None):
    """Запускает visual audit entity animation frames.

    Args:
        argv: Список аргументов командной строки; если `None`, берется `sys.argv`.

    Returns:
        Exit code: `0` при чистом audit, `1` если найдены artifacts.
    """
    args = build_parser().parse_args(argv)
    diagnostics, errors, temporal_reports = audit_frames(args.image_root)

    print("Frame diagnostics")
    for line in diagnostics:
        print(line)

    print("Temporal diagnostics")
    for report in temporal_reports:
        print(
            (
                f"{report.sequence_id}: frames={report.frame_count} "
                f"union_palette={report.union_palette_size} "
                f"max_color_churn={report.max_color_churn} "
                f"max_alpha_mask_churn={report.max_alpha_mask_churn} "
                f"single_frame_pixels={report.max_single_frame_pixels} "
                f"suspicious_color_churn={report.suspicious_color_churn} "
                f"runtime28_max_color_churn={report.runtime28_max_color_churn} "
                f"runtime28_weak_green_or_olive="
                f"{report.runtime28_weak_green_or_olive}"
            )
        )

    if not args.no_previews:
        created_paths = create_preview_sheets(args.image_root, args.preview_root)
        print("Preview sheets")
        for path in created_paths:
            print(path.as_posix())

    if errors:
        print("Audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
