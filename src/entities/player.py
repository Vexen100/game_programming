import pygame


class Player:
    def __init__(self, x, y) -> None:
        self.pos = pygame.Vector2(x, y)
        self.speed = 150
        self.radius = 40
        self.color = "blue"

    def update(self, dt, input_manager):
        direction = input_manager.get_velocity_direction()

        self.pos += direction * self.speed * dt

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)
