from src.components.components import CapturePoint


class CastleWaveSystem:
    """Создаёт минимальные подкрепления в замке после захвата точек"""

    def __init__(self, spawn_tiles, enemies_per_wave=2):
        self.spawn_tiles = spawn_tiles
        self.enemies_per_wave = enemies_per_wave
        self.spawned_for_capture_point_ids = set()
        self.next_spawn_index = 0

    def reset(self):
        self.spawned_for_capture_point_ids.clear()
        self.next_spawn_index = 0

    def update(self, ecm, entity_factory, tile_map, capture_point_ids):
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
        if not capture_point_ids:
            return False

        for capture_point_id in capture_point_ids:
            capture_point = ecm.get_component(capture_point_id, CapturePoint)

            if not capture_point.captured:
                return False

        return True

    def spawn_wave(self, entity_factory, tile_map):
        spawned_enemy_ids = []

        for _ in range(self.enemies_per_wave):
            tile_x, tile_y = self.get_next_spawn_tile(tile_map)
            x, y = tile_map.coord_tile_to_pixels(tile_x, tile_y)
            spawned_enemy_ids.append(entity_factory.create_enemy(x=x, y=y))

        return spawned_enemy_ids

    def get_next_spawn_tile(self, tile_map):
        if not self.spawn_tiles:
            raise ValueError("Castle wave spawn tiles are not configured")

        for _ in range(len(self.spawn_tiles)):
            spawn_tile = self.spawn_tiles[self.next_spawn_index % len(self.spawn_tiles)]
            self.next_spawn_index += 1

            tile_x, tile_y = spawn_tile

            if not tile_map.is_tile_blocked(tile_x, tile_y):
                return spawn_tile

        raise ValueError("No valid castle wave spawn tile")
