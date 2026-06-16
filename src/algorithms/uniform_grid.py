import math

from src.algorithms.spatial_index import SpatialIndex


class UniformGrid(SpatialIndex):
    """Хранит spatial grid для быстрых запросов объектов по области.

    """
    def __init__(self, width, height, cell_size):
        """Инициализирует `UniformGrid` и сохраняет начальные зависимости.

        Args:
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.
            cell_size: Размер одной ячейки spatial grid в пикселях.

        Returns:
            None.
        """
        if width <= 0:
            raise ValueError("width must be greater than 0")
        if height <= 0:
            raise ValueError("height must be greater than 0")
        if cell_size <= 0:
            raise ValueError("cell_size must be greater than 0")

        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.columns = math.ceil(width / cell_size)
        self.rows = math.ceil(height / cell_size)
        self.objects = {}
        self.cells = self.create_cells()

    def create_cells(self):
        """Создает пустую таблицу ячеек spatial grid.

        Returns:
            Двумерный список пустых множеств ячеек.
        """
        return [
            [set() for _ in range(self.columns)]
            for _ in range(self.rows)
        ]

    def clear(self):
        """Очищает накопленное состояние объекта.

        Returns:
            None.
        """
        self.objects.clear()
        self.cells = self.create_cells()

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
        if width <= 0 or height <= 0:
            return

        self.objects[entity_id] = (x, y, width, height)
        cell_range = self.get_cell_range(x, y, width, height)

        if cell_range is None:
            return

        start_column, end_column, start_row, end_row = cell_range

        for row in range(start_row, end_row + 1):
            for column in range(start_column, end_column + 1):
                self.cells[row][column].add(entity_id)

    def query_rect(self, x, y, width, height):
        """Ищет объекты spatial grid в прямоугольной области.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            Результат выполнения `query_rect`.
        """
        cell_range = self.get_cell_range(x, y, width, height)

        if cell_range is None:
            return set()

        start_column, end_column, start_row, end_row = cell_range
        entity_ids = set()

        for row in range(start_row, end_row + 1):
            for column in range(start_column, end_column + 1):
                entity_ids.update(self.cells[row][column])

        return entity_ids

    def query_radius(self, x, y, radius):
        """Ищет объекты spatial grid в радиусе.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            radius: Радиус области действия или отрисовки.

        Returns:
            Результат выполнения `query_radius`.
        """
        if radius < 0:
            return set()

        candidates = self.query_rect(
            x - radius,
            y - radius,
            radius * 2,
            radius * 2,
        )
        result = set()

        for entity_id in candidates:
            object_rect = self.objects.get(entity_id)

            if object_rect is None:
                continue

            object_x, object_y, object_width, object_height = object_rect
            object_center_x = object_x + object_width / 2
            object_center_y = object_y + object_height / 2
            dx = object_center_x - x
            dy = object_center_y - y

            if (dx ** 2 + dy ** 2) ** 0.5 <= radius:
                result.add(entity_id)

        return result

    def get_cell_range(self, x, y, width, height):
        """Возвращает ячейка range.

        Args:
            x: Координата по оси X в пикселях или тайлах, в зависимости от контекста.
            y: Координата по оси Y в пикселях или тайлах, в зависимости от контекста.
            width: Ширина области, карты или изображения.
            height: Высота области, карты или изображения.

        Returns:
            Найденное или вычисленное значение: ячейка range.
        """
        if width <= 0 or height <= 0:
            return None

        min_x = max(0, x)
        min_y = max(0, y)
        max_x = min(self.width, x + width)
        max_y = min(self.height, y + height)

        if max_x <= min_x or max_y <= min_y:
            return None

        start_column = self.clamp_cell_index(min_x // self.cell_size, self.columns)
        start_row = self.clamp_cell_index(min_y // self.cell_size, self.rows)
        end_column = self.clamp_cell_index((max_x - 0.000001) // self.cell_size, self.columns)
        end_row = self.clamp_cell_index((max_y - 0.000001) // self.cell_size, self.rows)

        return start_column, end_column, start_row, end_row

    def clamp_cell_index(self, value, maximum):
        """Ограничивает индекс ячейки границами spatial grid.

        Args:
            value: Значение, которое нужно проверить, ограничить или преобразовать.
            maximum: Максимально допустимое значение.

        Returns:
            Результат выполнения `clamp_cell_index`.
        """
        return max(0, min(maximum - 1, int(value)))
