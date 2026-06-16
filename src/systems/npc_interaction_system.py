import settings
from src.components.components import (
    NPC,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.entities.entities_settings import NPCSettings
from src.events.game_events import QuestCompletedEvent


class NPCInteractionSystem:
    """Инкапсулирует gameplay-логику системы: NPC interaction system.

    """

    def __init__(self, event_bus=None):
        """Инициализирует `NPCInteractionSystem` и сохраняет начальные зависимости.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        self.event_bus = event_bus

    def update(self, ecm, input_manager, region_id=None, dt=0):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.
            region_id: Идентификатор региона на карте мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        player_entities = ecm.get_entities_with(PlayerControlled, Position)

        if not player_entities:
            return

        player_id = next(iter(player_entities))

        if ecm.has_component(player_id, PlayerDefeated):
            return

        player_position = ecm.get_component(player_id, Position)

        for npc_id in ecm.get_entities_with(NPC, Position, Renderable):
            npc = ecm.get_component(npc_id, NPC)

            if npc.quest_completed:
                continue

            npc_position = ecm.get_component(npc_id, Position)

            if self.get_distance(player_position, npc_position) > npc.interaction_radius:
                npc.report_progress = 0
                continue

            if not self.is_required_outpost_cleared(ecm, npc.required_outpost_id):
                npc.report_progress = 0
                continue

            if not self.is_interact_held(input_manager):
                npc.report_progress = 0
                continue

            if dt <= 0:
                continue

            npc.report_progress = min(
                npc.report_duration,
                npc.report_progress + dt,
            )

            if npc.report_progress < npc.report_duration:
                continue

            npc.quest_completed = True
            npc.report_progress = npc.report_duration
            renderable = ecm.get_component(npc_id, Renderable)
            renderable.color = NPCSettings.COMPLETED_COLOR

            if self.event_bus is not None and region_id is not None:
                self.event_bus.publish(
                    QuestCompletedEvent(
                        quest_id=npc.quest_id,
                        npc_id=npc_id,
                        region_id=region_id,
                    )
                )

    def is_interact_held(self, input_manager):
        """Проверяет, удерживается ли действие взаимодействия.

        Args:
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if not hasattr(input_manager, "is_pressed"):
            return False

        return input_manager.is_pressed(settings.INTERACT)

    def is_required_outpost_cleared(self, ecm, outpost_id):
        """Проверяет, зачищен ли обязательный аванпост.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            outpost_id: Идентификатор сущности аванпоста.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if outpost_id is None:
            return True

        outpost = ecm.get_component(outpost_id, Outpost)

        if outpost is None:
            return False

        return outpost.cleared

    def get_distance(self, first_position, second_position):
        """Возвращает дистанция.

        Args:
            first_position: Позиция первого объекта в пикселях.
            second_position: Позиция второго объекта в пикселях.

        Returns:
            Расстояние между двумя позициями.
        """
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5
