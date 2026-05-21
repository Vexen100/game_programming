import pygame

from src.components.components import Health


class HUD:
    """Рисует базовую игровую информацию поверх сцены"""

    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 24)
        self.color = (255, 255, 255)

    def draw(self, screen, ecm, player_id, scene_name):
        health = ecm.get_component(player_id, Health)

        if health is None:
            hp_text = "HP: -"
        else:
            hp_text = f"HP: {health.current} / {health.maximum}"

        scene_text = f"Scene: {scene_name}"
        hp_surface = self.font.render(hp_text, True, self.color)
        scene_surface = self.font.render(scene_text, True, self.color)

        screen.blit(hp_surface, (10, 10))
        screen.blit(scene_surface, (10, 32))

    def draw_defeat_message(self, screen):
        text = "Defeated. Press R to restart."
        surface = self.font.render(text, True, self.color)
        rect = surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(surface, rect)
