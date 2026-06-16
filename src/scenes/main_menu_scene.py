import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.ui import texts


class MainMenuScene(BaseScene):
    """Показывает главное меню и запускает новый или сохраненный прогресс.

    Attributes:
        BACKGROUND_COLOR: Цвет `фон цвет` в формате PyGame.
        TEXT_COLOR: Цвет `текст цвет` в формате PyGame.
        SELECTED_COLOR: Цвет `выбранный цвет` в формате PyGame.
    """

    BACKGROUND_COLOR = (20, 20, 30)
    TEXT_COLOR = (230, 230, 230)
    SELECTED_COLOR = (220, 190, 40)

    def __init__(self, on_new_game=None, on_continue=None, has_save=False) -> None:
        """Инициализирует `MainMenuScene` и сохраняет начальные зависимости.

        Args:
            on_new_game: Значение `on новый игра`, используемое в логике метода.
            on_continue: Значение `on continue`, используемое в логике метода.
            has_save: Значение `has сохранение`, используемое в логике метода.

        Returns:
            None.
        """
        self.on_new_game = on_new_game
        self.on_continue = on_continue
        self.has_save = has_save
        continue_label = texts.CONTINUE if self.has_save else texts.CONTINUE_UNAVAILABLE
        self.items = [
            (texts.NEW_GAME, "start"),
            (continue_label, "continue"),
            (texts.SETTINGS_UNAVAILABLE, "settings"),
            (texts.EXIT, "exit"),
        ]
        self.selected_index = 0
        self.confirm_new_game_delete = False
        self.confirm_selected_index = 0
        self.confirm_items = [
            (texts.NEW_GAME_CONFIRM_YES, "yes"),
            (texts.NEW_GAME_CONFIRM_NO, "no"),
        ]
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 64)
        self.manager = None

    def handle_events(self, events):
        """Обрабатывает события текущего кадра.

        Args:
            events: Список событий PyGame за текущий кадр.

        Returns:
            None.
        """
        pass

    def update(self, dt, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        if self.confirm_new_game_delete:
            self.update_confirmation(input_manager)
            return

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

    def update_confirmation(self, input_manager):
        """Обновляет подтверждение.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        if input_manager.was_pressed(settings.MOVE_UP):
            self.confirm_selected_index = (
                self.confirm_selected_index - 1
            ) % len(self.confirm_items)

        if input_manager.was_pressed(settings.MOVE_DOWN):
            self.confirm_selected_index = (
                self.confirm_selected_index + 1
            ) % len(self.confirm_items)

        if input_manager.was_pressed(settings.PAUSE):
            self.cancel_new_game_confirmation()
            return

        self.update_confirmation_mouse_selection(input_manager)

        if input_manager.was_pressed(settings.SELECT):
            self.select_confirmation_item()
            return

        clicked_index = self.get_clicked_confirmation_item_index(input_manager)

        if clicked_index is not None:
            self.confirm_selected_index = clicked_index
            self.select_confirmation_item()

    def update_mouse_selection(self, input_manager):
        """Обновляет мышь selection.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        mouse_position = getattr(input_manager, "mouse_position", None)
        if mouse_position is None:
            return

        for index in range(len(self.items)):
            if self.get_item_rect(index).collidepoint(mouse_position):
                self.selected_index = index
                return

    def get_clicked_item_index(self, input_manager):
        """Возвращает clicked пункт индекс.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            Найденное или вычисленное значение: clicked пункт индекс.
        """
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

    def update_confirmation_mouse_selection(self, input_manager):
        """Обновляет подтверждение мышь selection.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        mouse_position = getattr(input_manager, "mouse_position", None)
        if mouse_position is None:
            return

        for index in range(len(self.confirm_items)):
            if self.get_confirmation_item_rect(index).collidepoint(mouse_position):
                self.confirm_selected_index = index
                return

    def get_clicked_confirmation_item_index(self, input_manager):
        """Возвращает clicked подтверждение пункт индекс.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            Найденное или вычисленное значение: clicked подтверждение пункт индекс.
        """
        if not hasattr(input_manager, "was_mouse_pressed"):
            return None

        if not input_manager.was_mouse_pressed(1):
            return None

        mouse_position = getattr(input_manager, "mouse_position", None)

        if mouse_position is None:
            return None

        for index in range(len(self.confirm_items)):
            if self.get_confirmation_item_rect(index).collidepoint(mouse_position):
                return index

        return None

    def get_item_rect(self, index, screen_width=settings.SCREEN_WIDTH):
        """Возвращает пункт прямоугольник.

        Args:
            index: Индекс элемента в списке меню или коллекции.
            screen_width: Ширина окна или экрана в пикселях.

        Returns:
            Найденное или вычисленное значение: пункт прямоугольник.
        """
        return pygame.Rect(
            0,
            0,
            420,
            42,
        ).move(
            screen_width // 2 - 210,
            260 + index * 48 - 21,
        )

    def get_confirmation_item_rect(self, index, screen_width=settings.SCREEN_WIDTH):
        """Возвращает подтверждение пункт прямоугольник.

        Args:
            index: Индекс элемента в списке меню или коллекции.
            screen_width: Ширина окна или экрана в пикселях.

        Returns:
            Найденное или вычисленное значение: подтверждение пункт прямоугольник.
        """
        return pygame.Rect(
            0,
            0,
            460,
            42,
        ).move(
            screen_width // 2 - 230,
            340 + index * 52 - 21,
        )

    def select_current_item(self):
        """Активирует текущий выбранный пункт меню.

        Returns:
            None.
        """
        label, action = self.items[self.selected_index]

        if action == "start":
            if self.has_save:
                self.confirm_new_game_delete = True
                self.confirm_selected_index = 0
            else:
                self.start_new_game()
            return

        if action == "continue":
            if self.has_save and self.on_continue is not None:
                self.on_continue()
            return

        if action == "exit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def select_confirmation_item(self):
        """Активирует пункт меню подтверждения.

        Returns:
            None.
        """
        label, action = self.confirm_items[self.confirm_selected_index]

        if action == "yes":
            self.confirm_new_game_delete = False
            self.start_new_game()
            return

        self.cancel_new_game_confirmation()

    def cancel_new_game_confirmation(self):
        """Отменяет подтверждение новой игры.

        Returns:
            None.
        """
        self.confirm_new_game_delete = False
        self.confirm_selected_index = 0

    def start_new_game(self):
        """Сбрасывает прогресс и начинает новую игру.

        Returns:
            None.
        """
        if self.on_new_game is not None:
            self.on_new_game()
        elif self.manager is not None:
            self.manager.request_change(settings.WORLD_MAP_SCENE)

    def draw(self, screen):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        screen.fill(self.BACKGROUND_COLOR)

        if self.confirm_new_game_delete:
            self.draw_confirmation(screen)
            return

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

    def draw_confirmation(self, screen):
        """Рисует подтверждение.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        title_surface = self.title_font.render(
            texts.NEW_GAME_CONFIRM_TITLE,
            True,
            self.TEXT_COLOR,
        )
        title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 180))
        screen.blit(title_surface, title_rect)

        warning_surface = self.font.render(
            texts.NEW_GAME_CONFIRM_WARNING,
            True,
            self.TEXT_COLOR,
        )
        warning_rect = warning_surface.get_rect(center=(screen.get_width() // 2, 260))
        screen.blit(warning_surface, warning_rect)

        for index, item in enumerate(self.confirm_items):
            label, action = item
            is_selected = index == self.confirm_selected_index
            color = self.SELECTED_COLOR if is_selected else self.TEXT_COLOR
            prefix = "> " if is_selected else "  "
            item_surface = self.font.render(prefix + label, True, color)
            item_rect = item_surface.get_rect(
                center=(screen.get_width() // 2, 340 + index * 52)
            )
            screen.blit(item_surface, item_rect)

        hint_surface = self.font.render(texts.SELECT_HINT, True, self.TEXT_COLOR)
        hint_rect = hint_surface.get_rect(center=(screen.get_width() // 2, settings.SCREEN_HEIGHT - 72))
        screen.blit(hint_surface, hint_rect)
