import json

from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL, RegionState


class GameState:
    """Хранит глобальное состояние регионов"""

    def __init__(self, regions, current_region_id=None):
        self.regions = {region.id: region for region in regions}
        self.current_region_id = current_region_id

        if self.current_region_id is None:
            self.current_region_id = self.get_first_unlocked_region_id()

    @classmethod
    def load_from_file(cls, file_path):
        with open(file_path, encoding="utf-8") as file:
            regions_data = json.load(file)

        regions = [RegionState.from_dict(region_data) for region_data in regions_data]
        return cls(regions)

    def get_first_unlocked_region_id(self):
        for region in self.regions.values():
            if region.unlocked:
                return region.id
        return None

    def get_region(self, region_id):
        return self.regions.get(region_id)

    def set_current_region(self, region_id):
        region = self.require_region(region_id)

        if not region.unlocked:
            raise ValueError(f"Регион с id '{region_id}' закрыт")

        self.current_region_id = region_id

    def unlock_region(self, region_id):
        region = self.require_region(region_id)

        region.unlocked = True
        if region.control_state == LOCKED_CONTROL:
            region.control_state = ENEMY_CONTROL

    def change_influence(self, region_id, delta_player=0, delta_enemy=0):
        region = self.require_region(region_id)

        region.player_influence = self.clamp(region.player_influence + delta_player)
        region.enemy_influence = self.clamp(region.enemy_influence + delta_enemy)

    def mark_assault_unlocked(self, region_id):
        region = self.require_region(region_id)
        region.assault_unlocked = True

    def mark_liberated(self, region_id):
        region = self.require_region(region_id)

        region.liberated = True
        region.unlocked = True
        region.control_state = PLAYER_CONTROL
        region.player_influence = 100
        region.enemy_influence = 0
        region.assault_unlocked = False

    def get_unlocked_regions(self):
        return [region for region in self.regions.values() if region.unlocked]

    def require_region(self, region_id):
        region = self.get_region(region_id)
        if region is None:
            raise ValueError(f"Регион с id '{region_id}' не найден")
        return region

    def clamp(self, value, minimum=0, maximum=100):
        return max(minimum, min(maximum, value))
