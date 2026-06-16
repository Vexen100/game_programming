from src.components.components import CapturePoint


class CastleWaveSystem:
    """Инкапсулирует gameplay-логику системы: замок волна system.

    """

    def __init__(self, spawn_tiles, enemies_per_wave=2):
        """Инициализирует `CastleWaveSystem` и сохраняет начальные зависимости.

        Args:
            spawn_tiles: Список координат тайлов `появление тайлы`.
            enemies_per_wave: Значение `враги per волна`, используемое в логике метода.

        Returns:
            None.
        """
        self.spawn_tiles = spawn_tiles
        self.enemies_per_wave = enemies_per_wave
        self.spawned_for_capture_point_ids = set()
        self.next_spawn_index = 0

    def reset(self):
        """Сбрасывает внутреннее состояние системы.

        Returns:
            None.
        """
        self.spawned_for_capture_point_ids.clear()
        self.next_spawn_index = 0

    def update(self, ecm, entity_factory, tile_map, capture_point_ids):
        """Обновляет состояние объекта за один кадр.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            entity_factory: Фабрика ECS-сущностей стандартных игровых архетипов.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.
            capture_point_ids: Список идентификаторов точек захвата.

        Returns:
            Результат выполнения `update`.
        """
        capture_point_ids = list(capture_point_ids)

        if self.are_all_capture_points_captured(ecm, capture_point_ids):
            return []

        spawned_enemy_ids = []

        for capture_point_id in capture_point_ids:
            capture_point = ecm.get_component(capture_point_id, CapturePoint)

            if not capture_point.captured:
                continue

            if capture_point_id in self.spawned_for_capture_point_ids:
                continue

            spawned_enemy_ids.extend(self.spawn_wave(entity_factory, tile_map))
            self.spawned_for_capture_point_ids.add(capture_point_id)

        return spawned_enemy_ids

    def are_all_capture_points_captured(self, ecm, capture_point_ids):
        """Проверяет, захвачены ли все точки захвата.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            capture_point_ids: Список идентификаторов точек захвата.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if not capture_point_ids:
            return False

        for capture_point_id in capture_point_ids:
            capture_point = ecm.get_component(capture_point_id, CapturePoint)

            if not capture_point.captured:
                return False

        return True

    def spawn_wave(self, entity_factory, tile_map):
        """Создает следующую волну врагов замка.

        Args:
            entity_factory: Фабрика ECS-сущностей стандартных игровых архетипов.
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.

        Returns:
            Список идентификаторов созданных врагов.
        """
        spawned_enemy_ids = []

        for _ in range(self.enemies_per_wave):
            tile_x, tile_y = self.get_next_spawn_tile(tile_map)
            x, y = tile_map.coord_tile_to_pixels(tile_x, tile_y)
            spawned_enemy_ids.append(entity_factory.create_enemy(x=x, y=y))

        return spawned_enemy_ids

    def get_next_spawn_tile(self, tile_map):
        """Возвращает next появление тайл.

        Args:
            tile_map: Тайловая карта для проверки стен, пола и координат тайлов.

        Returns:
            Найденное или вычисленное значение: next появление тайл.
        """
        if not self.spawn_tiles:
            raise ValueError("Castle wave spawn tiles are not configured")

        for _ in range(len(self.spawn_tiles)):
            spawn_tile = self.spawn_tiles[self.next_spawn_index % len(self.spawn_tiles)]
            self.next_spawn_index += 1

            tile_x, tile_y = spawn_tile

            if not tile_map.is_tile_blocked(tile_x, tile_y):
                return spawn_tile

        raise ValueError("No valid castle wave spawn tile")
