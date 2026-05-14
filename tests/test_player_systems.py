import unittest

import pygame

from src.components.components import (
    Collider,
    PlayerControlled,
    Position,
    Renderable,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import PlayerSettings
from src.systems.collision_system import CollisionSystem
from src.systems.movement_system import MovementSystem
from src.systems.player_input_system import PlayerInputSystem
from src.systems.render_system import RenderSystem
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class FakeInputManager:
    def __init__(self, direction):
        self.direction = direction

    def get_velocity_direction(self):
        return self.direction


class TestPlayerSystems(unittest.TestCase):
    def create_ecm_with_entity(self):
        ecm = EntityComponentManager()
        entity = ecm.create_entity(tag="player")
        return ecm, entity

    def create_tile_map(self):
        matrix = [
            [WALL, WALL, WALL, WALL],
            [WALL, FLOOR, WALL, WALL],
            [WALL, FLOOR, FLOOR, WALL],
            [WALL, WALL, WALL, WALL],
        ]
        return TileMap(matrix)

    def test_player_input_system_no_input(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, PlayerControlled())
        ecm.add_component(entity, Velocity(10, 20))

        system = PlayerInputSystem()
        system.update(ecm, FakeInputManager(pygame.Vector2(0, 0)))

        velocity = ecm.get_component(entity, Velocity)
        self.assertEqual(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_player_input_system_right(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, PlayerControlled())
        ecm.add_component(entity, Velocity())

        system = PlayerInputSystem()
        system.update(ecm, FakeInputManager(pygame.Vector2(1, 0)))

        velocity = ecm.get_component(entity, Velocity)
        self.assertEqual(velocity.x, PlayerSettings.SPEED)
        self.assertEqual(velocity.y, 0)

    def test_movement_system_moves_entity(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(10, 20))
        ecm.add_component(entity, Velocity(5, -2))

        previous_positions = MovementSystem().update(ecm, dt=2)
        position = ecm.get_component(entity, Position)

        self.assertEqual(previous_positions[entity], (10, 20))
        self.assertEqual(position.x, 20)
        self.assertEqual(position.y, 16)

    def test_movement_system_skips_zero_velocity(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(10, 20))
        ecm.add_component(entity, Velocity())

        previous_positions = MovementSystem().update(ecm, dt=2)
        position = ecm.get_component(entity, Position)

        self.assertNotIn(entity, previous_positions)
        self.assertEqual(position.x, 10)
        self.assertEqual(position.y, 20)

    def test_collision_system_blocks_wall(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(64, 32))
        ecm.add_component(entity, Collider(width=32, height=32, solid=True))

        CollisionSystem().update(ecm, self.create_tile_map(), {entity: (32, 32)})
        position = ecm.get_component(entity, Position)

        self.assertEqual(position.x, 32)
        self.assertEqual(position.y, 32)

    def test_collision_system_allows_floor(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(32, 64))
        ecm.add_component(entity, Collider(width=32, height=32, solid=True))

        CollisionSystem().update(ecm, self.create_tile_map(), {entity: (32, 32)})
        position = ecm.get_component(entity, Position)

        self.assertEqual(position.x, 32)
        self.assertEqual(position.y, 64)

    def test_collision_system_skips_not_solid(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(64, 32))
        ecm.add_component(entity, Collider(width=32, height=32, solid=False))

        CollisionSystem().update(ecm, self.create_tile_map(), {entity: (32, 32)})
        position = ecm.get_component(entity, Position)

        self.assertEqual(position.x, 64)
        self.assertEqual(position.y, 32)

    def test_render_system_draws_to_surface(self):
        ecm, entity = self.create_ecm_with_entity()
        ecm.add_component(entity, Position(10, 10))
        ecm.add_component(entity, Renderable(width=16, height=16, color=(50, 120, 255)))
        surface = pygame.Surface((64, 64))

        RenderSystem().draw(ecm, surface)


if __name__ == "__main__":
    unittest.main()
