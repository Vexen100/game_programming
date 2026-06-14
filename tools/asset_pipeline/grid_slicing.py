from PIL import Image


def parse_csv(value: str) -> list[str]:
    """Разбирает строку CSV в список значений.

    Args:
        value: Значение, которое нужно проверить, ограничить или преобразовать.

    Returns:
        Разобранное значение: csv.
    """
    if value is None:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def parse_hex_color(value: str) -> tuple[int, int, int]:
    """Разбирает цвет в формате #RRGGBB.

    Args:
        value: Значение, которое нужно проверить, ограничить или преобразовать.

    Returns:
        Разобранное значение: hex цвет.
    """
    if not isinstance(value, str):
        raise ValueError("Color must be a string in #RRGGBB format")

    value = value.strip()

    if value.startswith("#"):
        value = value[1:]

    if len(value) != 6:
        raise ValueError("Color must be in #RRGGBB format")

    try:
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )
    except ValueError as error:
        raise ValueError("Color must be in #RRGGBB format") from error


def get_grid_boxes(
    image_size,
    cols,
    rows,
    margin_x=0,
    margin_y=0,
    gutter_x=0,
    gutter_y=0,
    grid_mode="exact",
):
    """Возвращает сетка области.

    Args:
        image_size: Размер изображения в пикселях.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.
        grid_mode: Режим расчета сетки нарезки.

    Returns:
        Найденное или вычисленное значение: сетка области.
    """
    image_width, image_height = image_size
    validate_grid_parameters(
        image_width,
        image_height,
        cols,
        rows,
        margin_x,
        margin_y,
        gutter_x,
        gutter_y,
    )

    if grid_mode == "exact":
        return get_exact_grid_boxes(
            image_width,
            image_height,
            cols,
            rows,
            margin_x,
            margin_y,
            gutter_x,
            gutter_y,
        )

    if grid_mode == "proportional":
        return get_proportional_grid_boxes(
            image_width,
            image_height,
            cols,
            rows,
            margin_x,
            margin_y,
            gutter_x,
            gutter_y,
        )

    raise ValueError(f"Unsupported grid mode: {grid_mode}")


def validate_grid_parameters(
    image_width,
    image_height,
    cols,
    rows,
    margin_x,
    margin_y,
    gutter_x,
    gutter_y,
):
    """Проверяет параметры сетки нарезки изображения.

    Args:
        image_width: Ширина изображения в пикселях.
        image_height: Высота изображения в пикселях.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.

    Returns:
        None.
    """
    if cols <= 0 or rows <= 0:
        raise ValueError("Grid cols and rows must be positive")

    if min(margin_x, margin_y, gutter_x, gutter_y) < 0:
        raise ValueError("Grid margins and gutters must be non-negative")

    usable_width = image_width - margin_x * 2 - gutter_x * (cols - 1)
    usable_height = image_height - margin_y * 2 - gutter_y * (rows - 1)

    if usable_width <= 0 or usable_height <= 0:
        raise ValueError(
            "Grid usable size must be positive: "
            f"image_size={(image_width, image_height)}, "
            f"margins={(margin_x, margin_y)}, "
            f"gutters={(gutter_x, gutter_y)}, "
            f"cols={cols}, rows={rows}, "
            f"usable_size={(usable_width, usable_height)}"
        )


def get_exact_grid_boxes(
    image_width,
    image_height,
    cols,
    rows,
    margin_x,
    margin_y,
    gutter_x,
    gutter_y,
):
    """Возвращает области нарезки для exact grid.

    Args:
        image_width: Ширина изображения в пикселях.
        image_height: Высота изображения в пикселях.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.

    Returns:
        Список областей нарезки `(left, top, right, bottom)`.
    """
    usable_width = image_width - margin_x * 2 - gutter_x * (cols - 1)
    usable_height = image_height - margin_y * 2 - gutter_y * (rows - 1)

    if usable_width % cols != 0 or usable_height % rows != 0:
        raise ValueError(
            "Exact grid does not divide evenly: "
            f"image_size={(image_width, image_height)}, "
            f"margins={(margin_x, margin_y)}, "
            f"gutters={(gutter_x, gutter_y)}, "
            f"cols={cols}, rows={rows}, "
            f"usable_size={(usable_width, usable_height)}"
        )

    cell_width = usable_width // cols
    cell_height = usable_height // rows
    boxes = []

    for row in range(rows):
        for col in range(cols):
            left = margin_x + col * (cell_width + gutter_x)
            top = margin_y + row * (cell_height + gutter_y)
            boxes.append((left, top, left + cell_width, top + cell_height))

    return boxes


def get_proportional_grid_boxes(
    image_width,
    image_height,
    cols,
    rows,
    margin_x,
    margin_y,
    gutter_x,
    gutter_y,
):
    """Возвращает области нарезки для proportional grid.

    Args:
        image_width: Ширина изображения в пикселях.
        image_height: Высота изображения в пикселях.
        cols: Количество колонок в сетке нарезки.
        rows: Количество строк в сетке нарезки.
        margin_x: Горизонтальный отступ сетки от края изображения.
        margin_y: Вертикальный отступ сетки от края изображения.
        gutter_x: Горизонтальный промежуток между ячейками сетки.
        gutter_y: Вертикальный промежуток между ячейками сетки.

    Returns:
        Найденное или вычисленное значение: proportional сетка области.
    """
    usable_width = image_width - margin_x * 2 - gutter_x * (cols - 1)
    usable_height = image_height - margin_y * 2 - gutter_y * (rows - 1)
    boxes = []

    if gutter_x == 0 and gutter_y == 0:
        for row in range(rows):
            for col in range(cols):
                left = round(margin_x + col * usable_width / cols)
                right = round(margin_x + (col + 1) * usable_width / cols)
                top = round(margin_y + row * usable_height / rows)
                bottom = round(margin_y + (row + 1) * usable_height / rows)
                boxes.append((left, top, right, bottom))
    else:
        source_cell_width = usable_width / cols
        source_cell_height = usable_height / rows

        for row in range(rows):
            for col in range(cols):
                left = round(margin_x + col * (source_cell_width + gutter_x))
                top = round(margin_y + row * (source_cell_height + gutter_y))
                right = round(left + source_cell_width)
                bottom = round(top + source_cell_height)
                boxes.append((left, top, right, bottom))

    validate_boxes_inside_image(boxes, image_width, image_height)
    return boxes


def validate_boxes_inside_image(boxes, image_width, image_height):
    """Проверяет, что области нарезки находятся внутри изображения.

    Args:
        boxes: Список прямоугольных областей нарезки изображения.
        image_width: Ширина изображения в пикселях.
        image_height: Высота изображения в пикселях.

    Returns:
        None.
    """
    for box in boxes:
        left, top, right, bottom = box

        if right <= left or bottom <= top:
            raise ValueError(f"Grid box has non-positive size: {box}")

        if left < 0 or top < 0 or right > image_width or bottom > image_height:
            raise ValueError(
                f"Grid box is outside image bounds: box={box}, "
                f"image_size={(image_width, image_height)}"
            )


def remove_background(
    image,
    mode="none",
    background_color=None,
    tolerance=0,
):
    """Удаляет фон.

    Args:
        image: Изображение PIL или поверхность, которую нужно обработать.
        mode: Режим обработки или нарезки.
        background_color: Цвет `фон цвет` в формате PyGame.
        tolerance: Порог прозрачности или цвета при обработке изображения.

    Returns:
        Результат выполнения `remove_background`.
    """
    rgba_image = image.convert("RGBA")

    if mode == "none":
        return rgba_image

    if mode == "top-left":
        background_rgb = rgba_image.getpixel((0, 0))[:3]
    elif mode == "color":
        if background_color is None:
            raise ValueError("background_color is required for color mode")
        if isinstance(background_color, str):
            background_rgb = parse_hex_color(background_color)
        else:
            background_rgb = background_color
    else:
        raise ValueError(f"Unsupported background mode: {mode}")

    result = Image.new("RGBA", rgba_image.size)
    source_pixels = rgba_image.load()
    result_pixels = result.load()

    for y in range(rgba_image.height):
        for x in range(rgba_image.width):
            red, green, blue, alpha = source_pixels[x, y]

            if alpha == 0:
                result_pixels[x, y] = (red, green, blue, 0)
                continue

            if (
                abs(red - background_rgb[0]) <= tolerance
                and abs(green - background_rgb[1]) <= tolerance
                and abs(blue - background_rgb[2]) <= tolerance
            ):
                result_pixels[x, y] = (red, green, blue, 0)
            else:
                result_pixels[x, y] = (red, green, blue, alpha)

    return result
