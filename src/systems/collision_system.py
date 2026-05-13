from src.components.components import Collider, Position


class CollisionSystem:
    """Проверяет столкновения сущностей с тайловой картой"""

    def update(self, ecm, tile_map, previous_positions):
        for entity in ecm.get_entities_with(Position, Collider):
            if entity not in previous_positions:
                continue

            position = ecm.get_component(entity, Position)
            collider = ecm.get_component(entity, Collider)

            if not collider.solid:
                continue

            old_x, old_y = previous_positions[entity]
            new_x = position.x
            new_y = position.y

            position.x = old_x
            position.y = old_y

            if not tile_map.is_rect_blocked(new_x, old_y, collider.width, collider.height):
                position.x = new_x

            if not tile_map.is_rect_blocked(position.x, new_y, collider.width, collider.height):
                position.y = new_y
