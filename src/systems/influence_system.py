from src.events.game_events import EnemyKilledEvent, OutpostClearedEvent


class InfluenceSystem:
    """Меняет влияние региона на основе игровых событий"""

    ENEMY_KILL_PLAYER_INFLUENCE_GAIN = 25
    ENEMY_KILL_ENEMY_INFLUENCE_LOSS = -25
    OUTPOST_CLEAR_PLAYER_INFLUENCE_GAIN = 50
    OUTPOST_CLEAR_ENEMY_INFLUENCE_LOSS = -50
    ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD = 50

    def __init__(self, game_state):
        self.game_state = game_state

    def subscribe(self, event_bus):
        event_bus.subscribe(EnemyKilledEvent, self.on_enemy_killed)
        event_bus.subscribe(OutpostClearedEvent, self.on_outpost_cleared)

    def on_enemy_killed(self, event):
        self.apply_influence_change(
            event.region_id,
            self.ENEMY_KILL_PLAYER_INFLUENCE_GAIN,
            self.ENEMY_KILL_ENEMY_INFLUENCE_LOSS,
        )

    def on_outpost_cleared(self, event):
        self.apply_influence_change(
            event.region_id,
            self.OUTPOST_CLEAR_PLAYER_INFLUENCE_GAIN,
            self.OUTPOST_CLEAR_ENEMY_INFLUENCE_LOSS,
        )

    def apply_influence_change(self, region_id, delta_player, delta_enemy):
        region = self.game_state.get_region(region_id)

        if region is None:
            raise ValueError(f"Регион с id '{region_id}' не найден")

        self.game_state.change_influence(
            region_id,
            delta_player=delta_player,
            delta_enemy=delta_enemy,
        )

        region = self.game_state.get_region(region_id)

        if (
            not region.liberated
            and region.enemy_influence <= self.ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD
        ):
            self.game_state.mark_assault_unlocked(region_id)
