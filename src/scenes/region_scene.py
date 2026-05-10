import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.entities.player import Player


class RegionScene(BaseScene):
    """
    Стандартная сцена региона. Поле, где бегает игрок и происходит сама игра.
    """

    def __init__(self) -> None:
        self.player = Player(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2)
        self.manager = None

    def handle_events(self, events):
        pass

    def update(self, dt, input_manager):
        self.player.update(dt, input_manager)

    def draw(self, screen: pygame.Surface):
        screen.fill(settings.BG_COLOR)
        self.player.draw(screen)
