import pygame
from player import Player

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Crown Reclaim")
clock = pygame.time.Clock()
running = True
dt = 0
player = Player(screen.get_width() / 2, screen.get_height() / 2, 200)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("red")

    player.draw(screen)

    player.handle_input(dt)

    pygame.display.flip()

    dt = clock.tick(60)/1000

pygame.quit()
