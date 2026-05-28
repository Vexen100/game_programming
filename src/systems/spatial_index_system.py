from src.algorithms.uniform_grid import UniformGrid
from src.components.components import Collider, Dead, Enemy, Position


class SpatialIndexSystem:
    """Строит временные spatial indexes из текущего ECS-состояния"""

    def build_enemy_index(self, ecm, world_width, world_height, cell_size):
        enemy_index = UniformGrid(world_width, world_height, cell_size)

        for enemy_id in ecm.get_entities_with(Enemy, Position, Collider):
            if ecm.has_component(enemy_id, Dead):
                continue

            position = ecm.get_component(enemy_id, Position)
            collider = ecm.get_component(enemy_id, Collider)
            enemy_index.insert(
                enemy_id,
                position.x,
                position.y,
                collider.width,
                collider.height,
            )

        return enemy_index
