import pygame

from src.components.components import DamagePopup, HitFlash, Position, TemporaryVisualEffect


class VisualEffectSystem:
    """Обновляет и рисует runtime-only визуальные эффекты боя.

    """

    def __init__(self, font_size=18):
        """Инициализирует систему визуальных эффектов.

        Args:
            font_size: Размер шрифта для всплывающего текста урона.

        Returns:
            None.
        """
        self.font_size = font_size
        self.font = None

    def update(self, ecm, dt):
        """Обновляет таймеры временных визуальных эффектов.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        self.update_hit_flashes(ecm, dt)
        self.update_damage_popups(ecm, dt)
        self.update_temporary_effects(ecm, dt)

    def update_hit_flashes(self, ecm, dt):
        """Обновляет и удаляет завершенные flash-компоненты.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        for entity_id in list(ecm.get_entities_with(HitFlash)):
            hit_flash = ecm.get_component(entity_id, HitFlash)
            hit_flash.timer = max(0, hit_flash.timer - dt)

            if hit_flash.timer == 0:
                ecm.remove_component(entity_id, HitFlash)

    def update_damage_popups(self, ecm, dt):
        """Обновляет и удаляет завершенные damage popup entities.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        for entity_id in list(ecm.get_entities_with(DamagePopup)):
            popup = ecm.get_component(entity_id, DamagePopup)
            popup.timer = max(0, popup.timer - dt)

            if popup.timer == 0:
                ecm.destroy_entity(entity_id)

    def update_temporary_effects(self, ecm, dt):
        """Обновляет и удаляет завершенные temporary visual effects.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        for entity_id in list(ecm.get_entities_with(TemporaryVisualEffect)):
            effect = ecm.get_component(entity_id, TemporaryVisualEffect)
            effect.timer = max(0, effect.timer - dt)

            if effect.timer == 0:
                ecm.destroy_entity(entity_id)

    def draw(self, ecm, screen, camera=None):
        """Рисует временные визуальные эффекты поверх мира.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
        self.draw_temporary_effects(ecm, screen, camera)
        self.draw_damage_popups(ecm, screen, camera)

    def spawn_damage_popup(self, ecm, x, y, amount):
        """Создает runtime entity всплывающего текста урона.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            x: World X-координата центра popup.
            y: World Y-координата старта popup.
            amount: Количество нанесенного урона.

        Returns:
            Идентификатор созданной popup-сущности.
        """
        duration = 0.45
        entity_id = ecm.create_entity(tag="damage_popup")
        ecm.add_component(entity_id, Position(x, y))
        ecm.add_component(
            entity_id,
            DamagePopup(
                text=str(amount),
                timer=duration,
                duration=duration,
                start_y=y,
            ),
        )
        return entity_id

    def spawn_slash_effect(self, ecm, attack_rect, direction):
        """Создает короткий runtime slash effect около hitbox атаки.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            attack_rect: Словарь с координатами и размером attack hitbox.
            direction: Направление удара игрока.

        Returns:
            Идентификатор созданной effect-сущности.
        """
        duration = 0.13
        center_x = attack_rect["x"] + attack_rect["width"] / 2
        center_y = attack_rect["y"] + attack_rect["height"] / 2
        entity_id = ecm.create_entity(tag="slash_effect")
        ecm.add_component(entity_id, Position(center_x, center_y))
        ecm.add_component(
            entity_id,
            TemporaryVisualEffect(
                effect_type="slash",
                timer=duration,
                duration=duration,
                direction=direction,
            ),
        )
        return entity_id

    def get_font(self):
        """Возвращает cached font для damage popups.

        Returns:
            Шрифт PyGame для отрисовки текста.
        """
        if self.font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            self.font = pygame.font.Font(None, self.font_size)
        return self.font

    def draw_damage_popups(self, ecm, screen, camera=None):
        """Рисует всплывающие числа урона.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
        font = self.get_font()

        for entity_id in ecm.get_entities_with(Position, DamagePopup):
            position = ecm.get_component(entity_id, Position)
            popup = ecm.get_component(entity_id, DamagePopup)
            progress = self.get_progress(popup.timer, popup.duration)
            x = position.x
            y = popup.start_y - popup.rise_distance * progress

            if camera is not None:
                x, y = camera.apply(x, y)

            text_surface = font.render(popup.text, True, popup.color)
            if popup.duration <= 0:
                visible_ratio = 1
            else:
                visible_ratio = popup.timer / popup.duration
            alpha = int(255 * max(0.2, visible_ratio))
            text_surface.set_alpha(alpha)
            screen.blit(
                text_surface,
                (
                    x - text_surface.get_width() / 2,
                    y - text_surface.get_height() / 2,
                ),
            )

    def draw_temporary_effects(self, ecm, screen, camera=None):
        """Рисует slash и другие короткие эффекты.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            camera: Камера, задающая смещение видимой области карты.

        Returns:
            None.
        """
        for entity_id in ecm.get_entities_with(Position, TemporaryVisualEffect):
            position = ecm.get_component(entity_id, Position)
            effect = ecm.get_component(entity_id, TemporaryVisualEffect)

            if effect.effect_type != "slash":
                continue

            x, y = position.x, position.y

            if camera is not None:
                x, y = camera.apply(x, y)

            self.draw_slash(screen, x, y, effect)

    def draw_slash(self, screen, x, y, effect):
        """Рисует простой направленный slash effect.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            x: Screen X-координата центра эффекта.
            y: Screen Y-координата центра эффекта.
            effect: Компонент временного визуального эффекта.

        Returns:
            None.
        """
        progress = self.get_progress(effect.timer, effect.duration)
        length = 22 + int(8 * progress)
        color = effect.color

        if effect.direction == "left":
            points = [(x + 8, y - 12), (x - length, y), (x + 8, y + 12)]
        elif effect.direction == "up":
            points = [(x - 12, y + 8), (x, y - length), (x + 12, y + 8)]
        elif effect.direction == "down":
            points = [(x - 12, y - 8), (x, y + length), (x + 12, y - 8)]
        else:
            points = [(x - 8, y - 12), (x + length, y), (x - 8, y + 12)]

        pygame.draw.lines(screen, color, False, points, 3)
        pygame.draw.lines(screen, (255, 255, 255), False, points, 1)

    def get_progress(self, timer, duration):
        """Возвращает прогресс эффекта от `0` до `1`.

        Args:
            timer: Оставшееся время жизни эффекта.
            duration: Полная длительность эффекта.

        Returns:
            Нормализованный прогресс эффекта.
        """
        if duration <= 0:
            return 1

        return max(0, min(1, 1 - timer / duration))
