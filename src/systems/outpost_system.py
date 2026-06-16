from src.components.components import (
    Dead,
    Enemy,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.entities.entities_settings import OutpostSettings
from src.events.game_events import OutpostClearedEvent
import settings


class OutpostSystem:
    """Инкапсулирует gameplay-логику системы: аванпост system.

    """

    def __init__(self, event_bus=None):
        """Инициализирует `OutpostSystem` и сохраняет начальные зависимости.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        self.event_bus = event_bus

    def update(self, ecm, input_manager=None, region_id=None, dt=0, enemy_spatial_index=None):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.
            region_id: Идентификатор региона на карте мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            None.
        """
        if input_manager is None:
            return

        player_entities = ecm.get_entities_with(PlayerControlled, Position)

        if not player_entities:
            return

        player_id = next(iter(player_entities))

        if ecm.has_component(player_id, PlayerDefeated):
            return

        player_position = ecm.get_component(player_id, Position)

        for outpost_id in ecm.get_entities_with(Outpost, Position, Renderable):
            outpost = ecm.get_component(outpost_id, Outpost)

            if outpost.cleared:
                continue

            outpost_position = ecm.get_component(outpost_id, Position)
            renderable = ecm.get_component(outpost_id, Renderable)

            if self.get_distance(player_position, outpost_position) > outpost.radius:
                outpost.clear_progress = 0
                continue

            if self.has_living_enemy_near_outpost(
                ecm,
                outpost_position,
                outpost.radius,
                enemy_spatial_index,
            ):
                outpost.clear_progress = 0
                continue

            if not self.is_interact_held(input_manager):
                outpost.clear_progress = 0
                continue

            if dt <= 0:
                continue

            outpost.clear_progress = min(
                outpost.clear_duration,
                outpost.clear_progress + dt,
            )

            if outpost.clear_progress < outpost.clear_duration:
                continue

            outpost.cleared = True
            outpost.clear_progress = outpost.clear_duration
            renderable.color = OutpostSettings.CLEARED_COLOR

            if self.event_bus is not None and region_id is not None:
                self.event_bus.publish(OutpostClearedEvent(outpost_id, region_id))

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

    def has_living_enemy_near_outpost(self, ecm, outpost_position, radius, enemy_spatial_index=None):
        """Проверяет выполнение условия: has живой враг near аванпост.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            outpost_position: Позиция `аванпост position` в пикселях.
            radius: Радиус области действия или отрисовки.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        for enemy_id in self.get_enemy_candidates(ecm, outpost_position, radius, enemy_spatial_index):
            if not self.is_living_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, outpost_position) <= radius:
                return True

        return False

    def get_enemy_candidates(self, ecm, outpost_position, radius, enemy_spatial_index):
        """Возвращает враг candidates.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            outpost_position: Позиция `аванпост position` в пикселях.
            radius: Радиус области действия или отрисовки.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            Найденное или вычисленное значение: враг candidates.
        """
        if enemy_spatial_index is None:
            return ecm.get_entities_with(Enemy, Position)

        return enemy_spatial_index.query_rect(
            outpost_position.x - radius,
            outpost_position.y - radius,
            radius * 2,
            radius * 2,
        )

    def is_living_enemy(self, ecm, enemy_id):
        """Проверяет, является ли сущность живым врагом.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return (
            ecm.has_component(enemy_id, Enemy)
            and ecm.has_component(enemy_id, Position)
            and not ecm.has_component(enemy_id, Dead)
        )

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
