import pygame


class Player:
    def __init__(self, x, y) -> None:
        self.pos = pygame.Vector2(x, y)
        self.speed = 150
        self.radius = 40
        self.color = "blue"

    def handle_input(self, dt):
        direction = pygame.Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction.normalize_ip()

        self.pos += direction * self.speed * dt

    def update(self, dt):
        self.handle_input(dt)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)
