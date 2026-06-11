from src.events.game_events import EnemyKilledEvent, OutpostClearedEvent, QuestCompletedEvent


class InfluenceSystem:
    """Инкапсулирует gameplay-логику системы: influence system.

    Attributes:
        ENEMY_KILL_PLAYER_INFLUENCE_GAIN: Значение `враг kill игрок influence gain`, используемое в логике метода.
        ENEMY_KILL_ENEMY_INFLUENCE_LOSS: Значение `враг kill враг influence loss`, используемое в логике метода.
        OUTPOST_CLEAR_PLAYER_INFLUENCE_GAIN: Значение `аванпост clear игрок influence gain`, используемое в логике метода.
        OUTPOST_CLEAR_ENEMY_INFLUENCE_LOSS: Значение `аванпост clear враг influence loss`, используемое в логике метода.
        QUEST_COMPLETE_PLAYER_INFLUENCE_GAIN: Значение `задание complete игрок influence gain`, используемое в логике метода.
        QUEST_COMPLETE_ENEMY_INFLUENCE_LOSS: Значение `задание complete враг influence loss`, используемое в логике метода.
        ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD: Значение `штурм unlock враг influence threshold`, используемое в логике метода.
    """

    ENEMY_KILL_PLAYER_INFLUENCE_GAIN = 5
    ENEMY_KILL_ENEMY_INFLUENCE_LOSS = -5
    OUTPOST_CLEAR_PLAYER_INFLUENCE_GAIN = 20
    OUTPOST_CLEAR_ENEMY_INFLUENCE_LOSS = -20
    QUEST_COMPLETE_PLAYER_INFLUENCE_GAIN = 15
    QUEST_COMPLETE_ENEMY_INFLUENCE_LOSS = -15
    ASSAULT_UNLOCK_ENEMY_INFLUENCE_THRESHOLD = 25

    def __init__(self, game_state):
        """Инициализирует `InfluenceSystem` и сохраняет начальные зависимости.

        Args:
            game_state: Глобальное состояние мира, регионов и прогресса игрока.

        Returns:
            None.
        """
        self.game_state = game_state

    def subscribe(self, event_bus):
        """Подписывает обработчик на события указанного типа.

        Args:
            event_bus: Шина событий для связи систем без прямых зависимостей.

        Returns:
            None.
        """
        event_bus.subscribe(EnemyKilledEvent, self.on_enemy_killed)
        event_bus.subscribe(OutpostClearedEvent, self.on_outpost_cleared)
        event_bus.subscribe(QuestCompletedEvent, self.on_quest_completed)

    def on_enemy_killed(self, event):
        """Обрабатывает событие убийства врага.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        self.apply_influence_change(
            event.region_id,
            self.ENEMY_KILL_PLAYER_INFLUENCE_GAIN,
            self.ENEMY_KILL_ENEMY_INFLUENCE_LOSS,
        )

    def on_outpost_cleared(self, event):
        """Обрабатывает событие зачистки аванпоста.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        self.apply_influence_change(
            event.region_id,
            self.OUTPOST_CLEAR_PLAYER_INFLUENCE_GAIN,
            self.OUTPOST_CLEAR_ENEMY_INFLUENCE_LOSS,
        )

    def on_quest_completed(self, event):
        """Обрабатывает событие завершения задания.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        self.apply_influence_change(
            event.region_id,
            self.QUEST_COMPLETE_PLAYER_INFLUENCE_GAIN,
            self.QUEST_COMPLETE_ENEMY_INFLUENCE_LOSS,
        )

    def apply_influence_change(self, region_id, delta_player, delta_enemy):
        """Применяет influence change.

        Args:
            region_id: Идентификатор региона на карте мира.
            delta_player: Изменение влияния игрока в регионе.
            delta_enemy: Изменение влияния врага в регионе.

        Returns:
            None.
        """
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
