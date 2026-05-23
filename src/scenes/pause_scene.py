import pygame
import settings
from src.scenes.base_scene import BaseScene


class PauseScene(BaseScene):
    """Минимальное меню паузы"""

    BACKGROUND_COLOR = (18, 18, 26)
    TEXT_COLOR = (230, 230, 230)
    SELECTED_COLOR = (220, 190, 40)

    def __init__(self) -> None:
        self.items = [
            ("Resume", "resume"),
            ("World Map", "world_map"),
            ("Main Menu", "main_menu"),
        ]
        self.selected_index = 0
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 56)
        self.manager = None

    def handle_events(self, events):
        pass

    def update(self, dt, input_manager):
        if input_manager.was_pressed(settings.MOVE_UP):
            self.selected_index = (self.selected_index - 1) % len(self.items)

        if input_manager.was_pressed(settings.MOVE_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.items)

        if input_manager.was_pressed(settings.PAUSE):
            self.resume()
            return

        if input_manager.was_pressed(settings.SELECT):
            self.select_current_item()

    def select_current_item(self):
        label, action = self.items[self.selected_index]

        if action == "resume":
            self.resume()
            return

        if self.manager is None:
            return

        if action == "world_map":
            self.manager.request_change(settings.WORLD_MAP_SCENE)
        elif action == "main_menu":
            self.manager.request_change(settings.MAIN_MENU_SCENE)

    def resume(self):
        if self.manager is not None:
            self.manager.resume_scene()

    def draw(self, screen):
        screen.fill(self.BACKGROUND_COLOR)

        title_surface = self.title_font.render("Paused", True, self.TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 150))
        screen.blit(title_surface, title_rect)

        start_y = 260
        for index, item in enumerate(self.items):
            label, action = item
            is_selected = index == self.selected_index
            color = self.SELECTED_COLOR if is_selected else self.TEXT_COLOR
            prefix = "> " if is_selected else "  "
            item_surface = self.font.render(prefix + label, True, color)
            item_rect = item_surface.get_rect(center=(screen.get_width() // 2, start_y + index * 48))
            screen.blit(item_surface, item_rect)
