import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.ui import texts


class MainMenuScene(BaseScene):
    """Минимальное главное меню"""

    BACKGROUND_COLOR = (20, 20, 30)
    TEXT_COLOR = (230, 230, 230)
    SELECTED_COLOR = (220, 190, 40)

    def __init__(self) -> None:
        self.items = [
            (texts.NEW_GAME, "start"),
            (texts.CONTINUE_UNAVAILABLE, "continue"),
            (texts.SETTINGS_UNAVAILABLE, "settings"),
            (texts.EXIT, "exit"),
        ]
        self.selected_index = 0
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 64)
        self.manager = None

    def handle_events(self, events):
        pass

    def update(self, dt, input_manager):
        if input_manager.was_pressed(settings.MOVE_UP):
            self.selected_index = (self.selected_index - 1) % len(self.items)

        if input_manager.was_pressed(settings.MOVE_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.items)

        self.update_mouse_selection(input_manager)

        if input_manager.was_pressed(settings.SELECT):
            self.select_current_item()
            return

        clicked_index = self.get_clicked_item_index(input_manager)

        if clicked_index is not None:
            self.selected_index = clicked_index
            self.select_current_item()

    def update_mouse_selection(self, input_manager):
        mouse_position = getattr(input_manager, "mouse_position", None)
        if mouse_position is None:
            return

        for index in range(len(self.items)):
            if self.get_item_rect(index).collidepoint(mouse_position):
                self.selected_index = index
                return

    def get_clicked_item_index(self, input_manager):
        if not hasattr(input_manager, "was_mouse_pressed"):
            return None

        if not input_manager.was_mouse_pressed(1):
            return None

        mouse_position = getattr(input_manager, "mouse_position", None)

        if mouse_position is None:
            return None

        for index in range(len(self.items)):
            if self.get_item_rect(index).collidepoint(mouse_position):
                return index

        return None

    def get_item_rect(self, index, screen_width=settings.SCREEN_WIDTH):
        return pygame.Rect(
            0,
            0,
            420,
            42,
        ).move(
            screen_width // 2 - 210,
            260 + index * 48 - 21,
        )

    def select_current_item(self):
        label, action = self.items[self.selected_index]

        if action == "start":
            if self.manager is not None:
                self.manager.request_change(settings.WORLD_MAP_SCENE)
            return

        if action == "exit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, screen):
        screen.fill(self.BACKGROUND_COLOR)

        title_surface = self.title_font.render("Crown Reclaim", True, self.TEXT_COLOR)
        title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 140))
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

        hint_surface = self.font.render(texts.SELECT_HINT, True, self.TEXT_COLOR)
        hint_rect = hint_surface.get_rect(center=(screen.get_width() // 2, settings.SCREEN_HEIGHT - 72))
        screen.blit(hint_surface, hint_rect)
