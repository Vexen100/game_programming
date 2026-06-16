class Camera:
    """Следит за целью и ограничивает видимую область границами карты.

    """
    def __init__(self, viewport_width, viewport_height):
        """Инициализирует `Camera` и сохраняет начальные зависимости.

        Args:
            viewport_width: Ширина видимой области камеры.
            viewport_height: Высота видимой области камеры.

        Returns:
            None.
        """
        self.x = 0
        self.y = 0
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

    def follow(self, target_x, target_y, map_width_pixels, map_height_pixels):
        """Смещает камеру к целевой точке с учетом границ карты.

        Args:
            target_x: Значение `target x`, используемое в логике метода.
            target_y: Значение `target y`, используемое в логике метода.
            map_width_pixels: Ширина карты в пикселях.
            map_height_pixels: Высота карты в пикселях.

        Returns:
            None.
        """
        if map_width_pixels <= self.viewport_width:
            self.x = 0
        else:
            self.x = target_x - self.viewport_width / 2
            self.x = max(0, min(self.x, map_width_pixels - self.viewport_width))

        if map_height_pixels <= self.viewport_height:
            self.y = 0
        else:
            self.y = target_y - self.viewport_height / 2
            self.y = max(0, min(self.y, map_height_pixels - self.viewport_height))

    def apply(self, x, y):
        """Применяет смещение камеры к координатам.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.

        Returns:
            Результат выполнения `apply`.
        """
        return x - self.x, y - self.y
