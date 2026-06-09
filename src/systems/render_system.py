import pygame

from src.components.components import (
    AttackHitbox,
    Dead,
    Enemy,
    Health,
    Position,
    Renderable,
    Sprite,
)


class RenderSystem:
    """Инкапсулирует gameplay-логику системы: render system.

    """

    def __init__(self, resource_manager=None):
        """Инициализирует `RenderSystem` и сохраняет начальные зависимости.

        Args:
            resource_manager: Менеджер графических ресурсов и placeholder-изображений.

        Returns:
            None.
        """
        self.resource_manager = resource_manager

    def draw(self, ecm, screen, camera=None):
        """Рисует объект на переданной поверхности.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
        for entity in ecm.get_entities_with(Position, Renderable):
            position = ecm.get_component(entity, Position)
            renderable = ecm.get_component(entity, Renderable)
            x, y = position.x, position.y

            if camera is not None:
                x, y = camera.apply(x, y)

            sprite = ecm.get_component(entity, Sprite)
            surface = self.get_entity_surface(sprite, renderable)

            if surface is not None:
                screen.blit(surface, (x, y))
            else:
                rect = pygame.Rect(
                    x,
                    y,
                    renderable.width,
                    renderable.height,
                )
                pygame.draw.rect(screen, renderable.color, rect)

    def get_entity_surface(self, sprite, renderable):
        """Возвращает сущность поверхность.

        Args:
            sprite: Значение `sprite`, используемое в логике метода.
            renderable: Значение `renderable`, используемое в логике метода.

        Returns:
            Найденное или вычисленное значение: сущность поверхность.
        """
        if self.resource_manager is None or sprite is None:
            return None

        return self.resource_manager.get_entity_surface(
            sprite.asset_key,
            renderable.width,
            renderable.height,
            renderable.color,
        )

    def draw_attack_hitboxes(self, ecm, screen, camera=None):
        """Рисует атака hitboxes.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
        for entity in ecm.get_entities_with(AttackHitbox):
            if ecm.has_component(entity, Dead):
                continue

            hitbox = ecm.get_component(entity, AttackHitbox)

            if not hitbox.active:
                continue

            x, y = hitbox.x, hitbox.y

            if camera is not None:
                x, y = camera.apply(x, y)

            if ecm.has_component(entity, Enemy):
                color = (255, 90, 70) if hitbox.hit_landed else (255, 150, 80)
            else:
                color = (255, 230, 80) if hitbox.hit_landed else (180, 180, 180)

            rect = pygame.Rect(x, y, hitbox.width, hitbox.height)
            pygame.draw.rect(screen, color, rect, 2)

    def draw_enemy_health_bars(self, ecm, screen, camera=None):
        """Рисует враг health bars.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
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
