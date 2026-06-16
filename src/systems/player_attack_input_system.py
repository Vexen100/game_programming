import settings

from src.components.components import AttackIntent, PlayerControlled


class PlayerAttackInputSystem:
    """Инкапсулирует gameplay-логику системы: игрок атака ввод system.

    """

    def update(self, ecm, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        attack_requested = input_manager.was_pressed(settings.ATTACK)

        for entity in ecm.get_entities_with(PlayerControlled, AttackIntent):
            attack_intent = ecm.get_component(entity, AttackIntent)
            attack_intent.requested = attack_requested
