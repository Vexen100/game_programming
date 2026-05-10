from src.scenes.base_scene import BaseScene


class SceneManager:
    """
    Менеджер сцен. Является интерфейсом, через который game.py взаимодействует со сценами, 
    а также  переключает сцены. Каждая сцена сама вызывает менеджера, когда нужно.
    """

    def __init__(self) -> None:
        self.current_scene: BaseScene = None
        self.scenes_ids_register: dict[str, BaseScene] = {}
        self.next_scene_id: str = None

    def registry_scene_ids(self, register):
        self.scenes_ids_register = register
    
    def request_change_scene(self, new_scene_id: str):
        """
        Создаёт запрос на смену сцены. Сама смена сцены происходит в методе change_scene.
        Каждая сцена сама использует этот метод, когда нужно.
        """
        self.next_scene_id = new_scene_id

    def change_scene(self):
         """Меняет сцену на новую, если был запрос в этом кадре. И очищает буфер id следующей сцены"""
         if self.next_scene_id is not None:   
            new_scene = self.scenes_ids_register[self.next_scene_id]
            self.current_scene = new_scene()
            self.current_scene.manager = self
            self.next_scene_id = None

    def handle_events(self, events):
        """Обработка системных событий. Передаётся текущей сцене"""
        self.current_scene.handle_events(events)

    def update(self, dt, input_manager):
        """Обновление положения, анимаций. Передаётся текущей сцене -> объектам"""
        self.current_scene.update(dt, input_manager)

    def draw(self, screen):
        """Отрисовывает изменения на экране. Передаётся сцене -> объектам"""
        self.current_scene.draw(screen)
