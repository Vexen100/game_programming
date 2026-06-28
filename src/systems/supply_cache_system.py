import settings
from src.components.components import (
    Dead,
    Enemy,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
    SupplyCache,
)
from src.entities.entities_settings import SupplyCacheSettings
from src.events.game_events import SupplyCacheDestroyedEvent


class SupplyCacheSystem:
    """Обрабатывает уничтожение складов снабжения через hold-interaction.

    """

    ENEMY_BLOCK_RADIUS = settings.TILE_SIZE * 5

    def __init__(self, event_bus=None):
        """Инициализирует `SupplyCacheSystem` и сохраняет зависимости.

        Args:
            event_bus: Шина событий для публикации прогресса мира.

        Returns:
            None.
        """
        self.event_bus = event_bus

    def update(self, ecm, input_manager, region_id, dt, spatial_index=None):
        """Обновляет прогресс уничтожения ближайшего склада.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            input_manager: Менеджер ввода, который хранит состояние action-клавиш.
            region_id: Идентификатор текущего региона.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            spatial_index: Пространственный индекс живых врагов для broadphase-проверки.

        Returns:
            None.
        """
        if input_manager is None:
            return

        player_id = self.get_player_id(ecm)

        if player_id is None or ecm.has_component(player_id, PlayerDefeated):
            return

        cache_id = self.get_nearest_relevant_cache(ecm, player_id)
        self.reset_other_cache_progress(ecm, cache_id)

        if cache_id is None:
            return

        cache = ecm.get_component(cache_id, SupplyCache)
        cache_position = ecm.get_component(cache_id, Position)
        player_position = ecm.get_component(player_id, Position)

        if (
            cache is None
            or cache_position is None
            or player_position is None
            or cache.destroyed
        ):
            return

        if not self.is_player_near_cache(player_position, cache_position, cache):
            cache.destroy_progress = 0
            return

        if self.has_living_enemy_near_cache(ecm, cache_position, cache, spatial_index):
            cache.destroy_progress = 0
            return

        if not self.is_interact_held(input_manager):
            cache.destroy_progress = 0
            return

        if dt <= 0:
            return

        cache.destroy_progress = min(
            cache.destroy_duration,
            cache.destroy_progress + dt,
        )

        if cache.destroy_progress < cache.destroy_duration:
            return

        self.destroy_cache(ecm, cache_id, cache, region_id)

    def get_player_id(self, ecm):
        """Возвращает ECS id игрока, если он есть.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            Идентификатор игрока или `None`.
        """
        player_entities = ecm.get_entities_with(PlayerControlled, Position)

        if not player_entities:
            return None

        return next(iter(player_entities))

    def get_nearest_relevant_cache(self, ecm, player_id):
        """Находит ближайший неуничтоженный склад в радиусе interaction.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            player_id: Идентификатор сущности игрока.

        Returns:
            Идентификатор ближайшего склада или `None`.
        """
        player_position = ecm.get_component(player_id, Position)

        if player_position is None:
            return None

        nearest_cache_id = None
        nearest_distance = None

        for cache_id in ecm.get_entities_with(SupplyCache, Position):
            cache = ecm.get_component(cache_id, SupplyCache)
            cache_position = ecm.get_component(cache_id, Position)

            if cache is None or cache_position is None or cache.destroyed:
                continue

            distance = self.get_distance(player_position, cache_position)

            if distance > cache.interaction_radius:
                continue

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_cache_id = cache_id

        return nearest_cache_id

    def reset_other_cache_progress(self, ecm, active_cache_id):
        """Сбрасывает progress у всех складов, кроме активного.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            active_cache_id: Склад, с которым игрок взаимодействует сейчас.

        Returns:
            None.
        """
        for cache_id in ecm.get_entities_with(SupplyCache):
            if cache_id == active_cache_id:
                continue

            cache = ecm.get_component(cache_id, SupplyCache)
            if cache is not None and not cache.destroyed:
                cache.destroy_progress = 0

    def is_player_near_cache(self, player_position, cache_position, cache):
        """Проверяет, находится ли игрок рядом со складом.

        Args:
            player_position: Позиция игрока в пикселях.
            cache_position: Позиция склада в пикселях.
            cache: Компонент склада снабжения.

        Returns:
            `True`, если игрок находится в радиусе interaction.
        """
        return self.get_distance(player_position, cache_position) <= cache.interaction_radius

    def has_living_enemy_near_cache(self, ecm, cache_position, cache, spatial_index=None):
        """Проверяет, есть ли живой враг рядом со складом.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            cache_position: Позиция склада в пикселях.
            cache: Компонент склада снабжения.
            spatial_index: Пространственный индекс врагов для broadphase-проверки.

        Returns:
            `True`, если рядом есть живой враг.
        """
        radius = self.get_enemy_block_radius(cache)

        for enemy_id in self.get_enemy_candidates(ecm, cache_position, radius, spatial_index):
            if not self.is_living_enemy(ecm, enemy_id):
                continue

            enemy_position = ecm.get_component(enemy_id, Position)

            if self.get_distance(enemy_position, cache_position) <= radius:
                return True

        return False

    def get_enemy_block_radius(self, cache):
        """Возвращает радиус, в котором враги блокируют уничтожение склада.

        Args:
            cache: Компонент склада снабжения.

        Returns:
            Радиус проверки врагов в пикселях.
        """
        return max(cache.interaction_radius, self.ENEMY_BLOCK_RADIUS)

    def get_enemy_candidates(self, ecm, cache_position, radius, spatial_index):
        """Возвращает кандидатов-врагов для точной проверки дистанции.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            cache_position: Позиция склада в пикселях.
            radius: Радиус проверки врагов.
            spatial_index: Пространственный индекс врагов для broadphase-проверки.

        Returns:
            Набор или список id сущностей-кандидатов.
        """
        if spatial_index is None:
            return ecm.get_entities_with(Enemy, Position)

        if hasattr(spatial_index, "query_radius"):
            return spatial_index.query_radius(cache_position.x, cache_position.y, radius)

        return spatial_index.query_rect(
            cache_position.x - radius,
            cache_position.y - radius,
            radius * 2,
            radius * 2,
        )

    def is_living_enemy(self, ecm, enemy_id):
        """Проверяет, является ли сущность живым врагом.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            enemy_id: Идентификатор сущности врага.

        Returns:
            `True`, если враг жив и имеет позицию.
        """
        return (
            ecm.has_component(enemy_id, Enemy)
            and ecm.has_component(enemy_id, Position)
            and not ecm.has_component(enemy_id, Dead)
        )

    def is_interact_held(self, input_manager):
        """Проверяет, удерживается ли action взаимодействия.

        Args:
            input_manager: Менеджер ввода или тестовый fake input.

        Returns:
            `True`, если interaction удерживается.
        """
        if not hasattr(input_manager, "is_pressed"):
            return False

        return input_manager.is_pressed(settings.INTERACT)

    def destroy_cache(self, ecm, cache_id, cache, region_id):
        """Помечает склад уничтоженным и публикует событие прогресса.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            cache_id: Идентификатор склада.
            cache: Компонент склада снабжения.
            region_id: Идентификатор текущего региона.

        Returns:
            None.
        """
        if cache.destroyed:
            return

        cache.destroyed = True
        cache.destroy_progress = cache.destroy_duration

        renderable = ecm.get_component(cache_id, Renderable)
        if renderable is not None:
            renderable.color = SupplyCacheSettings.DESTROYED_COLOR

        if self.event_bus is not None and region_id is not None:
            self.event_bus.publish(
                SupplyCacheDestroyedEvent(
                    region_id=region_id,
                    supply_cache_key=cache.key,
                )
            )

    def get_distance(self, first_position, second_position):
        """Возвращает расстояние между двумя позициями.

        Args:
            first_position: Позиция первого объекта в пикселях.
            second_position: Позиция второго объекта в пикселях.

        Returns:
            Евклидово расстояние между позициями.
        """
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5
