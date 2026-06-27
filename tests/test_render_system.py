import os
import tempfile
import unittest
from pathlib import Path

import pygame
from PIL import Image

from src.components.components import Position, Renderable, Sprite
from src.core.resource_manager import ResourceManager
from src.ecs.entity_component_manager import EntityComponentManager
from src.systems.render_system import RenderSystem


class TestRenderSystem(unittest.TestCase):
    """Проверяет static sprite rendering и Y-sort порядок."""

    @classmethod
    def setUpClass(cls):
        """Инициализирует PyGame для headless rendering tests.

        Returns:
            None.
        """
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()

    def create_entity(self, ecm, x, y, color=(200, 0, 0), asset_key=None):
        """Создает renderable entity для тестов RenderSystem.

        Args:
            ecm: Менеджер сущностей и компонентов игрового мира.
            x: Координата по оси X.
            y: Координата по оси Y.
            color: Fallback-цвет прямоугольника.
            asset_key: Необязательный ключ static sprite.

        Returns:
            Идентификатор созданной сущности.
        """
        entity = ecm.create_entity()
        ecm.add_component(entity, Position(x, y))
        ecm.add_component(entity, Renderable(16, 16, color))

        if asset_key is not None:
            ecm.add_component(entity, Sprite(asset_key))

        return entity

    def test_render_system_draws_sprite_when_resource_manager_has_asset(self):
        """Проверяет отрисовку static PNG sprite.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (30, 120, 220, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={"player": "entities/player.png"},
            )
            ecm = EntityComponentManager()
            self.create_entity(ecm, 0, 0, asset_key="player")
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertEqual(screen.get_at((8, 8))[:3], (30, 120, 220))

    def test_render_system_falls_back_without_sprite_asset(self):
        """Проверяет fallback, когда Sprite есть, а PNG отсутствует.

        Returns:
            None.
        """
        resource_manager = ResourceManager(
            image_root="missing-root",
            tile_assets={},
            entity_assets={"player": "entities/missing.png"},
        )
        ecm = EntityComponentManager()
        self.create_entity(ecm, 0, 0, color=(10, 200, 30), asset_key="player")
        screen = pygame.Surface((32, 32), pygame.SRCALPHA)

        RenderSystem(resource_manager).draw(ecm, screen)

        self.assertGreater(screen.get_at((8, 8)).a, 0)

    def test_render_system_sorts_entities_by_baseline_y(self):
        """Проверяет Y-sort по visual baseline.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        lower_baseline = self.create_entity(ecm, 0, 30)
        upper_baseline = self.create_entity(ecm, 0, 5)

        order = RenderSystem().get_render_order(ecm)

        self.assertEqual(order, [upper_baseline, lower_baseline])

    def test_render_order_tie_breaks_by_entity_id(self):
        """Проверяет deterministic порядок при одинаковом baseline.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        first = self.create_entity(ecm, 0, 10)
        second = self.create_entity(ecm, 0, 10)

        order = RenderSystem().get_render_order(ecm)

        self.assertEqual(order, [first, second])
