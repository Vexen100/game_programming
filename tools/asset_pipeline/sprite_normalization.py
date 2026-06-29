from collections import Counter
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


@dataclass(frozen=True)
class SpriteArtifactReport:
    """Описывает найденные pixel artifacts в RGBA-спрайте.

    Attributes:
        transparent_nonzero_rgb: Число прозрачных пикселей с ненулевым RGB.
        semi_transparent_pixels: Число пикселей с alpha между `0` и `255`.
        low_alpha_pixels: Число видимых пикселей с почти нулевой alpha.
        visible_chroma_pixels: Число видимых пикселей, похожих на chroma green.
        isolated_suspicious_pixels: Число одиночных подозрительных пикселей.
        suspicious_colors: Частые подозрительные RGBA-цвета для диагностики.
    """
    transparent_nonzero_rgb: int
    semi_transparent_pixels: int
    low_alpha_pixels: int
    visible_chroma_pixels: int
    isolated_suspicious_pixels: int
    suspicious_colors: tuple


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


def clean_transparent_rgb(image):
    """Обнуляет RGB у fully transparent пикселей.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Returns:
        RGBA image, где все пиксели с `alpha == 0` равны `(0, 0, 0, 0)`.
    """
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0 and (red, green, blue) != (0, 0, 0):
                pixels[x, y] = (0, 0, 0, 0)

    return cleaned


def remove_chroma_pixels(image, chroma_color=(0, 255, 0), tolerance=40):
    """Делает transparent пиксели, похожие на chroma green.

    Args:
        image: PIL-изображение с alpha channel или без него.
        chroma_color: Базовый chroma color.
        tolerance: RGB-distance tolerance для точного chroma key.

    Returns:
        RGBA image без видимых chroma-green remnants.
    """
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 0 and is_chroma_pixel(red, green, blue, chroma_color, tolerance):
                pixels[x, y] = (0, 0, 0, 0)

    return cleaned


def remove_low_alpha_pixels(image, alpha_threshold=16):
    """Удаляет почти прозрачный цветной noise.

    Args:
        image: PIL-изображение с alpha channel или без него.
        alpha_threshold: Максимальная alpha, которую нужно считать мусорной.

    Returns:
        RGBA image без low-alpha noise.
    """
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if 0 < alpha <= alpha_threshold:
                pixels[x, y] = (0, 0, 0, 0)

    return cleaned


def remove_isolated_alpha_pixels(
    image,
    min_neighbors=1,
    artifact_alpha_threshold=64,
):
    """Удаляет одиночные слабые или debug-colored pixels.

    Args:
        image: PIL-изображение с alpha channel или без него.
        min_neighbors: Минимальное число видимых соседей в 8-neighborhood.
        artifact_alpha_threshold: Alpha, ниже которой одиночный пиксель считается шумом.

    Returns:
        RGBA image с удалёнными одиночными подозрительными пикселями.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size
    cleaned = rgba_image.copy()
    cleaned_pixels = cleaned.load()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue

            if not is_isolated_artifact_candidate(
                red,
                green,
                blue,
                alpha,
                artifact_alpha_threshold,
            ):
                continue

            if count_visible_neighbors(pixels, x, y, width, height) < min_neighbors:
                cleaned_pixels[x, y] = (0, 0, 0, 0)

    return cleaned


def clean_sprite_artifacts(
    image,
    chroma_color=(0, 255, 0),
    chroma_tolerance=40,
    alpha_threshold=16,
    min_neighbors=1,
    artifact_alpha_threshold=64,
):
    """Чистит chroma/alpha artifacts у entity animation frame.

    Args:
        image: PIL-изображение с alpha channel или без него.
        chroma_color: Базовый chroma color.
        chroma_tolerance: RGB-distance tolerance для chroma cleanup.
        alpha_threshold: Максимальная alpha для удаления low-alpha noise.
        min_neighbors: Минимальное число соседей для одиночных пикселей.
        artifact_alpha_threshold: Alpha, ниже которой isolated pixel считается noise.

    Returns:
        RGBA image с прозрачным фоном и без chroma/alpha мусора.
    """
    cleaned = clean_transparent_rgb(image)
    cleaned = remove_chroma_pixels(cleaned, chroma_color, chroma_tolerance)
    cleaned = remove_low_alpha_pixels(cleaned, alpha_threshold)
    cleaned = remove_isolated_alpha_pixels(
        cleaned,
        min_neighbors=min_neighbors,
        artifact_alpha_threshold=artifact_alpha_threshold,
    )
    return clean_transparent_rgb(cleaned)


def analyze_sprite_artifacts(
    image,
    chroma_color=(0, 255, 0),
    chroma_tolerance=40,
    low_alpha_threshold=16,
    isolated_min_neighbors=1,
    isolated_alpha_threshold=64,
):
    """Считает suspicious pixels в sprite frame.

    Args:
        image: PIL-изображение с alpha channel или без него.
        chroma_color: Базовый chroma color.
        chroma_tolerance: RGB-distance tolerance для chroma detection.
        low_alpha_threshold: Максимальная alpha для low-alpha diagnostics.
        isolated_min_neighbors: Минимум соседей для isolated-pixel проверки.
        isolated_alpha_threshold: Alpha, ниже которой isolated pixel подозрителен.

    Returns:
        `SpriteArtifactReport` с количественной диагностикой.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size
    suspicious_colors = Counter()
    transparent_nonzero_rgb = 0
    semi_transparent_pixels = 0
    low_alpha_pixels = 0
    visible_chroma_pixels = 0
    isolated_suspicious_pixels = 0

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            color = (red, green, blue, alpha)
            is_suspicious = False

            if alpha == 0 and (red, green, blue) != (0, 0, 0):
                transparent_nonzero_rgb += 1
                is_suspicious = True

            if 0 < alpha < 255:
                semi_transparent_pixels += 1

            if 0 < alpha <= low_alpha_threshold:
                low_alpha_pixels += 1
                is_suspicious = True

            if alpha > 0 and is_chroma_pixel(
                red,
                green,
                blue,
                chroma_color,
                chroma_tolerance,
            ):
                visible_chroma_pixels += 1
                is_suspicious = True

            if alpha > 0 and is_isolated_artifact_candidate(
                red,
                green,
                blue,
                alpha,
                isolated_alpha_threshold,
            ):
                neighbor_count = count_visible_neighbors(pixels, x, y, width, height)
                if neighbor_count < isolated_min_neighbors:
                    isolated_suspicious_pixels += 1
                    is_suspicious = True

            if is_suspicious:
                suspicious_colors[color] += 1

    return SpriteArtifactReport(
        transparent_nonzero_rgb=transparent_nonzero_rgb,
        semi_transparent_pixels=semi_transparent_pixels,
        low_alpha_pixels=low_alpha_pixels,
        visible_chroma_pixels=visible_chroma_pixels,
        isolated_suspicious_pixels=isolated_suspicious_pixels,
        suspicious_colors=tuple(suspicious_colors.most_common(8)),
    )


def is_chroma_pixel(red, green, blue, chroma_color=(0, 255, 0), tolerance=40):
    """Проверяет, похож ли RGB на chroma-green background.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        chroma_color: Базовый chroma color.
        tolerance: Допустимая RGB-distance для точного совпадения.

    Returns:
        `True`, если цвет выглядит как chroma remnant.
    """
    chroma_red, chroma_green, chroma_blue = chroma_color
    channel_rule = green >= 150 and green - red >= 70 and green - blue >= 70
    distance_rule = (
        abs(red - chroma_red)
        + abs(green - chroma_green)
        + abs(blue - chroma_blue)
        <= tolerance
    )
    return channel_rule or distance_rule


def is_debug_artifact_color(red, green, blue):
    """Проверяет debug-like magenta/cyan colors.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.

    Returns:
        `True`, если цвет похож на debug-pink или cyan artifact.
    """
    is_magenta = red >= 180 and blue >= 180 and green <= 80
    is_cyan = green >= 180 and blue >= 180 and red <= 80
    return is_magenta or is_cyan


def is_isolated_artifact_candidate(
    red,
    green,
    blue,
    alpha,
    artifact_alpha_threshold,
):
    """Проверяет, стоит ли isolated pixel считать подозрительным.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        alpha: Alpha channel.
        artifact_alpha_threshold: Alpha-порог для слабого isolated noise.

    Returns:
        `True`, если одиночный пиксель можно безопасно удалить.
    """
    return (
        alpha <= artifact_alpha_threshold
        or is_chroma_pixel(red, green, blue)
        or is_debug_artifact_color(red, green, blue)
    )


def count_visible_neighbors(pixels, x, y, width, height):
    """Считает видимых соседей пикселя в 8-neighborhood.

    Args:
        pixels: Pixel access object PIL.
        x: X-координата пикселя.
        y: Y-координата пикселя.
        width: Ширина изображения.
        height: Высота изображения.

    Returns:
        Количество соседей с `alpha > 0`.
    """
    visible_neighbors = 0

    for offset_y in (-1, 0, 1):
        for offset_x in (-1, 0, 1):
            if offset_x == 0 and offset_y == 0:
                continue

            neighbor_x = x + offset_x
            neighbor_y = y + offset_y

            if not (0 <= neighbor_x < width and 0 <= neighbor_y < height):
                continue

            if pixels[neighbor_x, neighbor_y][3] > 0:
                visible_neighbors += 1

    return visible_neighbors


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
            cleaned_frame = clean_sprite_artifacts(frame_image)
            normalized = normalize_sprite_frame(
                cleaned_frame,
                output_size=output_size,
                target_visible_height=reference.height,
                target_visible_width=reference.width,
                baseline_y=reference.baseline_y,
                max_scale=max_scale,
            )
            normalized = clean_sprite_artifacts(normalized)

        normalized.save(frame_path)
        processed_count += 1

    return processed_count
