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
        green_dominant_artifact_pixels: Число видимых тёмно-зелёных remnants.
        weak_green_or_olive_pixels: Число слабых olive/green remnants.
        isolated_suspicious_pixels: Число одиночных подозрительных пикселей.
        dark_tinted_pixels: Число очень тёмных видимых пикселей.
        yellow_beige_pixels: Число видимых yellow/beige pixels.
        visible_pixel_count: Число видимых пикселей.
        unique_visible_colors: Число уникальных видимых RGB-цветов.
        suspicious_colors: Частые подозрительные RGBA-цвета для диагностики.
    """
    transparent_nonzero_rgb: int
    semi_transparent_pixels: int
    low_alpha_pixels: int
    visible_chroma_pixels: int
    green_dominant_artifact_pixels: int
    weak_green_or_olive_pixels: int
    isolated_suspicious_pixels: int
    dark_tinted_pixels: int
    yellow_beige_pixels: int
    visible_pixel_count: int
    unique_visible_colors: int
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


def iter_visible_pixels(image):
    """Перебирает видимые RGBA pixels изображения.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Yields:
        RGBA tuple для пикселей с `alpha > 0`.
    """
    rgba_image = image.convert("RGBA")
    pixels = rgba_image.load()
    width, height = rgba_image.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha > 0:
                yield red, green, blue, alpha


def extract_visible_palette(image):
    """Возвращает частоты видимых RGB-цветов.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Returns:
        `Counter`, где ключом является `(red, green, blue)`.
    """
    palette = Counter()

    for red, green, blue, _alpha in iter_visible_pixels(image):
        palette[(red, green, blue)] += 1

    return palette


def get_unique_visible_color_count(image):
    """Считает уникальные видимые RGB-цвета.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Returns:
        Количество уникальных RGB-цветов среди pixels с `alpha > 0`.
    """
    return len(extract_visible_palette(image))


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


def remove_green_dominant_artifacts(image):
    """Удаляет dark/medium green chroma remnants.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Returns:
        RGBA image без green-dominant opaque artifacts.
    """
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if is_green_dominant_artifact_pixel(red, green, blue, alpha):
                pixels[x, y] = (0, 0, 0, 0)

    return cleaned


def remove_weak_green_or_olive_artifacts(image):
    """Удаляет слабые dark olive/green chroma remnants.

    Args:
        image: PIL-изображение с alpha channel или без него.

    Returns:
        RGBA image без weak green/olive remnants.
    """
    cleaned = image.convert("RGBA")
    pixels = cleaned.load()
    width, height = cleaned.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if is_weak_green_or_olive_artifact_pixel(red, green, blue, alpha):
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
    cleaned = remove_green_dominant_artifacts(cleaned)
    cleaned = remove_weak_green_or_olive_artifacts(cleaned)
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
    green_dominant_artifact_pixels = 0
    weak_green_or_olive_pixels = 0
    isolated_suspicious_pixels = 0
    dark_tinted_pixels = 0
    yellow_beige_pixels = 0
    visible_pixel_count = 0
    visible_colors = set()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            color = (red, green, blue, alpha)
            is_suspicious = False

            if alpha > 0:
                visible_pixel_count += 1
                visible_colors.add((red, green, blue))

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

            if is_green_dominant_artifact_pixel(red, green, blue, alpha):
                green_dominant_artifact_pixels += 1
                is_suspicious = True

            if is_weak_green_or_olive_artifact_pixel(red, green, blue, alpha):
                weak_green_or_olive_pixels += 1
                is_suspicious = True

            if is_dark_tinted_pixel(red, green, blue, alpha):
                dark_tinted_pixels += 1

            if is_yellow_beige_pixel(red, green, blue, alpha):
                yellow_beige_pixels += 1

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
        green_dominant_artifact_pixels=green_dominant_artifact_pixels,
        weak_green_or_olive_pixels=weak_green_or_olive_pixels,
        isolated_suspicious_pixels=isolated_suspicious_pixels,
        dark_tinted_pixels=dark_tinted_pixels,
        yellow_beige_pixels=yellow_beige_pixels,
        visible_pixel_count=visible_pixel_count,
        unique_visible_colors=len(visible_colors),
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


def is_green_dominant_artifact_pixel(red, green, blue, alpha):
    """Проверяет dark/medium green chroma remnant.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        alpha: Alpha channel.

    Returns:
        `True`, если visible pixel похож на тёмный chroma-green остаток.
    """
    if alpha == 0:
        return False

    strong_dark_green = (
        green >= 70
        and green >= red + 25
        and green >= blue + 25
    )
    chroma_shadow_green = (
        green >= 90
        and red <= 45
        and blue <= 45
        and green >= max(red, blue) * 2
    )
    return strong_dark_green or chroma_shadow_green


def is_weak_green_or_olive_artifact_pixel(red, green, blue, alpha):
    """Проверяет weak olive/green chroma remnant.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        alpha: Alpha channel.

    Returns:
        `True`, если visible pixel похож на слабый olive/green remnant.
    """
    if alpha == 0:
        return False

    weak_green_tint = (
        green >= 30
        and green >= red + 8
        and green >= blue + 8
        and red <= 35
        and blue <= 35
    )
    olive_shadow = (
        35 <= green <= 90
        and green >= max(red, blue) + 10
        and red <= 45
        and blue <= 45
    )
    return weak_green_tint or olive_shadow


def is_dark_tinted_pixel(red, green, blue, alpha):
    """Проверяет очень тёмный видимый pixel для diagnostics.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        alpha: Alpha channel.

    Returns:
        `True`, если pixel относится к тёмной палитре.
    """
    return alpha > 0 and max(red, green, blue) <= 45


def is_yellow_beige_pixel(red, green, blue, alpha):
    """Проверяет yellow/beige visible pixel для diagnostics.

    Args:
        red: Красный канал.
        green: Зелёный канал.
        blue: Синий канал.
        alpha: Alpha channel.

    Returns:
        `True`, если pixel похож на yellow/beige detail.
    """
    return (
        alpha > 0
        and red >= 90
        and green >= 70
        and blue <= 150
        and red >= blue + 25
        and green >= blue + 10
    )


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
        or is_green_dominant_artifact_pixel(red, green, blue, alpha)
        or is_weak_green_or_olive_artifact_pixel(red, green, blue, alpha)
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


def get_palette_bucket(color, bucket_size=32):
    """Возвращает coarse bucket для RGB-цвета.

    Args:
        color: RGB tuple.
        bucket_size: Размер bucket по каждому каналу.

    Returns:
        Tuple bucket indexes.
    """
    red, green, blue = color
    return red // bucket_size, green // bucket_size, blue // bucket_size


def build_entity_animation_palette(
    images,
    reference_images=(),
    max_colors=64,
    bucket_size=32,
):
    """Строит стабильную palette для группы animation frames.

    Args:
        images: Iterable PIL-кадров animation group.
        reference_images: Дополнительные reference sprites для palette.
        max_colors: Максимальное число representative colors.
        bucket_size: Размер coarse RGB bucket.

    Returns:
        Tuple RGB representative colors.
    """
    bucket_stats = {}

    for image in tuple(reference_images) + tuple(images):
        for color, count in extract_visible_palette(image).items():
            bucket = get_palette_bucket(color, bucket_size)
            if bucket not in bucket_stats:
                bucket_stats[bucket] = [0, 0, 0, 0]

            red, green, blue = color
            bucket_stats[bucket][0] += count
            bucket_stats[bucket][1] += red * count
            bucket_stats[bucket][2] += green * count
            bucket_stats[bucket][3] += blue * count

    representatives = []
    for bucket, (count, red_sum, green_sum, blue_sum) in bucket_stats.items():
        if count <= 0:
            continue

        representatives.append(
            (
                count,
                bucket,
                (
                    round(red_sum / count),
                    round(green_sum / count),
                    round(blue_sum / count),
                ),
            )
        )

    representatives.sort(key=lambda item: (-item[0], item[1], item[2]))
    palette = tuple(color for _count, _bucket, color in representatives[:max_colors])

    if not palette:
        return ((0, 0, 0),)

    return palette


def find_nearest_palette_color(color, palette):
    """Возвращает ближайший RGB-цвет из palette.

    Args:
        color: RGB tuple исходного pixel.
        palette: Tuple RGB representative colors.

    Returns:
        RGB tuple из palette.
    """
    red, green, blue = color
    return min(
        palette,
        key=lambda palette_color: (
            (red - palette_color[0]) ** 2
            + (green - palette_color[1]) ** 2
            + (blue - palette_color[2]) ** 2
        ),
    )


def quantize_sprite_to_palette(image, palette):
    """Стабилизирует RGB pixels через nearest palette color.

    Args:
        image: PIL-изображение с alpha channel или без него.
        palette: Tuple RGB representative colors.

    Returns:
        RGBA image с исходной alpha mask и palette-snapped RGB.
    """
    quantized = image.convert("RGBA")
    pixels = quantized.load()
    width, height = quantized.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue

            nearest = find_nearest_palette_color((red, green, blue), palette)
            pixels[x, y] = (nearest[0], nearest[1], nearest[2], alpha)

    return quantized


def stabilize_animation_sequence_palette(
    images,
    reference_images=(),
    max_colors=64,
    bucket_size=32,
):
    """Стабилизирует palette группы кадров без dithering.

    Args:
        images: Iterable PIL-кадров animation group.
        reference_images: Дополнительные reference sprites для palette.
        max_colors: Максимальное число цветов в общей palette.
        bucket_size: Размер coarse RGB bucket.

    Returns:
        Tuple `(stabilized_images, palette)`.
    """
    cleaned_images = [clean_sprite_artifacts(image) for image in images]
    cleaned_references = [clean_sprite_artifacts(image) for image in reference_images]
    palette = build_entity_animation_palette(
        cleaned_images,
        reference_images=cleaned_references,
        max_colors=max_colors,
        bucket_size=bucket_size,
    )
    stabilized_images = [
        clean_sprite_artifacts(quantize_sprite_to_palette(image, palette))
        for image in cleaned_images
    ]
    return stabilized_images, palette


def analyze_runtime_scaled_artifacts(image, runtime_size=(28, 28)):
    """Возвращает artifact diagnostics для runtime-size preview.

    Args:
        image: PIL-изображение с alpha channel или без него.
        runtime_size: Размер diagnostic runtime preview.

    Returns:
        `SpriteArtifactReport` для nearest-resized image.
    """
    runtime_image = image.convert("RGBA").resize(
        runtime_size,
        Image.Resampling.NEAREST,
    )
    return analyze_sprite_artifacts(runtime_image)


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
    max_palette_colors=64,
):
    """Нормализует и стабилизирует набор PNG кадров.

    Args:
        frame_paths: Пути PNG кадров, которые нужно перезаписать.
        reference_path: Путь к static sprite reference.
        output_size: Размер итогового canvas.
        max_scale: Максимально допустимый scale factor или `None`.
        max_palette_colors: Максимальное число цветов общей stable palette.

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
    normalized_images = []

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

        normalized_images.append(normalized)

    reference_images = []
    reference_path = Path(reference_path) if reference_path is not None else None
    if reference_path is not None and reference_path.is_file():
        with Image.open(reference_path) as reference_image:
            reference_images.append(reference_image.convert("RGBA"))

    stabilized_images, _palette = stabilize_animation_sequence_palette(
        normalized_images,
        reference_images=reference_images,
        max_colors=max_palette_colors,
    )

    for frame_path, stabilized_image in zip(existing_frame_paths, stabilized_images):
        stabilized_image.save(frame_path)

    return len(stabilized_images)
