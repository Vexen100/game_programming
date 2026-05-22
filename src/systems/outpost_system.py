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


class OutpostSystem:
    """Проверяет зачистку аванпостов"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus

    def update(self, ecm, region_id=None):
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
                continue

            if self.has_living_enemy_near_outpost(ecm, outpost_position, outpost.radius):
                continue

            outpost.cleared = True
            renderable.color = OutpostSettings.CLEARED_COLOR

            if self.event_bus is not None and region_id is not None:
                self.event_bus.publish(OutpostClearedEvent(outpost_id, region_id))

    def has_living_enemy_near_outpost(self, ecm, outpost_position, radius):
        for enemy_id in ecm.get_entities_with(Enemy, Position):
            if ecm.has_component(enemy_id, Dead):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, outpost_position) <= radius:
                return True

        return False

    def get_distance(self, first_position, second_position):
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5
