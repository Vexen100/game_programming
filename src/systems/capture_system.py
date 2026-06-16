from src.components.components import (
    CapturePoint,
    Dead,
    Enemy,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
)
from src.entities.entities_settings import CapturePointSettings
from src.events.game_events import CapturePointTakenEvent, RegionLiberatedEvent


class CaptureSystem:
    """Инкапсулирует gameplay-логику системы: точка захвата system.

    """

    def __init__(self, event_bus=None):
        """Инициализирует `CaptureSystem` и сохраняет начальные зависимости.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        self.event_bus = event_bus
        self.region_liberation_published = False

    def reset(self):
        """Сбрасывает внутреннее состояние системы.

        Returns:
            None.
        """
        self.region_liberation_published = False

    def update(self, ecm, dt, region_id=None, enemy_spatial_index=None):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            region_id: Идентификатор региона на карте мира.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

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

        for capture_point_id in ecm.get_entities_with(CapturePoint, Position, Renderable):
            capture_point = ecm.get_component(capture_point_id, CapturePoint)

            if capture_point.captured:
                continue

            capture_point_position = ecm.get_component(capture_point_id, Position)

            if self.get_distance(player_position, capture_point_position) > capture_point.radius:
                continue

            if self.has_living_enemy_near_capture_point(
                ecm,
                capture_point_position,
                capture_point.radius,
                enemy_spatial_index,
            ):
                continue

            self.capture_point(ecm, capture_point_id, capture_point, dt, region_id)

        self.publish_region_liberated_if_ready(ecm, region_id)

    def capture_point(self, ecm, capture_point_id, capture_point, dt, region_id):
        """Обновляет прогресс конкретной точки захвата.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            capture_point_id: Идентификатор сущности точки захвата.
            capture_point: Значение `точка захвата точка`, используемое в логике метода.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        capture_point.progress = min(
            100,
            capture_point.progress + CapturePointSettings.CAPTURE_SPEED * dt,
        )

        if capture_point.progress < 100:
            return

        capture_point.captured = True
        capture_point.owner = "player"

        renderable = ecm.get_component(capture_point_id, Renderable)
        renderable.color = CapturePointSettings.PLAYER_COLOR

        if self.event_bus is not None and region_id is not None:
            self.event_bus.publish(CapturePointTakenEvent(capture_point_id, region_id))

    def publish_region_liberated_if_ready(self, ecm, region_id):
        """Публикует событие освобождения региона при выполнении условий.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            region_id: Идентификатор региона на карте мира.

        Returns:
            None.
        """
        if self.region_liberation_published:
            return

        capture_point_ids = list(ecm.get_entities_with(CapturePoint))

        if not capture_point_ids:
            return

        for capture_point_id in capture_point_ids:
            capture_point = ecm.get_component(capture_point_id, CapturePoint)

            if not capture_point.captured:
                return

        self.region_liberation_published = True

        if self.event_bus is not None and region_id is not None:
            self.event_bus.publish(RegionLiberatedEvent(region_id))

    def has_living_enemy_near_capture_point(
        self,
        ecm,
        capture_point_position,
        radius,
        enemy_spatial_index=None,
    ):
        """Проверяет, есть ли живой враг рядом с точкой захвата.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            capture_point_position: Позиция `точка захвата точка position` в пикселях.
            radius: Радиус области действия или отрисовки.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        for enemy_id in self.get_enemy_candidates(
            ecm,
            capture_point_position,
            radius,
            enemy_spatial_index,
        ):
            if not self.is_living_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, capture_point_position) <= radius:
                return True

        return False

    def get_enemy_candidates(self, ecm, capture_point_position, radius, enemy_spatial_index):
        """Возвращает враг candidates.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            capture_point_position: Позиция `точка захвата точка position` в пикселях.
            radius: Радиус области действия или отрисовки.
            enemy_spatial_index: Пространственный индекс врагов для быстрых проверок рядом.

        Returns:
            Найденное или вычисленное значение: враг candidates.
        """
        if enemy_spatial_index is None:
            return ecm.get_entities_with(Enemy, Position)

        return enemy_spatial_index.query_rect(
            capture_point_position.x - radius,
            capture_point_position.y - radius,
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
