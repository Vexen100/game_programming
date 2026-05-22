from src.events.game_events import EnemyKilledEvent


class InfluenceSystem:
    """Меняет влияние региона на основе игровых событий"""

    ENEMY_KILL_PLAYER_INFLUENCE_GAIN = 25
    ENEMY_KILL_ENEMY_INFLUENCE_LOSS = -25
    ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD = 50

    def __init__(self, game_state):
        self.game_state = game_state

    def subscribe(self, event_bus):
        event_bus.subscribe(EnemyKilledEvent, self.on_enemy_killed)

    def on_enemy_killed(self, event):
        region = self.game_state.get_region(event.region_id)

        if region is None:
            raise ValueError(f"Регион с id '{event.region_id}' не найден")

        self.game_state.change_influence(
            event.region_id,
            delta_player=self.ENEMY_KILL_PLAYER_INFLUENCE_GAIN,
            delta_enemy=self.ENEMY_KILL_ENEMY_INFLUENCE_LOSS,
        )

        region = self.game_state.get_region(event.region_id)

        if (
            not region.liberated
            and region.enemy_influence <= self.ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD
        ):
            self.game_state.mark_assault_unlocked(event.region_id)
