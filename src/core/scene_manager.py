from collections.abc import Callable

from src.scenes.base_scene import BaseScene


class SceneManager:
    """
    Менеджер сцен. Является интерфейсом, через который game.py взаимодействует со сценами, 
    а также  переключает сцены. Каждая сцена сама вызывает менеджера, когда нужно.
    """

    def __init__(self) -> None:
        self.current_scene: BaseScene | None = None
        self.scene_registry: dict[str, Callable[[], BaseScene]] = {}
        self.next_scene_id: str | None = None
        self.paused_scene: BaseScene | None = None
        self.pause_scene_id: str | None = None

    def register_scenes(self, scene_registry):
        self.scene_registry = scene_registry

    def request_change(self, new_scene_id: str):
        """
        Создаёт запрос на смену сцены. Сама смена сцены происходит в методе process_scene_change.
        Каждая сцена сама использует этот метод, когда нужно.
        """
        if new_scene_id not in self.scene_registry:
            raise ValueError(f"Сцена с id '{new_scene_id}' не зарегистрирована")
        self.next_scene_id = new_scene_id

    def request_pause(self, pause_scene_id):
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
        if self.paused_scene is None:
            return

        self.current_scene = self.paused_scene
        self.current_scene.manager = self
        self.paused_scene = None
        self.pause_scene_id = None
        self.next_scene_id = None

    def process_scene_change(self):
        """Меняет сцену на новую, если был запрос в этом кадре. И очищает буфер id следующей сцены"""
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
        """Обработка системных событий. Передаётся текущей сцене"""
        if self.current_scene is None:
            return
        self.current_scene.handle_events(events)

    def update(self, dt, input_manager):
        """Обновление положения, анимаций. Передаётся текущей сцене -> объектам"""
        if self.current_scene is None:
            return
        self.current_scene.update(dt, input_manager)

    def draw(self, screen):
        """Отрисовывает изменения на экране. Передаётся сцене -> объектам"""
        if self.current_scene is None:
            return
        self.current_scene.draw(screen)
