from src.scenes.base_scene import BaseScene


class SceneManager:
    """
    Менеджер сцен. Является интерфейсом, через который game.py взаимодействует со сценами, 
    а также  переключает сцены. Каждая сцена сама вызывает менеджера, когда нужно.
    """

    def __init__(self) -> None:
        self.current_scene: BaseScene = None

    def change_scene(self, new_scene):
        self.current_scene = new_scene
        self.current_scene.manager = self

    def handle_event(self):
        self.current_scene.handle_event()

    def update(self, dt):
        self.current_scene.update(dt)

    def draw(self, screen):
        self.current_scene.draw(screen)
