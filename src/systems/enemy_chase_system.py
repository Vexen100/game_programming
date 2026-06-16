import pygame

from src.algorithms.line_of_sight import has_line_of_sight
from src.algorithms.pathfinding import find_path
from src.components.components import (
    ChaseBehavior,
    Collider,
    Enemy,
    PatrolRoute,
    PlayerControlled,
    Position,
    Velocity,
)


class EnemyChaseSystem:
    """Инкапсулирует gameplay-логику системы: враг chase system.

    """

    def __init__(self, path_rebuild_interval=0.25, last_seen_memory_duration=1.0):
        """Инициализирует `EnemyChaseSystem` и сохраняет начальные зависимости.

        Args:
            path_rebuild_interval: Значение `путь rebuild interval`, используемое в логике метода.
            last_seen_memory_duration: Значение `last seen память duration`, используемое в логике метода.

        Returns:
            None.
        """
        self.path_rebuild_interval = path_rebuild_interval
        self.last_seen_memory_duration = last_seen_memory_duration
        self.cached_paths = {}
        self.cached_goal_tiles = {}
        self.path_rebuild_timers = {}
        self.last_seen_player_tiles = {}
        self.last_seen_timers = {}

    def update(self, ecm, tile_map=None, dt=0):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            None.
        """
        player_entities = ecm.get_entities_with(PlayerControlled, Position)
        enemy_ids = ecm.get_entities_with(Enemy, Position, Velocity, ChaseBehavior)
        self.remove_stale_path_cache(enemy_ids)

        if not player_entities:
            self.clear_path_cache()
            self.clear_ai_memory()
            self.stop_enemies(ecm)
            return

        player_id = next(iter(player_entities))
        player_position = ecm.get_component(player_id, Position)
        player_collider = ecm.get_component(player_id, Collider)

        for enemy_id in enemy_ids:
            enemy_position = ecm.get_component(enemy_id, Position)
            enemy_velocity = ecm.get_component(enemy_id, Velocity)
            enemy_collider = ecm.get_component(enemy_id, Collider)
            chase = ecm.get_component(enemy_id, ChaseBehavior)
            patrol_route = ecm.get_component(enemy_id, PatrolRoute)

            distance = self.get_distance(enemy_position, player_position)

            if tile_map is None:
                if distance == 0 or distance > chase.detection_radius:
                    self.stop_enemy(enemy_velocity)
                    continue

                self.move_towards_position(
                    enemy_velocity,
                    enemy_position,
                    player_position.x,
                    player_position.y,
                    chase.speed,
                )
                continue

            self.update_enemy_with_pathfinding(
                enemy_id,
                enemy_velocity,
                enemy_position,
                enemy_collider,
                player_position,
                player_collider,
                chase,
                patrol_route,
                tile_map,
                dt,
                distance,
            )

    def update_enemy_with_pathfinding(
        self,
        enemy_id,
        enemy_velocity,
        enemy_position,
        enemy_collider,
        player_position,
        player_collider,
        chase,
        patrol_route,
        tile_map,
        dt,
        distance,
    ):
        """Обновляет враг with pathfinding.

        Args:
            enemy_id: Идентификатор сущности врага.
            enemy_velocity: Компонент скорости врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            player_position: Позиция игрока в пикселях.
            player_collider: Коллайдер игрока.
            chase: Значение `chase`, используемое в логике метода.
            patrol_route: Компонент или список точек маршрута патруля.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            distance: Расстояние между объектами или тайлами.

        Returns:
            None.
        """
        enemy_tile = self.get_entity_tile(tile_map, enemy_position, enemy_collider)
        player_tile = self.get_entity_tile(tile_map, player_position, player_collider)
        can_see_player = (
            distance <= chase.detection_radius
            and has_line_of_sight(tile_map, enemy_tile, player_tile)
        )

        if can_see_player:
            self.last_seen_player_tiles[enemy_id] = player_tile
            self.last_seen_timers[enemy_id] = self.last_seen_memory_duration
            target_tile = player_tile
        else:
            target_tile = self.get_active_last_seen_tile(enemy_id, dt)

        if target_tile is None:
            self.clear_enemy_ai_memory(enemy_id)
            self.update_patrol_or_stop(
                enemy_id,
                enemy_velocity,
                enemy_position,
                enemy_collider,
                enemy_tile,
                patrol_route,
                chase.speed,
                tile_map,
                dt,
            )
            return

        if enemy_tile == target_tile:
            if can_see_player:
                self.move_towards_position(
                    enemy_velocity,
                    enemy_position,
                    player_position.x,
                    player_position.y,
                    chase.speed,
                )
                return

            self.clear_enemy_ai_memory(enemy_id)
            self.clear_enemy_path_cache(enemy_id)
            self.stop_enemy(enemy_velocity)
            return

        moved = self.move_to_target_tile(
            enemy_id,
            enemy_velocity,
            enemy_position,
            enemy_collider,
            enemy_tile,
            target_tile,
            chase.speed,
            tile_map,
            dt,
        )

        if moved:
            return

        if not can_see_player:
            self.clear_enemy_ai_memory(enemy_id)
            self.clear_enemy_path_cache(enemy_id)
            self.update_patrol_or_stop(
                enemy_id,
                enemy_velocity,
                enemy_position,
                enemy_collider,
                enemy_tile,
                patrol_route,
                chase.speed,
                tile_map,
                dt,
            )

    def update_patrol_or_stop(
        self,
        enemy_id,
        enemy_velocity,
        enemy_position,
        enemy_collider,
        enemy_tile,
        patrol_route,
        speed,
        tile_map,
        dt,
    ):
        """Обновляет патруль or stop.

        Args:
            enemy_id: Идентификатор сущности врага.
            enemy_velocity: Компонент скорости врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            enemy_tile: Координаты тайла, на котором находится враг.
            patrol_route: Компонент или список точек маршрута патруля.
            speed: Скорость движения сущности.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Результат выполнения `update_patrol_or_stop`.
        """
        if patrol_route is not None:
            return self.update_enemy_patrol(
                enemy_id,
                enemy_velocity,
                enemy_position,
                enemy_collider,
                enemy_tile,
                patrol_route,
                speed,
                tile_map,
                dt,
            )

        self.clear_enemy_path_cache(enemy_id)
        self.stop_enemy(enemy_velocity)
        return False

    def update_enemy_patrol(
        self,
        enemy_id,
        enemy_velocity,
        enemy_position,
        enemy_collider,
        enemy_tile,
        patrol_route,
        speed,
        tile_map,
        dt,
    ):
        """Обновляет враг патруль.

        Args:
            enemy_id: Идентификатор сущности врага.
            enemy_velocity: Компонент скорости врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            enemy_tile: Координаты тайла, на котором находится враг.
            patrol_route: Компонент или список точек маршрута патруля.
            speed: Скорость движения сущности.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Результат выполнения `update_enemy_patrol`.
        """
        if len(patrol_route.patrol_tiles) < 2:
            self.clear_enemy_path_cache(enemy_id)
            self.stop_enemy(enemy_velocity)
            return False

        for _ in range(len(patrol_route.patrol_tiles)):
            target_tile = patrol_route.patrol_tiles[patrol_route.current_index]

            if enemy_tile == target_tile:
                if patrol_route.wait_duration > 0:
                    if patrol_route.wait_timer <= 0:
                        patrol_route.wait_timer = patrol_route.wait_duration

                    patrol_route.wait_timer = max(0, patrol_route.wait_timer - dt)

                    if patrol_route.wait_timer > 0:
                        self.stop_enemy(enemy_velocity)
                        return True

                patrol_route.current_index = (
                    patrol_route.current_index + 1
                ) % len(patrol_route.patrol_tiles)
                target_tile = patrol_route.patrol_tiles[patrol_route.current_index]

            moved = self.move_to_target_tile(
                enemy_id,
                enemy_velocity,
                enemy_position,
                enemy_collider,
                enemy_tile,
                target_tile,
                speed,
                tile_map,
                dt,
            )

            if moved:
                return True

            self.clear_enemy_path_cache(enemy_id)
            patrol_route.wait_timer = 0
            patrol_route.current_index = (
                patrol_route.current_index + 1
            ) % len(patrol_route.patrol_tiles)

        self.stop_enemy(enemy_velocity)
        return False

    def move_to_target_tile(
        self,
        enemy_id,
        enemy_velocity,
        enemy_position,
        enemy_collider,
        enemy_tile,
        target_tile,
        speed,
        tile_map,
        dt,
    ):
        """Двигает врага к целевому тайлу.

        Args:
            enemy_id: Идентификатор сущности врага.
            enemy_velocity: Компонент скорости врага.
            enemy_position: Позиция врага в пикселях.
            enemy_collider: Коллайдер врага.
            enemy_tile: Координаты тайла, на котором находится враг.
            target_tile: Координаты тайла, к которому нужно двигаться.
            speed: Скорость движения сущности.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Результат выполнения `move_to_target_tile`.
        """
        self.path_rebuild_timers[enemy_id] = self.path_rebuild_timers.get(enemy_id, 0) - dt
        path = self.get_cached_or_rebuilt_path(
            enemy_id,
            tile_map,
            enemy_tile,
            target_tile,
        )

        if not path:
            self.clear_enemy_path_cache(enemy_id)
            self.stop_enemy(enemy_velocity)
            return False

        if len(path) < 2:
            self.clear_enemy_path_cache(enemy_id)
            self.stop_enemy(enemy_velocity)
            return False

        next_tile = self.get_next_tile_from_path(path, enemy_tile)

        if next_tile is None:
            self.clear_enemy_path_cache(enemy_id)
            path = self.get_cached_or_rebuilt_path(
                enemy_id,
                tile_map,
                enemy_tile,
                target_tile,
            )

            if not path:
                self.clear_enemy_path_cache(enemy_id)
                self.stop_enemy(enemy_velocity)
                return False

            if len(path) < 2:
                self.clear_enemy_path_cache(enemy_id)
                self.stop_enemy(enemy_velocity)
                return False

            next_tile = path[1]

        target_x, target_y = self.get_tile_target_position(tile_map, next_tile, enemy_collider)
        self.move_towards_position(
            enemy_velocity,
            enemy_position,
            target_x,
            target_y,
            speed,
        )
        return True

    def get_active_last_seen_tile(self, enemy_id, dt):
        """Возвращает активное last seen тайл.

        Args:
            enemy_id: Идентификатор сущности врага.
            dt: Время, прошедшее с предыдущего кадра, в секундах.

        Returns:
            Найденное или вычисленное значение: активное last seen тайл.
        """
        last_seen_tile = self.last_seen_player_tiles.get(enemy_id)
        timer = self.last_seen_timers.get(enemy_id, 0)

        if last_seen_tile is None or timer <= 0:
            return None

        timer -= dt

        if timer <= 0:
            return None

        self.last_seen_timers[enemy_id] = timer
        return last_seen_tile

    def clear_enemy_path_cache(self, enemy_id):
        """Очищает враг путь кэш.

        Args:
            enemy_id: Идентификатор сущности врага.

        Returns:
            None.
        """
        self.cached_paths.pop(enemy_id, None)
        self.cached_goal_tiles.pop(enemy_id, None)
        self.path_rebuild_timers.pop(enemy_id, None)

    def clear_ai_memory(self):
        """Очищает AI память.

        Returns:
            None.
        """
        self.last_seen_player_tiles.clear()
        self.last_seen_timers.clear()

    def clear_enemy_ai_memory(self, enemy_id):
        """Очищает враг AI память.

        Args:
            enemy_id: Идентификатор сущности врага.

        Returns:
            None.
        """
        self.last_seen_player_tiles.pop(enemy_id, None)
        self.last_seen_timers.pop(enemy_id, None)

    def clear_path_cache(self):
        """Очищает путь кэш.

        Returns:
            None.
        """
        self.cached_paths.clear()
        self.cached_goal_tiles.clear()
        self.path_rebuild_timers.clear()

    def remove_stale_path_cache(self, active_enemy_ids):
        """Удаляет устаревший путь кэш.

        Args:
            active_enemy_ids: Множество или список врагов, существующих в сцене.

        Returns:
            None.
        """
        active_enemy_ids = set(active_enemy_ids)
        remembered_enemy_ids = (
            set(self.cached_paths)
            | set(self.cached_goal_tiles)
            | set(self.path_rebuild_timers)
            | set(self.last_seen_player_tiles)
            | set(self.last_seen_timers)
        )

        for enemy_id in remembered_enemy_ids:
            if enemy_id not in active_enemy_ids:
                self.clear_enemy_path_cache(enemy_id)
                self.clear_enemy_ai_memory(enemy_id)

    def should_rebuild_path(self, enemy_id, goal_tile):
        """Проверяет, нужно ли пересобрать A* путь.

        Args:
            enemy_id: Идентификатор сущности врага.
            goal_tile: Координаты целевого тайла для поиска пути.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if enemy_id not in self.cached_paths:
            return True

        if self.cached_goal_tiles.get(enemy_id) != goal_tile:
            return True

        return self.path_rebuild_timers.get(enemy_id, 0) <= 0

    def rebuild_path(self, enemy_id, tile_map, enemy_tile, goal_tile):
        """Пересобирает A* путь для врага.

        Args:
            enemy_id: Идентификатор сущности врага.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            enemy_tile: Координаты тайла, на котором находится враг.
            goal_tile: Координаты целевого тайла для поиска пути.

        Returns:
            Результат выполнения `rebuild_path`.
        """
        path = find_path(tile_map, enemy_tile, goal_tile)
        self.cached_paths[enemy_id] = path
        self.cached_goal_tiles[enemy_id] = goal_tile
        self.path_rebuild_timers[enemy_id] = self.path_rebuild_interval
        return path

    def get_cached_or_rebuilt_path(self, enemy_id, tile_map, enemy_tile, goal_tile):
        """Возвращает cached or rebuilt путь.

        Args:
            enemy_id: Идентификатор сущности врага.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            enemy_tile: Координаты тайла, на котором находится враг.
            goal_tile: Координаты целевого тайла для поиска пути.

        Returns:
            Найденное или вычисленное значение: cached or rebuilt путь.
        """
        path = self.cached_paths.get(enemy_id)

        if self.should_rebuild_path(enemy_id, goal_tile):
            return self.rebuild_path(enemy_id, tile_map, enemy_tile, goal_tile)

        if path and enemy_tile not in path:
            return self.rebuild_path(enemy_id, tile_map, enemy_tile, goal_tile)

        return path

    def get_next_tile_from_path(self, path, enemy_tile):
        """Возвращает next тайл from путь.

        Args:
            path: Путь к файлу или список тайлов пути, в зависимости от контекста.
            enemy_tile: Координаты тайла, на котором находится враг.

        Returns:
            Найденное или вычисленное значение: next тайл from путь.
        """
        if enemy_tile not in path:
            return None

        current_index = path.index(enemy_tile)

        if current_index + 1 >= len(path):
            return path[-1]

        return path[current_index + 1]

    def get_entity_tile(self, tile_map, position, collider):
        """Возвращает сущность тайл.

        Args:
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            position: Позиция объекта в пикселях.
            collider: Коллайдер сущности для столкновений и попаданий.

        Returns:
            Найденное или вычисленное значение: сущность тайл.
        """
        if collider is None:
            return tile_map.coord_pixels_to_tile(position.x, position.y)

        center_x = position.x + collider.width / 2
        center_y = position.y + collider.height / 2
        return tile_map.coord_pixels_to_tile(center_x, center_y)

    def get_tile_target_position(self, tile_map, tile, collider=None):
        """Возвращает тайл target position.

        Args:
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            tile: Координаты тайла в формате `(x, y)`.
            collider: Коллайдер сущности для столкновений и попаданий.

        Returns:
            Найденное или вычисленное значение: тайл target position.
        """
        tile_x, tile_y = tile
        x, y = tile_map.coord_tile_to_pixels(tile_x, tile_y)

        if collider is None:
            return x, y

        return (
            x + (tile_map.tile_size - collider.width) / 2,
            y + (tile_map.tile_size - collider.height) / 2,
        )

    def move_towards_position(self, velocity, position, target_x, target_y, speed):
        """Направляет скорость сущности к заданной позиции.

        Args:
            velocity: Скорость сущности по осям X и Y.
            position: Позиция объекта в пикселях.
            target_x: Значение `target x`, используемое в логике метода.
            target_y: Значение `target y`, используемое в логике метода.
            speed: Скорость движения сущности.

        Returns:
            None.
        """
        direction = pygame.Vector2(
            target_x - position.x,
            target_y - position.y,
        )

        if direction.length() == 0:
            self.stop_enemy(velocity)
            return

        direction.normalize_ip()
        velocity.x = direction.x * speed
        velocity.y = direction.y * speed

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

    def stop_enemy(self, enemy_velocity):
        """Останавливает одного врага.

        Args:
            enemy_velocity: Компонент скорости врага.

        Returns:
            None.
        """
        enemy_velocity.x = 0
        enemy_velocity.y = 0

    def stop_enemies(self, ecm):
        """Останавливает всех врагов.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.

        Returns:
            None.
        """
        for enemy_id in ecm.get_entities_with(Enemy, Velocity):
            enemy_velocity = ecm.get_component(enemy_id, Velocity)
            self.stop_enemy(enemy_velocity)
