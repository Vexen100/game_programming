import pygame

from src.components.components import (
    Animation,
    AttackHitbox,
    Dead,
    Enemy,
    Health,
    HitFlash,
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
        for entity in self.get_render_order(ecm):
            position = ecm.get_component(entity, Position)
            renderable = ecm.get_component(entity, Renderable)
            x, y = position.x, position.y

            if camera is not None:
                x, y = camera.apply(x, y)

            animation = ecm.get_component(entity, Animation)
            surface = self.get_animation_surface(animation, renderable)

            if surface is None:
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

            self.draw_hit_flash(ecm, entity, screen, x, y, renderable)

    def get_render_order(self, ecm):
        """Возвращает порядок отрисовки world entities с Y-sort.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            Список entity id, отсортированный по visual baseline и id.
        """
        entities = []

        for entity in ecm.get_entities_with(Position, Renderable):
            position = ecm.get_component(entity, Position)
            renderable = ecm.get_component(entity, Renderable)
            baseline_y = position.y + renderable.height
            entities.append((baseline_y, entity))

        entities.sort()
        return [entity for _, entity in entities]

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

    def get_animation_surface(self, animation, renderable):
        """Возвращает кадр runtime-анимации сущности.

        Args:
            animation: Компонент runtime-анимации сущности.
            renderable: Компонент отрисовки сущности.

        Returns:
            Surface кадра или `None`, если кадр недоступен.
        """
        if self.resource_manager is None or animation is None:
            return None

        return self.resource_manager.get_animation_frame_surface(
            animation.animation_key,
            animation.state,
            animation.direction,
            animation.frame_index,
            renderable.width,
            renderable.height,
            renderable.color,
        )

    def draw_hit_flash(self, ecm, entity_id, screen, x, y, renderable):
        """Рисует white overlay для активного hit flash.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            entity_id: Идентификатор сущности в EntityComponentManager.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            x: Screen X-координата сущности.
            y: Screen Y-координата сущности.
            renderable: Компонент отрисовки сущности.

        Returns:
            None.
        """
        hit_flash = ecm.get_component(entity_id, HitFlash)

        if hit_flash is None or hit_flash.timer <= 0:
            return

        if hit_flash.duration <= 0:
            alpha = 150
        else:
            alpha = int(150 * min(1, hit_flash.timer / hit_flash.duration))

        overlay = pygame.Surface(
            (renderable.width, renderable.height),
            pygame.SRCALPHA,
        )
        overlay.fill((*hit_flash.color, max(40, alpha)))
        screen.blit(overlay, (x, y))

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
                color = (255, 80, 60) if hitbox.hit_landed else (255, 180, 60)
            else:
                color = (255, 230, 80) if hitbox.hit_landed else (180, 180, 180)

            rect = pygame.Rect(x, y, hitbox.width, hitbox.height)
            width = 3 if ecm.has_component(entity, Enemy) else 2
            pygame.draw.rect(screen, color, rect, width)

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
