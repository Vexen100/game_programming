import os
import tempfile
import unittest
from pathlib import Path

import pygame
from PIL import Image

from src.components.components import Animation, HitFlash, Position, Renderable, Sprite
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

    def test_render_system_draws_supply_cache_without_asset(self):
        """Проверяет fallback-отрисовку склада снабжения без PNG.

        Returns:
            None.
        """
        resource_manager = ResourceManager(image_root="missing-root")
        ecm = EntityComponentManager()
        self.create_entity(
            ecm,
            0,
            0,
            color=(165, 95, 35),
            asset_key="supply_cache_enemy",
        )
        screen = pygame.Surface((32, 32), pygame.SRCALPHA)

        RenderSystem(resource_manager).draw(ecm, screen)

        self.assertEqual(screen.get_at((8, 10))[:3], (165, 95, 35))

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

    def test_render_system_draws_hit_flash_overlay_without_crash(self):
        """Проверяет отрисовку hit flash overlay без падения.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = self.create_entity(ecm, 0, 0, color=(10, 20, 30))
        ecm.add_component(entity, HitFlash(timer=0.12))
        screen = pygame.Surface((32, 32), pygame.SRCALPHA)

        RenderSystem().draw(ecm, screen)

        self.assertGreater(screen.get_at((8, 8)).r, 10)

    def test_render_system_draws_animation_frame_when_available(self):
        """Проверяет приоритет runtime animation frame над static sprite.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "walk_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (220, 80, 30, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="walk", direction="down"))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertEqual(screen.get_at((8, 8))[:3], (220, 80, 30))

    def test_render_system_falls_back_to_static_sprite_when_animation_frame_missing(self):
        """Проверяет fallback с missing animation frame на static Sprite.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (40, 200, 90, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={"player": "entities/player.png"},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="walk", direction="down"))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertEqual(screen.get_at((8, 8))[:3], (40, 200, 90))

    def test_render_system_falls_back_to_rectangle_when_animation_and_sprite_missing(self):
        """Проверяет fallback rectangle без animation frame и Sprite.

        Returns:
            None.
        """
        resource_manager = ResourceManager(
            image_root="missing-root",
            tile_assets={},
            entity_assets={},
        )
        ecm = EntityComponentManager()
        entity = self.create_entity(ecm, 0, 0, color=(15, 90, 200))
        ecm.add_component(entity, Animation("player", state="walk", direction="down"))
        screen = pygame.Surface((32, 32), pygame.SRCALPHA)

        RenderSystem(resource_manager).draw(ecm, screen)

        self.assertEqual(screen.get_at((8, 8))[:3], (15, 90, 200))

    def test_hit_flash_overlay_still_works_with_animation_frame(self):
        """Проверяет hit flash поверх animated frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "walk_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (10, 20, 30, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="walk", direction="down"))
            ecm.add_component(entity, HitFlash(timer=0.12))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertGreater(screen.get_at((8, 8)).r, 10)

    def test_render_system_draws_attack_animation_frame_when_available(self):
        """Проверяет отрисовку attack animation frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "attack_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (230, 70, 120, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="attack", direction="down"))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertEqual(screen.get_at((8, 8))[:3], (230, 70, 120))

    def test_render_system_falls_back_to_static_sprite_when_attack_frame_missing(self):
        """Проверяет fallback static Sprite для missing attack frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (20, 160, 220, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={"player": "entities/player.png"},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="attack", direction="down"))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertEqual(screen.get_at((8, 8))[:3], (20, 160, 220))

    def test_hit_flash_overlay_still_works_with_attack_animation_frame(self):
        """Проверяет HitFlash поверх attack animation frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "entities" / "player" / "attack_down_0.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (10, 20, 30, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={},
                entity_assets={},
            )
            ecm = EntityComponentManager()
            entity = self.create_entity(ecm, 0, 0, asset_key="player")
            ecm.add_component(entity, Animation("player", state="attack", direction="down"))
            ecm.add_component(entity, HitFlash(timer=0.12))
            screen = pygame.Surface((32, 32), pygame.SRCALPHA)

            RenderSystem(resource_manager).draw(ecm, screen)

            self.assertGreater(screen.get_at((8, 8)).r, 10)
