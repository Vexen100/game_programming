import pygame
import settings
from src.entities.player import Player


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0

        self.player = Player(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            self.dt = self.clock.tick(settings.FPS) / 1000

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        self.player.update(self.dt)

    def draw(self):
        self.screen.fill('red')
        self.player.draw(self.screen)
        pygame.display.flip()
