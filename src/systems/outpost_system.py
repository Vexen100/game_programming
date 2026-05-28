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
    """Проверяет зачистку аванпостов"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus

    def update(self, ecm, input_manager=None, region_id=None, dt=0, enemy_spatial_index=None):
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
        if not hasattr(input_manager, "is_pressed"):
            return False

        return input_manager.is_pressed(settings.INTERACT)

    def has_living_enemy_near_outpost(self, ecm, outpost_position, radius, enemy_spatial_index=None):
        for enemy_id in self.get_enemy_candidates(ecm, outpost_position, radius, enemy_spatial_index):
            if not self.is_living_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, outpost_position) <= radius:
                return True

        return False

    def get_enemy_candidates(self, ecm, outpost_position, radius, enemy_spatial_index):
        if enemy_spatial_index is None:
            return ecm.get_entities_with(Enemy, Position)

        return enemy_spatial_index.query_rect(
            outpost_position.x - radius,
            outpost_position.y - radius,
            radius * 2,
            radius * 2,
        )

    def is_living_enemy(self, ecm, enemy_id):
        return (
            ecm.has_component(enemy_id, Enemy)
            and ecm.has_component(enemy_id, Position)
            and not ecm.has_component(enemy_id, Dead)
        )

    def get_distance(self, first_position, second_position):
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5
