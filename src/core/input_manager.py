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
        self.bindings = {
            settings.MOVE_UP: pygame.K_w,
            settings.MOVE_LEFT: pygame.K_a,
            settings.MOVE_DOWN: pygame.K_s,
            settings.MOVE_RIGHT: pygame.K_d,
            settings.PAUSE: pygame.K_ESCAPE,
            settings.DEBUG: pygame.K_F3,
            settings.ATTACK: pygame.K_SPACE,
            settings.RESTART: pygame.K_r,
        }

    def update_events(self, event):
        """Записывает новое положение клавиш в кадре"""
        if event.type == pygame.KEYDOWN:
            self.down_keys.add(event.key)
            self.pressed_keys.add(event.key)
        elif event.type == pygame.KEYUP:
            self.down_keys.discard(event.key)
            self.released_keys.add(event.key)

    def clear(self):
        """Очищает данные об однократных нажатиях и отпущенных клавишах за кадр"""
        self.released_keys.clear()
        self.pressed_keys.clear()

    def was_pressed(self, action):
        """Проверяет была ли один раз нажата клавиша в этом кадре"""
        key = self.bindings.get(action)
        if key is None:
            return False
        return key in self.pressed_keys

    def is_pressed(self, action):
        """Проверяет зажата ли клавиша в этом кадре"""
        key = self.bindings.get(action)
        if key is None:
            return False
        return key in self.down_keys

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
