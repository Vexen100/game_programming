import unittest

from src.components.components import (
    ChaseBehavior,
    Enemy,
    PlayerControlled,
    Position,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.enemy_chase_system import EnemyChaseSystem
from src.world.tile_types import FLOOR, WALL


class FakeTileMap:
    def __init__(self, matrix, tile_size=32):
        self.matrix = matrix
        self.height = len(matrix)
        self.width = len(matrix[0])
        self.tile_size = tile_size

    def is_tile_blocked(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return True

        return self.matrix[tile_y][tile_x] == WALL

    def coord_pixels_to_tile(self, x, y):
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)
        return tile_x, tile_y

    def coord_tile_to_pixels(self, tile_x, tile_y):
        return tile_x * self.tile_size, tile_y * self.tile_size


class TestEnemyChaseSystem(unittest.TestCase):
    def setUp(self):
        self.ecm = EntityComponentManager()
        self.system = EnemyChaseSystem()

    def create_enemy(self, x=0, y=0, speed=50, detection_radius=100):
        enemy = self.ecm.create_entity(tag="enemy")
        self.ecm.add_component(enemy, Enemy())
        self.ecm.add_component(enemy, Position(x, y))
        self.ecm.add_component(enemy, Velocity(10, 20))
        self.ecm.add_component(
            enemy,
            ChaseBehavior(
                speed=speed,
                detection_radius=detection_radius,
            ),
        )
        return enemy

    def create_player(self, x, y):
        player = self.ecm.create_entity(tag="player")
        self.ecm.add_component(player, PlayerControlled())
        self.ecm.add_component(player, Position(x, y))
        return player

    def test_no_player_stops_enemy(self):
        enemy = self.create_enemy()

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_enemy_outside_detection_radius_stops(self):
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=100)
        self.create_player(200, 0)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_enemy_inside_detection_radius_chases_player(self):
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=100)
        self.create_player(100, 0)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 50)
        self.assertEqual(velocity.y, 0)

    def test_update_without_tile_map_keeps_direct_chase_behavior(self):
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=100)
        self.create_player(100, 0)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 50)
        self.assertEqual(velocity.y, 0)

    def test_enemy_same_position_as_player_stops(self):
        enemy = self.create_enemy(x=10, y=10, speed=50, detection_radius=100)
        self.create_player(10, 10)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_enemy_uses_chase_behavior_speed(self):
        enemy = self.create_enemy(x=0, y=0, speed=17, detection_radius=100)
        self.create_player(0, 50)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 17)

    def test_enemy_diagonal_chase_velocity_is_normalized(self):
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=100)
        self.create_player(30, 40)

        self.system.update(self.ecm)
        velocity = self.ecm.get_component(enemy, Velocity)
        velocity_length = (velocity.x ** 2 + velocity.y ** 2) ** 0.5

        self.assertAlmostEqual(velocity_length, 50)

    def test_update_with_tile_map_moves_enemy_on_empty_map(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR],
            ]
        )
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=200)
        self.create_player(64, 0)

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 50)
        self.assertEqual(velocity.y, 0)

    def test_update_with_tile_map_moves_enemy_toward_next_path_tile_around_wall(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
                [FLOOR, WALL, WALL, FLOOR, FLOOR],
                [FLOOR, FLOOR, FLOOR, FLOOR, FLOOR],
            ]
        )
        enemy = self.create_enemy(x=0, y=32, speed=50, detection_radius=300)
        self.create_player(128, 32)

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)
        velocity_length = (velocity.x ** 2 + velocity.y ** 2) ** 0.5

        self.assertAlmostEqual(velocity_length, 50)
        self.assertNotEqual(velocity.y, 0)

    def test_update_with_tile_map_stops_enemy_if_path_is_blocked(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, WALL, FLOOR],
            ]
        )
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=200)
        self.create_player(64, 0)

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_update_with_tile_map_stops_enemy_outside_detection_radius(self):
        tile_map = FakeTileMap(
            [
                [FLOOR, FLOOR, FLOOR, FLOOR],
            ]
        )
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=10)
        self.create_player(96, 0)

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_update_with_tile_map_uses_direct_movement_inside_same_tile(self):
        tile_map = FakeTileMap([[FLOOR]])
        enemy = self.create_enemy(x=0, y=0, speed=50, detection_radius=100)
        self.create_player(10, 0)

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 50)
        self.assertEqual(velocity.y, 0)

    def test_update_with_tile_map_stops_enemies_without_player(self):
        tile_map = FakeTileMap([[FLOOR]])
        enemy = self.create_enemy()

        self.system.update(self.ecm, tile_map)
        velocity = self.ecm.get_component(enemy, Velocity)

        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)


if __name__ == "__main__":
    unittest.main()
