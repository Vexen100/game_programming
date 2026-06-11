import pygame

from src.components.components import Health, MeleeAttack
from src.ui import texts


class HUD:
    """Рисует игровые подсказки, статус и служебные сообщения.

    """

    def __init__(self) -> None:
        """Инициализирует `HUD` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.font = pygame.font.Font(None, 24)
        self.color = (255, 255, 255)

    def draw(self, screen, ecm, player_id, scene_name, contextual_prompts=None, status_lines=None):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            ecm: Менеджер сущностей и компонентов игрового мира.
            player_id: Идентификатор сущности игрока.
            scene_name: Название сцены, отображаемое в HUD.
            contextual_prompts: Список подсказок, актуальных рядом с игроком.
            status_lines: Список строк статуса для HUD.

        Returns:
            None.
        """
        health = ecm.get_component(player_id, Health)
        attack = ecm.get_component(player_id, MeleeAttack)

        if health is None:
            hp_text = f"{texts.HP_LABEL}: -"
        else:
            hp_text = f"{texts.HP_LABEL}: {health.current} / {health.maximum}"

        if attack is None or attack.cooldown_timer == 0:
            attack_text = texts.ATTACK_READY
        else:
            attack_text = texts.ATTACK_COOLDOWN.format(seconds=attack.cooldown_timer)

        scene_text = f"{texts.SCENE_LABEL}: {scene_name}"
        lines = [
            hp_text,
            scene_text,
            attack_text,
            *(status_lines or []),
        ]

        y = 10
        for text in lines:
            surface = self.font.render(text, True, self.color)
            screen.blit(surface, (10, y))
            y += 22

        self.draw_controls(screen, contextual_prompts or [])

    def draw_controls(self, screen, contextual_prompts):
        """Рисует подсказки управления.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            contextual_prompts: Список подсказок, актуальных рядом с игроком.

        Returns:
            None.
        """
        controls = [
            texts.MOVE_HINT,
            texts.ATTACK_HINT,
            texts.INTERACT_HINT,
            texts.MAP_HINT,
            texts.PAUSE_HINT,
            texts.FULLSCREEN_HINT,
        ]
        y = screen.get_height() - 24 * (len(controls) + len(contextual_prompts)) - 10

        for text in controls + contextual_prompts:
            surface = self.font.render(text, True, self.color)
            screen.blit(surface, (10, y))
            y += 24

    def draw_defeat_message(self, screen, message=texts.DEFEATED_RESTART):
        """Рисует поражение message.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.
            message: Текст сообщения для HUD или диагностики.

        Returns:
            None.
        """
        text = message
        surface = self.font.render(text, True, self.color)
        rect = surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(surface, rect)
