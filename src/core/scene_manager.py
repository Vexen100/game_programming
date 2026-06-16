from collections.abc import Callable

import settings
from src.scenes.base_scene import BaseScene


class SceneManager:
    """Управляет реестром сцен и безопасно выполняет отложенные переходы.

    """

    def __init__(self) -> None:
        """Инициализирует `SceneManager` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.current_scene: BaseScene | None = None
        self.scene_registry: dict[str, Callable[[], BaseScene]] = {}
        self.next_scene_id: str | None = None
        self.paused_scene: BaseScene | None = None
        self.pause_scene_id: str | None = None
        self.world_map_return_scene: BaseScene | None = None

    def register_scenes(self, scene_registry):
        """Регистрирует доступные сцены в SceneManager.

        Args:
            scene_registry: Значение `сцена реестр`, используемое в логике метода.

        Returns:
            None.
        """
        self.scene_registry = scene_registry

    def request_change(self, new_scene_id: str):
        """Запрашивает переход на другую сцену.

        Args:
            new_scene_id: Идентификатор сцены, на которую запрошен переход.

        Returns:
            None.
        """
        if new_scene_id not in self.scene_registry:
            raise ValueError(f"Сцена с id '{new_scene_id}' не зарегистрирована")

        if new_scene_id != settings.WORLD_MAP_SCENE:
            self.world_map_return_scene = None

        self.next_scene_id = new_scene_id

    def request_pause(self, pause_scene_id):
        """Запрашивает переход в сцену паузы.

        Args:
            pause_scene_id: Идентификатор сцены паузы.

        Returns:
            None.
        """
        if self.current_scene is None:
            return

        if pause_scene_id not in self.scene_registry:
            raise ValueError(f"Сцена с id '{pause_scene_id}' не зарегистрирована")

        if self.paused_scene is not None:
            return

        self.paused_scene = self.current_scene
        self.pause_scene_id = pause_scene_id
        self.next_scene_id = pause_scene_id

    def resume_scene(self):
        """Возобновляет сцену, которая была поставлена на паузу.

        Returns:
            None.
        """
        if self.paused_scene is None:
            return

        self.current_scene = self.paused_scene
        self.current_scene.manager = self
        self.paused_scene = None
        self.pause_scene_id = None
        self.next_scene_id = None

    def open_world_map(self, return_scene=None):
        """Открывает карту мира.

        Args:
            return_scene: Сцена, в которую нужно вернуться после карты мира.

        Returns:
            None.
        """
        if settings.WORLD_MAP_SCENE not in self.scene_registry:
            raise ValueError(f"Сцена с id '{settings.WORLD_MAP_SCENE}' не зарегистрирована")

        self.world_map_return_scene = return_scene
        self.next_scene_id = settings.WORLD_MAP_SCENE

    def open_world_map_from_pause(self):
        """Открывает карту мира из меню паузы.

        Returns:
            None.
        """
        if self.paused_scene is None:
            self.open_world_map()
            return

        return_scene = self.paused_scene
        self.open_world_map(return_scene=return_scene)
        self.paused_scene = None
        self.pause_scene_id = None

    def has_world_map_return_scene(self):
        """Проверяет, сохранена ли сцена возврата с карты мира.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.world_map_return_scene is not None

    def return_from_world_map(self):
        """Возвращает игрока с карты мира в сохраненную сцену.

        Returns:
            None.
        """
        if self.world_map_return_scene is None:
            return

        self.current_scene = self.world_map_return_scene
        self.current_scene.manager = self
        self.world_map_return_scene = None
        self.next_scene_id = None

    def process_scene_change(self):
        """Применяет отложенный переход сцены.

        Returns:
            None.
        """
        if self.next_scene_id is not None:
            scene_factory = self.scene_registry.get(self.next_scene_id)
            if scene_factory is None:
                raise ValueError(f"Сцена с id '{self.next_scene_id}' не зарегистрирована")

            keep_paused_scene = self.next_scene_id == self.pause_scene_id

            self.current_scene = scene_factory()
            self.current_scene.manager = self
            self.next_scene_id = None

            if not keep_paused_scene:
                self.paused_scene = None
                self.pause_scene_id = None

    def handle_events(self, events):
        """Обрабатывает события текущего кадра.

        Args:
            events: Список событий PyGame за текущий кадр.

        Returns:
            None.
        """
        if self.current_scene is None:
            return
        self.current_scene.handle_events(events)

    def update(self, dt, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        if self.current_scene is None:
            return
        self.current_scene.update(dt, input_manager)

    def draw(self, screen):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        if self.current_scene is None:
            return
        self.current_scene.draw(screen)
