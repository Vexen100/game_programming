import json
from dataclasses import dataclass
from pathlib import Path

from src.core.game_state import GameState


@dataclass
class SaveData:
    """Хранит восстановленные данные save-файла.

    Attributes:
        game_state: Глобальное состояние мира, регионов и прогресса игрока.
        region_runtime: Значение `регион runtime`, используемое в логике метода.
    """
    game_state: GameState
    region_runtime: dict


class SaveManager:
    """Читает, валидирует и записывает сохранения игры.

    Attributes:
        SAVE_VERSION: Поддерживаемая версия формата save-файла.
    """
    SAVE_VERSION = 1

    def __init__(self, save_file_path):
        """Инициализирует `SaveManager` и сохраняет начальные зависимости.

        Args:
            save_file_path: Значение `сохранение file путь`, используемое в логике метода.

        Returns:
            None.
        """
        self.save_file_path = Path(save_file_path)

    def has_save(self):
        """Проверяет, есть ли сохранение.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.save_file_path.is_file()

    def save(self, game_state, region_runtime=None):
        """Сохраняет текущее состояние во внешний источник.

        Args:
            game_state: Глобальное состояние мира, регионов и прогресса игрока.
            region_runtime: Значение `регион runtime`, используемое в логике метода.

        Returns:
            None.
        """
        self.save_file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": self.SAVE_VERSION,
            "game_state": game_state.to_dict(),
            "region_runtime": region_runtime or {},
        }
        temp_file_path = self.save_file_path.with_suffix(
            self.save_file_path.suffix + ".tmp"
        )

        with open(temp_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        temp_file_path.replace(self.save_file_path)

    def load(self):
        """Загружает данные из внешнего источника.

        Returns:
            Загруженные данные или `None`, если источника нет.
        """
        if not self.has_save():
            return None

        data = self._load_json()
        game_state_data, region_runtime = self._validate_save_data(data)

        try:
            game_state = GameState.from_dict(game_state_data)
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("Save file has invalid game_state schema") from error

        return SaveData(
            game_state=game_state,
            region_runtime=region_runtime,
        )

    def _load_json(self):
        """Читает JSON-файл сохранения и превращает его в Python-данные.

        Returns:
            Данные из JSON-файла.
        """
        try:
            with open(self.save_file_path, encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError("Save file contains invalid JSON") from error

    def _validate_save_data(self, data):
        """Проверяет базовую схему сохранения перед восстановлением состояния.

        Args:
            data: Словарь или структура данных из JSON или другого источника.

        Returns:
            Проверенные данные `game_state` и `region_runtime`.
        """
        if not isinstance(data, dict):
            raise ValueError("Save file root must be an object")

        version = data.get("version")
        if version != self.SAVE_VERSION:
            raise ValueError(f"Unsupported save version: {version}")

        game_state_data = data.get("game_state")
        if not isinstance(game_state_data, dict):
            raise ValueError("Save file game_state must be an object")

        if not isinstance(game_state_data.get("regions"), list):
            raise ValueError("Save file game_state.regions must be a list")

        if "region_runtime" not in data:
            return game_state_data, {}

        region_runtime = data["region_runtime"]
        if not isinstance(region_runtime, dict):
            raise ValueError("Save file region_runtime must be an object")

        return game_state_data, region_runtime

    def delete_save(self):
        """Удаляет файл сохранения или отмечает удаление в тестовом фейке.

        Returns:
            None.
        """
        self.save_file_path.unlink(missing_ok=True)
