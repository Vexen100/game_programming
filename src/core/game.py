import pygame
import settings
from src.core.scene_manager import SceneManager
from src.scenes.region_scene import RegionScene


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        self.scene_manager = SceneManager()
        self.scene_manager.change_scene(RegionScene())

    def run(self):
        while self.running:
            self.handle_event()
            self.update()
            self.draw()

            self.dt = self.clock.tick(settings.FPS) / 1000

        pygame.quit()

    def handle_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        self.scene_manager.handle_event()

    def update(self):
        self.scene_manager.update(self.dt)

    def draw(self):
        self.scene_manager.draw(self.screen)
        pygame.display.flip()
