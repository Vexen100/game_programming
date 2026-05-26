import pygame

from src.components.components import Health, MeleeAttack


class HUD:
    """Рисует базовую игровую информацию поверх сцены"""

    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 24)
        self.color = (255, 255, 255)

    def draw(self, screen, ecm, player_id, scene_name, contextual_prompts=None):
        health = ecm.get_component(player_id, Health)
        attack = ecm.get_component(player_id, MeleeAttack)

        if health is None:
            hp_text = "HP: -"
        else:
            hp_text = f"HP: {health.current} / {health.maximum}"

        if attack is None or attack.cooldown_timer == 0:
            attack_text = "Attack: READY"
        else:
            attack_text = f"Attack: {attack.cooldown_timer:.1f}s"

        scene_text = f"Scene: {scene_name}"
        hp_surface = self.font.render(hp_text, True, self.color)
        scene_surface = self.font.render(scene_text, True, self.color)
        attack_surface = self.font.render(attack_text, True, self.color)

        screen.blit(hp_surface, (10, 10))
        screen.blit(scene_surface, (10, 32))
        screen.blit(attack_surface, (10, 54))
        self.draw_controls(screen, contextual_prompts or [])

    def draw_controls(self, screen, contextual_prompts):
        controls = [
            "WASD/Arrows: Move",
            "Space: Attack",
            "E: Interact",
            "M: Map",
            "Esc: Pause",
            "F11: Fullscreen",
        ]
        y = screen.get_height() - 24 * (len(controls) + len(contextual_prompts)) - 10

        for text in controls + contextual_prompts:
            surface = self.font.render(text, True, self.color)
            screen.blit(surface, (10, y))
            y += 24

    def draw_defeat_message(self, screen, message="Defeated. Press R to restart."):
        text = message
        surface = self.font.render(text, True, self.color)
        rect = surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(surface, rect)
