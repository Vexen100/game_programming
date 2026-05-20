import settings

from src.components.components import AttackIntent, PlayerControlled


class PlayerAttackInputSystem:
    """Записывает намерение атаки игрока"""

    def update(self, ecm, input_manager):
        attack_requested = input_manager.was_pressed(settings.ATTACK)

        for entity in ecm.get_entities_with(PlayerControlled, AttackIntent):
            attack_intent = ecm.get_component(entity, AttackIntent)
            attack_intent.requested = attack_requested
