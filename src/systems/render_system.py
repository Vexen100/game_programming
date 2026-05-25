import pygame

from src.components.components import AttackHitbox, Dead, Enemy, Health, Position, Renderable


class RenderSystem:
    """Рисует сущности с компонентами Position и Renderable"""

    def draw(self, ecm, screen, camera=None):
        for entity in ecm.get_entities_with(Position, Renderable):
            position = ecm.get_component(entity, Position)
            renderable = ecm.get_component(entity, Renderable)
            x, y = position.x, position.y

            if camera is not None:
                x, y = camera.apply(x, y)

            rect = pygame.Rect(
                x,
                y,
                renderable.width,
                renderable.height,
            )
            pygame.draw.rect(screen, renderable.color, rect)

    def draw_attack_hitboxes(self, ecm, screen, camera=None):
        for entity in ecm.get_entities_with(AttackHitbox):
            hitbox = ecm.get_component(entity, AttackHitbox)

            if not hitbox.active:
                continue

            x, y = hitbox.x, hitbox.y

            if camera is not None:
                x, y = camera.apply(x, y)

            color = (255, 230, 80) if hitbox.hit_landed else (180, 180, 180)
            rect = pygame.Rect(x, y, hitbox.width, hitbox.height)
            pygame.draw.rect(screen, color, rect, 2)

    def draw_enemy_health_bars(self, ecm, screen, camera=None):
        for enemy_id in ecm.get_entities_with(Enemy, Position, Renderable, Health):
            if ecm.has_component(enemy_id, Dead):
                continue

            position = ecm.get_component(enemy_id, Position)
            renderable = ecm.get_component(enemy_id, Renderable)
            health = ecm.get_component(enemy_id, Health)

            if health.maximum <= 0:
                continue

            x, y = position.x, position.y - 8

            if camera is not None:
                x, y = camera.apply(x, y)

            width = renderable.width
            ratio = max(0, min(1, health.current / health.maximum))
            background_rect = pygame.Rect(x, y, width, 4)
            health_rect = pygame.Rect(x, y, width * ratio, 4)
            pygame.draw.rect(screen, (40, 40, 40), background_rect)
            pygame.draw.rect(screen, (40, 220, 80), health_rect)
