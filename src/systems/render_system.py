import pygame

from src.components.components import Position, Renderable


class RenderSystem:
    """Рисует сущности с компонентами Position и Renderable"""

    def draw(self, ecm, screen):
        for entity in ecm.get_entities_with(Position, Renderable):
            position = ecm.get_component(entity, Position)
            renderable = ecm.get_component(entity, Renderable)
            rect = pygame.Rect(
                position.x,
                position.y,
                renderable.width,
                renderable.height,
            )
            pygame.draw.rect(screen, renderable.color, rect)
