import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

try:
    from .sprite_normalization import (
        analyze_sprite_artifacts,
        analyze_runtime_scaled_artifacts,
        get_alpha_bbox,
        get_sprite_footprint,
    )
except ImportError:
    from sprite_normalization import (
        analyze_sprite_artifacts,
        analyze_runtime_scaled_artifacts,
        get_alpha_bbox,
        get_sprite_footprint,
    )


DEFAULT_ENTITIES = ("player", "enemy")
DEFAULT_STATES = ("walk", "attack")
EXPECTED_SIZE = (32, 32)


@dataclass
class ValidationResult:
    """Хранит результат проверки animation frame footprint.

    Attributes:
        diagnostics: Человекочитаемые строки диагностики.
        errors: Строки ошибок validator.
    """
    diagnostics: list[str]
    errors: list[str]

    @property
    def passed(self):
        """Проверяет, прошла ли validation без ошибок.

        Returns:
            `True`, если ошибок нет.
        """
        return not self.errors


def validate_entity_animation_frames(
    image_root="assets/images",
    entities=DEFAULT_ENTITIES,
    states=DEFAULT_STATES,
    expected_size=EXPECTED_SIZE,
    min_height_ratio=0.75,
    max_height_ratio=1.25,
    min_width_ratio=0.75,
    max_walk_width_ratio=1.25,
    max_attack_width_ratio=1.50,
    max_baseline_delta=3,
    max_transparent_nonzero_rgb=0,
    max_visible_chroma_pixels=0,
    max_green_dominant_artifact_pixels=0,
    max_weak_green_or_olive_pixels=0,
    max_low_alpha_pixels=0,
    max_isolated_suspicious_pixels=0,
    max_unique_visible_colors=64,
    max_runtime28_weak_green_or_olive_pixels=0,
):
    """Проверяет footprint и pixel artifacts существующих animation frames.

    Args:
        image_root: Корень final game-ready PNG ассетов.
        entities: Entity keys, например `player` и `enemy`.
        states: Animation states, которые нужно проверить.
        expected_size: Ожидаемый canvas size кадра.
        min_height_ratio: Минимальная доля высоты относительно static reference.
        max_height_ratio: Максимальная доля высоты относительно static reference.
        min_width_ratio: Минимальная доля ширины относительно static reference.
        max_walk_width_ratio: Максимальная доля ширины walk кадра.
        max_attack_width_ratio: Максимальная доля ширины attack кадра.
        max_baseline_delta: Допустимое отклонение baseline в пикселях.
        max_transparent_nonzero_rgb: Допустимое число прозрачных пикселей с RGB.
        max_visible_chroma_pixels: Допустимое число видимых chroma pixels.
        max_green_dominant_artifact_pixels: Допустимое число green-dominant remnants.
        max_weak_green_or_olive_pixels: Допустимое число weak olive/green remnants.
        max_low_alpha_pixels: Допустимое число low-alpha visible pixels.
        max_isolated_suspicious_pixels: Допустимое число isolated artifacts.
        max_unique_visible_colors: Допустимое число видимых RGB-цветов.
        max_runtime28_weak_green_or_olive_pixels: Допустимое число runtime28 remnants.

    Returns:
        `ValidationResult` с diagnostics и errors.
    """
    image_root = Path(image_root)
    diagnostics = []
    errors = []

    for entity in entities:
        reference_path = image_root / "entities" / f"{entity}.png"
        reference_footprint = load_reference_footprint(reference_path)

        if reference_footprint is None:
            diagnostics.append(f"{entity}: missing or transparent static reference")
            continue

        diagnostics.append(
            (
                f"{entity} static: bbox={reference_footprint.width}x"
                f"{reference_footprint.height} baseline={reference_footprint.baseline_y}"
            )
        )

        entity_dir = image_root / "entities" / entity
        frame_paths = collect_frame_paths(entity_dir, states)

        if not frame_paths:
            diagnostics.append(f"{entity}: no animation frames found")
            continue

        for frame_path in frame_paths:
            validate_frame(
                frame_path,
                reference_footprint,
                expected_size,
                min_height_ratio,
                max_height_ratio,
                min_width_ratio,
                max_walk_width_ratio,
                max_attack_width_ratio,
                max_baseline_delta,
                max_transparent_nonzero_rgb,
                max_visible_chroma_pixels,
                max_green_dominant_artifact_pixels,
                max_weak_green_or_olive_pixels,
                max_low_alpha_pixels,
                max_isolated_suspicious_pixels,
                max_unique_visible_colors,
                max_runtime28_weak_green_or_olive_pixels,
                diagnostics,
                errors,
            )

    return ValidationResult(diagnostics=diagnostics, errors=errors)


def load_reference_footprint(reference_path):
    """Загружает footprint static reference.

    Args:
        reference_path: Путь к static sprite PNG.

    Returns:
        `SpriteFootprint` или `None`.
    """
    if not reference_path.is_file():
        return None

    with Image.open(reference_path) as image:
        return get_sprite_footprint(image)


def collect_frame_paths(entity_dir, states):
    """Собирает существующие animation frame paths.

    Args:
        entity_dir: Каталог кадров entity.
        states: Animation states для проверки.

    Returns:
        Отсортированный список PNG кадров.
    """
    frame_paths = []

    if not entity_dir.is_dir():
        return frame_paths

    for state in states:
        frame_paths.extend(sorted(entity_dir.glob(f"{state}_*.png")))

    return frame_paths


def validate_frame(
    frame_path,
    reference_footprint,
    expected_size,
    min_height_ratio,
    max_height_ratio,
    min_width_ratio,
    max_walk_width_ratio,
    max_attack_width_ratio,
    max_baseline_delta,
    max_transparent_nonzero_rgb,
    max_visible_chroma_pixels,
    max_green_dominant_artifact_pixels,
    max_weak_green_or_olive_pixels,
    max_low_alpha_pixels,
    max_isolated_suspicious_pixels,
    max_unique_visible_colors,
    max_runtime28_weak_green_or_olive_pixels,
    diagnostics,
    errors,
):
    """Проверяет один animation frame на footprint и pixel artifacts.

    Args:
        frame_path: Путь к PNG кадру.
        reference_footprint: Footprint static sprite.
        expected_size: Ожидаемый размер canvas.
        min_height_ratio: Минимальная доля высоты относительно reference.
        max_height_ratio: Максимальная доля высоты относительно reference.
        min_width_ratio: Минимальная доля ширины относительно reference.
        max_walk_width_ratio: Максимальная доля ширины walk frame.
        max_attack_width_ratio: Максимальная доля ширины attack frame.
        max_baseline_delta: Допустимое отклонение baseline.
        max_transparent_nonzero_rgb: Допустимое число прозрачных пикселей с RGB.
        max_visible_chroma_pixels: Допустимое число видимых chroma pixels.
        max_green_dominant_artifact_pixels: Допустимое число green-dominant remnants.
        max_weak_green_or_olive_pixels: Допустимое число weak olive/green remnants.
        max_low_alpha_pixels: Допустимое число low-alpha visible pixels.
        max_isolated_suspicious_pixels: Допустимое число isolated artifacts.
        max_unique_visible_colors: Допустимое число видимых RGB-цветов.
        max_runtime28_weak_green_or_olive_pixels: Допустимое число runtime28 remnants.
        diagnostics: Список строк диагностики.
        errors: Список строк ошибок.

    Returns:
        None.
    """
    with Image.open(frame_path) as image:
        mode = image.mode
        size = image.size
        rgba_image = image.convert("RGBA")
        bbox = get_alpha_bbox(rgba_image)
        footprint = get_sprite_footprint(rgba_image)
        artifact_report = analyze_sprite_artifacts(rgba_image)
        runtime28_report = analyze_runtime_scaled_artifacts(rgba_image)

    relative_path = frame_path.as_posix()

    if size != expected_size:
        errors.append(f"{relative_path}: expected size {expected_size}, got {size}")

    if not has_alpha_mode(mode):
        errors.append(f"{relative_path}: expected alpha-compatible PNG mode, got {mode}")

    if bbox is None or footprint is None:
        errors.append(f"{relative_path}: empty alpha bbox")
        return

    height_ratio = footprint.height / reference_footprint.height
    width_ratio = footprint.width / reference_footprint.width
    baseline_delta = abs(footprint.baseline_y - reference_footprint.baseline_y)
    state = get_state_from_frame_path(frame_path)
    max_width_ratio = max_attack_width_ratio if state == "attack" else max_walk_width_ratio

    diagnostics.append(
        (
            f"{relative_path}: mode={mode} size={size} bbox={bbox} "
            f"bbox_size={footprint.width}x{footprint.height} "
            f"height_ratio={height_ratio:.2f} width_ratio={width_ratio:.2f} "
            f"baseline_delta={baseline_delta} "
            f"transparent_rgb={artifact_report.transparent_nonzero_rgb} "
            f"semi_alpha={artifact_report.semi_transparent_pixels} "
            f"low_alpha={artifact_report.low_alpha_pixels} "
            f"visible_chroma={artifact_report.visible_chroma_pixels} "
            f"green_dominant={artifact_report.green_dominant_artifact_pixels} "
            f"weak_green_or_olive={artifact_report.weak_green_or_olive_pixels} "
            f"isolated_suspicious={artifact_report.isolated_suspicious_pixels} "
            f"visible_pixels={artifact_report.visible_pixel_count} "
            f"unique_colors={artifact_report.unique_visible_colors} "
            f"runtime28_unique_colors={runtime28_report.unique_visible_colors} "
            f"runtime28_weak_green_or_olive="
            f"{runtime28_report.weak_green_or_olive_pixels}"
        )
    )
    suspicious_total = sum(count for _, count in artifact_report.suspicious_colors)
    if artifact_report.suspicious_colors and suspicious_total <= 24:
        diagnostics.append(
            f"{relative_path}: suspicious_colors={artifact_report.suspicious_colors}"
        )

    if height_ratio < min_height_ratio:
        errors.append(
            f"{relative_path}: visible height ratio {height_ratio:.2f} below {min_height_ratio}"
        )

    if height_ratio > max_height_ratio:
        errors.append(
            f"{relative_path}: visible height ratio {height_ratio:.2f} above {max_height_ratio}"
        )

    if width_ratio < min_width_ratio:
        errors.append(
            f"{relative_path}: visible width ratio {width_ratio:.2f} below {min_width_ratio}"
        )

    if width_ratio > max_width_ratio:
        errors.append(
            f"{relative_path}: visible width ratio {width_ratio:.2f} above {max_width_ratio}"
        )

    if baseline_delta > max_baseline_delta:
        errors.append(
            f"{relative_path}: baseline delta {baseline_delta} above {max_baseline_delta}"
        )

    if artifact_report.transparent_nonzero_rgb > max_transparent_nonzero_rgb:
        errors.append(
            (
                f"{relative_path}: transparent pixels with non-zero RGB "
                f"{artifact_report.transparent_nonzero_rgb} above "
                f"{max_transparent_nonzero_rgb}"
            )
        )

    if artifact_report.visible_chroma_pixels > max_visible_chroma_pixels:
        errors.append(
            (
                f"{relative_path}: visible chroma pixels "
                f"{artifact_report.visible_chroma_pixels} above "
                f"{max_visible_chroma_pixels}"
            )
        )

    if (
        artifact_report.green_dominant_artifact_pixels
        > max_green_dominant_artifact_pixels
    ):
        errors.append(
            (
                f"{relative_path}: green-dominant artifact pixels "
                f"{artifact_report.green_dominant_artifact_pixels} above "
                f"{max_green_dominant_artifact_pixels}"
            )
        )

    if artifact_report.weak_green_or_olive_pixels > max_weak_green_or_olive_pixels:
        errors.append(
            (
                f"{relative_path}: weak green/olive artifact pixels "
                f"{artifact_report.weak_green_or_olive_pixels} above "
                f"{max_weak_green_or_olive_pixels}"
            )
        )

    if artifact_report.low_alpha_pixels > max_low_alpha_pixels:
        errors.append(
            (
                f"{relative_path}: low-alpha pixels "
                f"{artifact_report.low_alpha_pixels} above {max_low_alpha_pixels}"
            )
        )

    if artifact_report.unique_visible_colors > max_unique_visible_colors:
        errors.append(
            (
                f"{relative_path}: unique visible colors "
                f"{artifact_report.unique_visible_colors} above "
                f"{max_unique_visible_colors}"
            )
        )

    if (
        runtime28_report.weak_green_or_olive_pixels
        > max_runtime28_weak_green_or_olive_pixels
    ):
        errors.append(
            (
                f"{relative_path}: runtime28 weak green/olive artifact pixels "
                f"{runtime28_report.weak_green_or_olive_pixels} above "
                f"{max_runtime28_weak_green_or_olive_pixels}"
            )
        )

    if artifact_report.isolated_suspicious_pixels > max_isolated_suspicious_pixels:
        errors.append(
            (
                f"{relative_path}: isolated suspicious pixels "
                f"{artifact_report.isolated_suspicious_pixels} above "
                f"{max_isolated_suspicious_pixels}"
            )
        )


def has_alpha_mode(mode):
    """Проверяет, поддерживает ли PNG mode alpha channel.

    Args:
        mode: PIL image mode.

    Returns:
        `True`, если mode совместим с alpha.
    """
    return mode in {"RGBA", "LA", "PA"}


def get_state_from_frame_path(frame_path):
    """Возвращает animation state из имени кадра.

    Args:
        frame_path: Путь к PNG кадру.

    Returns:
        State до первого `_`, например `walk` или `attack`.
    """
    return frame_path.stem.split("_", 1)[0]


def build_parser():
    """Собирает CLI parser validator.

    Returns:
        `argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        description="Validate Crown Reclaim entity animation frame footprints and artifacts.",
    )
    parser.add_argument("--image-root", default="assets/images")
    return parser


def main(argv=None):
    """Запускает validator animation frame footprint.

    Args:
        argv: Список аргументов командной строки; если `None`, берется `sys.argv`.

    Returns:
        Exit code: `0` при успехе, `1` при ошибках.
    """
    args = build_parser().parse_args(argv)
    result = validate_entity_animation_frames(image_root=args.image_root)

    for line in result.diagnostics:
        print(line)

    if result.errors:
        print("Validation failed:")
        for error in result.errors:
            print(f"- {error}")
        return 1

    print("Validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
