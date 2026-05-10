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
        }

    def update_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.down_keys.add(event.key)
            self.pressed_keys.add(event.key)
        elif event.type == pygame.KEYUP:
            self.down_keys.discard(event.key)
            self.released_keys.add(event.key)

    def clear(self):
        self.released_keys.clear()
        self.pressed_keys.clear()

    def was_pressed(self, action):
        if self.bindings[action] in self.pressed_keys:
            return True

    def is_pressed(self, action):
        if self.bindings[action] in self.down_keys:
            return True

    def get_velocity_direction(self):
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
