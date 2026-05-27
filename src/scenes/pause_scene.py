import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.ui import texts


class PauseScene(BaseScene):
    """Минимальное меню паузы"""

    BACKGROUND_COLOR = (18, 18, 26)
    TEXT_COLOR = (230, 230, 230)
    SELECTED_COLOR = (220, 190, 40)

    def __init__(self) -> None:
        self.items = [
            (texts.RESUME, "resume"),
            (texts.WORLD_MAP, "world_map"),
            (texts.MAIN_MENU, "main_menu"),
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
            360,
            42,
        ).move(
            screen_width // 2 - 180,
            260 + index * 48 - 21,
        )

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

        title_surface = self.title_font.render(texts.PAUSED, True, self.TEXT_COLOR)
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

        hint_surface = self.font.render(texts.SELECT_HINT, True, self.TEXT_COLOR)
        hint_rect = hint_surface.get_rect(center=(screen.get_width() // 2, settings.SCREEN_HEIGHT - 72))
        screen.blit(hint_surface, hint_rect)
