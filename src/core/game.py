import pygame
import settings
from src.core.scene_manager import SceneManager
from src.scenes.region_scene import RegionScene
from src.core.input_manager import InputManager


class Game:
    """Основной игровой цикл"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        self.scene_manager = SceneManager()
        self.scene_manager.change_scene(RegionScene())
        self.input_manager = InputManager()

    def run(self):
        """Запускает игровой цикл"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            # очищаем нажатые один раз и отпущенные клавиши в конце кадра
            self.input_manager.clear()

            self.dt = self.clock.tick(settings.FPS) / 1000

        pygame.quit()

    def handle_events(self):
        """Обрабатывает системные события и передаёт нажатия клавиш менеджеру ввода"""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            self.input_manager.update_events(event)

        self.scene_manager.handle_events(events)

    def update(self):
        """
        Обновление положения, анимаций (просто передаётся: менеджеру сцен -> сцене -> объектам)
        """
        self.scene_manager.update(self.dt, self.input_manager)

    def draw(self):
        self.scene_manager.draw(self.screen)
        pygame.display.flip()
