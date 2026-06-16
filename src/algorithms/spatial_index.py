class SpatialIndex:
    """Задает общий интерфейс пространственного индекса.

    """
    def clear(self):
        """Очищает накопленное состояние объекта.

        Returns:
            None.
        """
        raise NotImplementedError

    def insert(self, entity_id, x, y, width=1, height=1):
        """Добавляет объект в пространственный индекс.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            None.
        """
        raise NotImplementedError

    def query_rect(self, x, y, width, height):
        """Ищет объекты spatial grid в прямоугольной области.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            None.
        """
        raise NotImplementedError

    def query_radius(self, x, y, radius):
        """Ищет объекты spatial grid в радиусе.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            radius: Радиус области действия или отрисовки.

        Returns:
            None.
        """
        raise NotImplementedError
