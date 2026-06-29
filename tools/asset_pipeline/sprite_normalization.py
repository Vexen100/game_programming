from dataclasses import dataclass
from pathlib import Path
from statistics import median

from PIL import Image


@dataclass(frozen=True)
class SpriteFootprint:
    """Описывает видимый footprint спрайта по alpha bbox.

    Attributes:
        width: Ширина видимой alpha bbox.
        height: Высота видимой alpha bbox.
        baseline_y: Нижняя строка видимой alpha bbox.
    """
    width: int
    height: int
    baseline_y: int


def get_alpha_bbox(image):
    """Возвращает alpha bbox изображения.

    Args:
        image: PIL-изображение с альфой или без неё.

    Returns:
        Tuple `(left, top, right, bottom)` или `None`, если видимых пикселей нет.
    """
    rgba_image = image.convert("RGBA")
    return rgba_image.getchannel("A").getbbox()


def get_visible_size(image):
    """Возвращает размер видимой alpha bbox.

    Args:
        image: PIL-изображение с альфой или без неё.

    Returns:
        Tuple `(width, height)` видимой области или `(0, 0)`.
    """
    bbox = get_alpha_bbox(image)

    if bbox is None:
        return 0, 0

    left, top, right, bottom = bbox
    return right - left, bottom - top


def get_sprite_footprint(image):
    """Возвращает footprint спрайта по alpha bbox.

    Args:
        image: PIL-изображение с альфой или без неё.

    Returns:
        `SpriteFootprint` или `None`, если видимых пикселей нет.
    """
    bbox = get_alpha_bbox(image)

    if bbox is None:
        return None

    left, top, right, bottom = bbox
    return SpriteFootprint(
        width=right - left,
        height=bottom - top,
        baseline_y=bottom - 1,
    )


def normalize_sprite_frame(
    image,
    output_size=(32, 32),
    target_visible_height=None,
    target_visible_width=None,
    baseline_y=None,
    max_scale=None,
):
    """Нормализует один animation frame под общий visual footprint.

    Args:
        image: Входной PIL frame.
        output_size: Размер итогового transparent canvas.
        target_visible_height: Целевая высота видимой alpha bbox.
        target_visible_width: Целевая ширина видимой alpha bbox.
        baseline_y: Целевая нижняя строка видимой alpha bbox.
        max_scale: Максимально допустимый scale factor или `None`.

    Returns:
        RGBA image с тем же canvas size и bottom-center alignment.
    """
    output_width, output_height = output_size
    rgba_image = image.convert("RGBA")
    bbox = get_alpha_bbox(rgba_image)

    if bbox is None:
        return Image.new("RGBA", output_size, (0, 0, 0, 0))

    cropped = rgba_image.crop(bbox)
    safe_width = max(1, output_width - 2)
    safe_height = max(1, output_height - 2)
    scale_x, scale_y = get_normalization_scales(
        cropped,
        safe_width,
        safe_height,
        target_visible_width,
        target_visible_height,
        max_scale,
    )

    resized_width = max(1, round(cropped.width * scale_x))
    resized_height = max(1, round(cropped.height * scale_y))
    resized = cropped.resize(
        (resized_width, resized_height),
        Image.Resampling.NEAREST,
    )

    canvas = Image.new("RGBA", output_size, (0, 0, 0, 0))
    target_baseline_y = baseline_y
    if target_baseline_y is None:
        target_baseline_y = output_height - 2

    paste_x = (output_width - resized_width) // 2
    paste_y = round(target_baseline_y - resized_height + 1)
    paste_y = max(0, min(output_height - resized_height, paste_y))

    canvas.alpha_composite(resized, (paste_x, paste_y))
    return canvas


def get_normalization_scale(
    cropped,
    safe_width,
    safe_height,
    target_visible_width,
    target_visible_height,
    max_scale,
):
    """Возвращает scale factor для нормализации visible bbox.

    Args:
        cropped: Обрезанный по alpha bbox кадр.
        safe_width: Максимальная безопасная ширина внутри output canvas.
        safe_height: Максимальная безопасная высота внутри output canvas.
        target_visible_width: Целевая ширина visible bbox или `None`.
        target_visible_height: Целевая высота visible bbox или `None`.
        max_scale: Максимально допустимый scale factor или `None`.

    Returns:
        Числовой scale factor.
    """
    scale_candidates = []

    if target_visible_width is not None:
        scale_candidates.append(max(1, target_visible_width) / cropped.width)

    if target_visible_height is not None:
        scale_candidates.append(max(1, target_visible_height) / cropped.height)

    if scale_candidates:
        scale = min(scale_candidates)
    else:
        scale = min(safe_width / cropped.width, safe_height / cropped.height)

    canvas_scale_limit = min(safe_width / cropped.width, safe_height / cropped.height)
    scale = min(scale, canvas_scale_limit)

    if max_scale is not None:
        scale = min(scale, max_scale)

    return max(scale, 1 / max(cropped.width, cropped.height))


def get_normalization_scales(
    cropped,
    safe_width,
    safe_height,
    target_visible_width,
    target_visible_height,
    max_scale,
):
    """Возвращает X/Y scale factors для target footprint.

    Args:
        cropped: Обрезанный по alpha bbox кадр.
        safe_width: Максимальная безопасная ширина внутри output canvas.
        safe_height: Максимальная безопасная высота внутри output canvas.
        target_visible_width: Целевая ширина visible bbox или `None`.
        target_visible_height: Целевая высота visible bbox или `None`.
        max_scale: Максимально допустимый scale factor или `None`.

    Returns:
        Пара `(scale_x, scale_y)`.
    """
    if target_visible_width is None or target_visible_height is None:
        scale = get_normalization_scale(
            cropped,
            safe_width,
            safe_height,
            target_visible_width,
            target_visible_height,
            max_scale,
        )
        return scale, scale

    scale_x = max(1, target_visible_width) / cropped.width
    scale_y = max(1, target_visible_height) / cropped.height
    scale_x = min(scale_x, safe_width / cropped.width)
    scale_y = min(scale_y, safe_height / cropped.height)

    if max_scale is not None:
        scale_x = min(scale_x, max_scale)
        scale_y = min(scale_y, max_scale)

    return (
        max(scale_x, 1 / cropped.width),
        max(scale_y, 1 / cropped.height),
    )


def get_reference_footprint(reference_path=None, frame_paths=(), output_size=(32, 32)):
    """Возвращает reference footprint из static sprite или median кадров.

    Args:
        reference_path: Путь к static sprite entity.
        frame_paths: Пути кадров, используемые как fallback reference.
        output_size: Размер итогового canvas.

    Returns:
        `SpriteFootprint` для нормализации.
    """
    reference_path = Path(reference_path) if reference_path is not None else None

    if reference_path is not None and reference_path.is_file():
        with Image.open(reference_path) as reference_image:
            footprint = get_sprite_footprint(reference_image)
            if footprint is not None:
                return footprint

    footprints = []
    for frame_path in frame_paths:
        frame_path = Path(frame_path)
        if not frame_path.is_file():
            continue

        with Image.open(frame_path) as frame_image:
            footprint = get_sprite_footprint(frame_image)
            if footprint is not None:
                footprints.append(footprint)

    if footprints:
        return SpriteFootprint(
            width=round(median(footprint.width for footprint in footprints)),
            height=round(median(footprint.height for footprint in footprints)),
            baseline_y=round(median(footprint.baseline_y for footprint in footprints)),
        )

    output_width, output_height = output_size
    return SpriteFootprint(
        width=output_width - 4,
        height=output_height - 4,
        baseline_y=output_height - 2,
    )


def normalize_sprite_files(
    frame_paths,
    reference_path=None,
    output_size=(32, 32),
    max_scale=None,
):
    """Нормализует набор PNG кадров относительно reference footprint.

    Args:
        frame_paths: Пути PNG кадров, которые нужно перезаписать.
        reference_path: Путь к static sprite reference.
        output_size: Размер итогового canvas.
        max_scale: Максимально допустимый scale factor или `None`.

    Returns:
        Количество перепроцессенных кадров.
    """
    frame_paths = [Path(frame_path) for frame_path in frame_paths]
    existing_frame_paths = [frame_path for frame_path in frame_paths if frame_path.is_file()]
    reference = get_reference_footprint(
        reference_path=reference_path,
        frame_paths=existing_frame_paths,
        output_size=output_size,
    )
    processed_count = 0

    for frame_path in existing_frame_paths:
        with Image.open(frame_path) as frame_image:
            normalized = normalize_sprite_frame(
                frame_image,
                output_size=output_size,
                target_visible_height=reference.height,
                target_visible_width=reference.width,
                baseline_y=reference.baseline_y,
                max_scale=max_scale,
            )

        normalized.save(frame_path)
        processed_count += 1

    return processed_count
