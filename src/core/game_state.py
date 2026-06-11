import json

from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL, RegionState


class GameState:
    """Хранит долгосрочный прогресс мира и выбранный регион.

    """

    def __init__(self, regions, current_region_id=None):
        """Инициализирует `GameState` и сохраняет начальные зависимости.

        Args:
            regions: Список регионов, из которых собирается состояние мира.
            current_region_id: Идентификатор текущего выбранного региона.

        Returns:
            None.
        """
        self.regions = {region.id: region for region in regions}
        self.current_region_id = current_region_id

        if self.current_region_id is None:
            self.current_region_id = self.get_first_unlocked_region_id()

    @classmethod
    def load_from_file(cls, file_path):
        """Загружает состояние игры из JSON-файла.

        Args:
            file_path: Путь к файлу для чтения или записи.

        Returns:
            Загруженное состояние игры.
        """
        with open(file_path, encoding="utf-8") as file:
            regions_data = json.load(file)

        regions = [RegionState.from_dict(region_data) for region_data in regions_data]
        return cls(regions)

    @classmethod
    def from_dict(cls, data):
        """Создает объект из словаря сериализованных данных.

        Args:
            data: Словарь или структура данных из JSON или другого источника.

        Returns:
            Восстановленный объект нужного типа.
        """
        regions = [
            RegionState.from_dict(region_data)
            for region_data in data["regions"]
        ]
        return cls(regions, current_region_id=data.get("current_region_id"))

    def to_dict(self):
        """Преобразует объект в словарь для сериализации.

        Returns:
            Словарь с сериализованным состоянием объекта.
        """
        return {
            "current_region_id": self.current_region_id,
            "regions": [
                region.to_dict()
                for region in self.regions.values()
            ],
        }

    def get_first_unlocked_region_id(self):
        """Возвращает первый открытые регион id.

        Returns:
            Найденное или вычисленное значение: первый открытые регион id.
        """
        for region in self.regions.values():
            if region.unlocked:
                return region.id
        return None

    def get_region(self, region_id):
        """Возвращает регион.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            Найденное или вычисленное значение: регион.
        """
        return self.regions.get(region_id)

    def set_current_region(self, region_id):
        """Назначает текущий регион, если он уже открыт.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        region = self.require_region(region_id)

        if not region.unlocked:
            raise ValueError(f"Регион с id '{region_id}' закрыт")

        self.current_region_id = region_id

    def unlock_region(self, region_id):
        """Открывает регион для выбора на карте мира.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        region = self.require_region(region_id)

        region.unlocked = True
        if region.control_state == LOCKED_CONTROL:
            region.control_state = ENEMY_CONTROL

    def change_influence(self, region_id, delta_player=0, delta_enemy=0):
        """Изменяет влияние игрока и врага в регионе.

        Args:
            region_id: Идентификатор региона на карте мира.
            delta_player: Изменение влияния игрока в регионе.
            delta_enemy: Изменение влияния врага в регионе.

        Returns:
            None.
        """
        region = self.require_region(region_id)

        region.player_influence = self.clamp(region.player_influence + delta_player)
        region.enemy_influence = self.clamp(region.enemy_influence + delta_enemy)

    def mark_assault_unlocked(self, region_id):
        """Помечает штурм региона как доступный.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        region = self.require_region(region_id)
        region.assault_unlocked = True

    def mark_liberated(self, region_id):
        """Помечает регион освобожденным и открывает следующие регионы.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        region = self.require_region(region_id)

        region.liberated = True
        region.unlocked = True
        region.control_state = PLAYER_CONTROL
        region.player_influence = 100
        region.enemy_influence = 0
        region.assault_unlocked = False

        for next_region_id in region.unlocks_on_liberation:
            self.unlock_region(next_region_id)

    def get_unlocked_regions(self):
        """Возвращает открытые регионы.

        Returns:
            Найденное или вычисленное значение: открытые регионы.
        """
        return [region for region in self.regions.values() if region.unlocked]

    def require_region(self, region_id):
        """Возвращает регион или выбрасывает понятную ошибку.

        Args:
            region_id: Идентификатор региона на карте мира.

        Returns:
            Результат выполнения `require_region`.
        """
        region = self.get_region(region_id)
        if region is None:
            raise ValueError(f"Регион с id '{region_id}' не найден")
        return region

    def clamp(self, value, minimum=0, maximum=100):
        """Ограничивает число заданным диапазоном.

        Args:
            value: Значение, которое нужно проверить, ограничить или преобразовать.
            minimum: Минимально допустимое значение.
            maximum: Максимально допустимое значение.

        Returns:
            Результат выполнения `clamp`.
        """
        return max(minimum, min(maximum, value))
