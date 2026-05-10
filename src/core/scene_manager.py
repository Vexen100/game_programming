from src.scenes.base_scene import BaseScene


class SceneManager:
    """
    Менеджер сцен. Является интерфейсом, через который game.py взаимодействует со сценами, 
    а также  переключает сцены. Каждая сцена сама вызывает менеджера, когда нужно.
    """

    def __init__(self) -> None:
        self.current_scene: BaseScene = None

    def change_scene(self, new_scene):
        """Сменить текущую сцену. Каждая сцена сама использует этот метод, когда нужно"""
        self.current_scene = new_scene
        self.current_scene.manager = self

    def handle_events(self, events):
        """Обработка системных событий. Передаётся текущей сцене"""
        self.current_scene.handle_events(events)

    def update(self, dt, input_manager):
        """Обновление положения, анимаций. Передаётся текущей сцене -> объектам"""
        self.current_scene.update(dt, input_manager)

    def draw(self, screen):
        """Отрисовывает изменения на экране. Передаётся сцене -> объектам"""
        self.current_scene.draw(screen)
