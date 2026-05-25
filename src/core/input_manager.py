import pygame
import settings


class InputManager:
    """
    Менеджер ввода. По сути самостоятельный слой обработки ввода.
    Системы и компоненты обращаются к нему по постоянным строкам actions.
    """

    def __init__(self) -> None:
        self.down_keys = set()
        self.released_keys = set()
        self.pressed_keys = set()
        self.mouse_position = (0, 0)
        self.mouse_buttons_pressed = set()
        self.bindings = {
            settings.MOVE_UP: (pygame.K_w, pygame.K_UP),
            settings.MOVE_LEFT: (pygame.K_a, pygame.K_LEFT),
            settings.MOVE_DOWN: (pygame.K_s, pygame.K_DOWN),
            settings.MOVE_RIGHT: (pygame.K_d, pygame.K_RIGHT),
            settings.PAUSE: pygame.K_ESCAPE,
            settings.DEBUG: pygame.K_F3,
            settings.ATTACK: pygame.K_SPACE,
            settings.INTERACT: pygame.K_e,
            settings.RESTART: pygame.K_r,
            settings.SELECT: pygame.K_RETURN,
            settings.START_ASSAULT: pygame.K_c,
            settings.OPEN_WORLD_MAP: pygame.K_m,
            settings.TOGGLE_FULLSCREEN: pygame.K_F11,
        }

    def update_events(self, event):
        """Записывает новое положение клавиш в кадре"""
        if event.type == pygame.KEYDOWN:
            self.down_keys.add(event.key)
            self.pressed_keys.add(event.key)
        elif event.type == pygame.KEYUP:
            self.down_keys.discard(event.key)
            self.released_keys.add(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self.mouse_position = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_position = event.pos
            self.mouse_buttons_pressed.add(event.button)

    def clear(self):
        """Очищает данные об однократных нажатиях и отпущенных клавишах за кадр"""
        self.released_keys.clear()
        self.pressed_keys.clear()
        self.mouse_buttons_pressed.clear()

    def was_pressed(self, action):
        """Проверяет была ли один раз нажата клавиша в этом кадре"""
        key = self.bindings.get(action)
        if key is None:
            return False
        if isinstance(key, tuple):
            return any(single_key in self.pressed_keys for single_key in key)
        return key in self.pressed_keys

    def is_pressed(self, action):
        """Проверяет зажата ли клавиша в этом кадре"""
        key = self.bindings.get(action)
        if key is None:
            return False
        if isinstance(key, tuple):
            return any(single_key in self.down_keys for single_key in key)
        return key in self.down_keys

    def was_mouse_pressed(self, button=1):
        return button in self.mouse_buttons_pressed

    def get_velocity_direction(self):
        """Считает направление вектора скорости игрока в этом кадре"""
        direction = pygame.Vector2(0, 0)
        if self.is_pressed(settings.MOVE_UP):
            direction.y -= 1
        if self.is_pressed(settings.MOVE_LEFT):
            direction.x -= 1
        if self.is_pressed(settings.MOVE_DOWN):
            direction.y += 1
        if self.is_pressed(settings.MOVE_RIGHT):
            direction.x += 1

        if direction.length_squared() > 0:
            direction.normalize_ip()

        return direction
