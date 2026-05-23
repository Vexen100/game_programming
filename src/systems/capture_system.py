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
    """Обрабатывает захват точек в замке"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.region_liberation_published = False

    def reset(self):
        self.region_liberation_published = False

    def update(self, ecm, dt, region_id=None):
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
            ):
                continue

            self.capture_point(ecm, capture_point_id, capture_point, dt, region_id)

        self.publish_region_liberated_if_ready(ecm, region_id)

    def capture_point(self, ecm, capture_point_id, capture_point, dt, region_id):
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

    def has_living_enemy_near_capture_point(self, ecm, capture_point_position, radius):
        for enemy_id in ecm.get_entities_with(Enemy, Position):
            if ecm.has_component(enemy_id, Dead):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, capture_point_position) <= radius:
                return True

        return False

    def get_distance(self, first_position, second_position):
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5
