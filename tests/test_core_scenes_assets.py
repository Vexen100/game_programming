import os
import tempfile
import unittest
from pathlib import Path

import pygame
from PIL import Image

import settings
from src.components.components import Health, Position, Renderable
from src.core.game_state import GameState
from src.core.resource_manager import ResourceManager
from src.ecs.entity_component_manager import EntityComponentManager
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.render_system import RenderSystem
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
from src.world.castle_generator import CastleGenerator
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL
from tools.asset_pipeline.grid_slicing import get_grid_boxes, parse_csv, parse_hex_color


class FakeManager:
    """Управляет подсистемой: fake manager.

    """

    def __init__(self):
        """Инициализирует `FakeManager` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.requested_scene_ids = []
        self.opened_world_map = False
        self.paused_scene_id = None

    def request_change(self, scene_id):
        """Запрашивает переход на другую сцену.

        Args:
            scene_id: Идентификатор сцены в реестре SceneManager.

        Returns:
            None.
        """
        self.requested_scene_ids.append(scene_id)

    def open_world_map(self, return_scene=None):
        """Открывает карту мира.

        Args:
            return_scene: Сцена, в которую нужно вернуться после карты мира.

        Returns:
            None.
        """
        self.opened_world_map = True
        self.return_scene = return_scene

    def request_pause(self, pause_scene_id):
        """Запрашивает переход в сцену паузы.

        Args:
            pause_scene_id: Идентификатор сцены паузы.

        Returns:
            None.
        """
        self.paused_scene_id = pause_scene_id


class FakeInput:
    """Описывает объект проекта: fake ввод.

    """

    def __init__(self, pressed=None):
        """Инициализирует `FakeInput` и сохраняет начальные зависимости.

        Args:
            pressed: Значение `нажатие`, используемое в логике метода.

        Returns:
            None.
        """
        self.pressed = set(pressed or [])
        self.mouse_position = None

    def was_pressed(self, action):
        """Проверяет, было ли действие нажато в текущем кадре.

        Args:
            action: Имя игрового действия из таблицы привязок ввода.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return action in self.pressed

    def was_mouse_pressed(self, button):
        """Проверяет, была ли кнопка мыши нажата в текущем кадре.

        Args:
            button: Кнопка мыши, состояние которой нужно проверить.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return False


class SpyTileMap:
    """Запоминает вызов TileMap.draw для проверки порядка слоев."""

    def __init__(self, calls):
        """Инициализирует список вызовов.

        Args:
            calls: Общий список, куда записываются названия слоев.

        Returns:
            None.
        """
        self.calls = calls

    def draw(self, screen, camera=None, resource_manager=None):
        """Запоминает отрисовку tile map.

        Args:
            screen: Поверхность PyGame.
            camera: Камера сцены.
            resource_manager: Менеджер ресурсов сцены.

        Returns:
            None.
        """
        self.calls.append("tile_map")


class SpyRenderSystem:
    """Запоминает вызовы RenderSystem для проверки layering."""

    def __init__(self, calls):
        """Инициализирует список вызовов.

        Args:
            calls: Общий список, куда записываются названия слоев.

        Returns:
            None.
        """
        self.calls = calls

    def draw(self, ecm, screen, camera=None):
        """Запоминает отрисовку world entities.

        Args:
            ecm: Менеджер сущностей и компонентов.
            screen: Поверхность PyGame.
            camera: Камера сцены.

        Returns:
            None.
        """
        self.calls.append("entities")

    def draw_attack_hitboxes(self, ecm, screen, camera=None):
        """Запоминает отрисовку attack hitboxes.

        Args:
            ecm: Менеджер сущностей и компонентов.
            screen: Поверхность PyGame.
            camera: Камера сцены.

        Returns:
            None.
        """
        self.calls.append("hitboxes")

    def draw_enemy_health_bars(self, ecm, screen, camera=None):
        """Запоминает отрисовку enemy health bars.

        Args:
            ecm: Менеджер сущностей и компонентов.
            screen: Поверхность PyGame.
            camera: Камера сцены.

        Returns:
            None.
        """
        self.calls.append("health_bars")


class SpyDebugOverlay:
    """Запоминает вызов debug overlay."""

    def __init__(self, calls):
        """Инициализирует список вызовов.

        Args:
            calls: Общий список, куда записываются названия слоев.

        Returns:
            None.
        """
        self.calls = calls

    def draw(self, screen, ecm, player_id, tile_map, dt):
        """Запоминает отрисовку debug overlay.

        Args:
            screen: Поверхность PyGame.
            ecm: Менеджер сущностей и компонентов.
            player_id: Идентификатор игрока.
            tile_map: Тайловая карта сцены.
            dt: Длительность кадра.

        Returns:
            None.
        """
        self.calls.append("debug")


class SpyVisualEffectSystem:
    """Запоминает вызов visual effects layer."""

    def __init__(self, calls):
        """Инициализирует список вызовов.

        Args:
            calls: Общий список, куда записываются названия слоев.

        Returns:
            None.
        """
        self.calls = calls

    def draw(self, ecm, screen, camera=None):
        """Запоминает отрисовку visual effects.

        Args:
            ecm: Менеджер сущностей и компонентов.
            screen: Поверхность PyGame.
            camera: Камера сцены.

        Returns:
            None.
        """
        self.calls.append("visual_effects")


class SpyHUD:
    """Запоминает вызовы HUD."""

    def __init__(self, calls):
        """Инициализирует список вызовов.

        Args:
            calls: Общий список, куда записываются названия слоев.

        Returns:
            None.
        """
        self.calls = calls

    def draw(self, screen, ecm, player_id, scene_name, contextual_prompts=None, status_lines=None):
        """Запоминает отрисовку HUD.

        Args:
            screen: Поверхность PyGame.
            ecm: Менеджер сущностей и компонентов.
            player_id: Идентификатор игрока.
            scene_name: Название сцены.
            contextual_prompts: Контекстные подсказки.
            status_lines: Строки статуса.

        Returns:
            None.
        """
        self.calls.append("hud")

    def draw_defeat_message(self, screen, message):
        """Запоминает сообщение поражения.

        Args:
            screen: Поверхность PyGame.
            message: Текст сообщения.

        Returns:
            None.
        """
        self.calls.append("defeat")


class TestCoreScenesAssets(unittest.TestCase):
    """Проверяет ключевое поведение: test core scenes ассеты.

    """

    @classmethod
    def setUpClass(cls):
        """Готовит общий PyGame-контекст для тестового класса.

        Returns:
            None.
        """
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        pygame.font.init()

    def load_game_state(self):
        """Загружает игра состояние.

        Returns:
            Результат выполнения `load_game_state`.
        """
        return GameState.load_from_file(settings.REGIONS_DATA_PATH)

    def test_resource_manager_returns_placeholder_for_missing_tile_asset(self):
        """Проверяет сценарий: ресурс manager returns placeholder for missing тайл ассет.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            resource_manager = ResourceManager(image_root=tmp, tile_assets={}, entity_assets={})

            surface = resource_manager.get_tile_surface(FLOOR, 32)

            self.assertEqual(surface.get_size(), (32, 32))

    def test_resource_manager_loads_existing_image(self):
        """Проверяет сценарий: ресурс manager loads existing изображение.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "tile.png"
            Image.new("RGBA", (16, 16), (255, 0, 0, 255)).save(image_path)
            resource_manager = ResourceManager(
                image_root=tmp,
                tile_assets={FLOOR: "tile.png"},
                entity_assets={},
            )

            surface = resource_manager.get_tile_surface(FLOOR, 32)

            self.assertEqual(surface.get_size(), (32, 32))
            self.assertTrue(resource_manager.has_image(f"tile_{FLOOR}"))

    def test_tile_map_draws_to_surface(self):
        """Проверяет сценарий: тайл карта draws to поверхность.

        Returns:
            None.
        """
        screen = pygame.Surface((64, 32))
        tile_map = TileMap([[FLOOR, WALL]])

        tile_map.draw(screen)

        self.assertNotEqual(screen.get_at((1, 1)), screen.get_at((40, 1)))

    def test_render_system_draws_entity_rect_without_resource_manager(self):
        """Проверяет сценарий: render system draws сущность прямоугольник without ресурс manager.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, Position(4, 4))
        ecm.add_component(entity, Renderable(8, 8, (10, 200, 10)))
        screen = pygame.Surface((32, 32))

        RenderSystem().draw(ecm, screen)

        self.assertEqual(screen.get_at((5, 5))[:3], (10, 200, 10))

    def test_hud_and_debug_overlay_draw_without_errors(self):
        """Проверяет сценарий: hud and debug overlay draw without errors.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        player = ecm.create_entity()
        ecm.add_component(player, Health(10, 10))
        ecm.add_component(player, Position(32, 32))
        screen = pygame.Surface((320, 240))
        tile_map = TileMap([[FLOOR for _ in range(3)] for _ in range(3)])
        overlay = DebugOverlay()
        overlay.toggle()

        HUD().draw(screen, ecm, player, "Тест")
        overlay.draw(screen, ecm, player, tile_map, dt=0.1)

        self.assertTrue(overlay.visible)

    def test_region_scene_builds_tile_map_and_entities(self):
        """Проверяет сценарий: регион сцена builds тайл карта and сущности.

        Returns:
            None.
        """
        scene = RegionScene(game_state=self.load_game_state())

        self.assertGreater(scene.tile_map.width, 0)
        self.assertGreater(len(scene.enemy_ids), 0)
        self.assertGreater(len(scene.outpost_ids), 0)
        self.assertGreater(len(scene.npc_ids), 0)

    def test_region_scene_requests_castle_assault_when_unlocked(self):
        """Проверяет сценарий: регион сцена requests замок штурм when открытые.

        Returns:
            None.
        """
        game_state = self.load_game_state()
        game_state.set_current_region("old_ruins")
        game_state.mark_assault_unlocked("old_ruins")
        scene = RegionScene(game_state=game_state)
        scene.manager = FakeManager()

        result = scene.request_castle_assault()

        self.assertTrue(result)
        self.assertEqual(scene.manager.requested_scene_ids, [settings.CASTLE_ASSAULT_SCENE])

    def test_region_scene_draw_layers_debug_before_hud(self):
        """Проверяет порядок слоев RegionScene: world, effects, debug, HUD.

        Returns:
            None.
        """
        scene = RegionScene(game_state=self.load_game_state())
        calls = []
        scene.tile_map = SpyTileMap(calls)
        scene.render_system = SpyRenderSystem(calls)
        scene.visual_effect_system = SpyVisualEffectSystem(calls)
        scene.debug_overlay = SpyDebugOverlay(calls)
        scene.hud = SpyHUD(calls)
        screen = pygame.Surface((320, 240))

        scene.draw(screen)

        self.assertEqual(
            calls,
            [
                "tile_map",
                "entities",
                "hitboxes",
                "visual_effects",
                "health_bars",
                "debug",
                "hud",
            ],
        )

    def test_region_scene_has_visual_effect_system(self):
        """Проверяет, что RegionScene создает систему визуальных эффектов.

        Returns:
            None.
        """
        scene = RegionScene(game_state=self.load_game_state())

        self.assertIsNotNone(scene.visual_effect_system)
        self.assertIs(scene.melee_attack_system.visual_effect_system, scene.visual_effect_system)

    def test_castle_assault_scene_builds_layout_and_capture_points(self):
        """Проверяет сценарий: замок штурм сцена builds layout and точка захвата точки.

        Returns:
            None.
        """
        layout = CastleGenerator(48, 36, seed=31).generate()
        scene = CastleAssaultScene(game_state=self.load_game_state(), castle_layout=layout)

        self.assertEqual(scene.castle_layout_fingerprint, layout.fingerprint())
        self.assertEqual(len(scene.capture_point_ids), len(layout.capture_point_tiles))
        self.assertGreater(len(scene.enemy_ids), 0)

    def test_castle_assault_scene_has_visual_effect_system(self):
        """Проверяет, что CastleAssaultScene создает систему визуальных эффектов.

        Returns:
            None.
        """
        layout = CastleGenerator(48, 36, seed=31).generate()
        scene = CastleAssaultScene(game_state=self.load_game_state(), castle_layout=layout)

        self.assertIsNotNone(scene.visual_effect_system)
        self.assertIs(scene.melee_attack_system.visual_effect_system, scene.visual_effect_system)

    def test_world_map_enters_unlocked_region(self):
        """Проверяет сценарий: мир карта enters открытые регион.

        Returns:
            None.
        """
        game_state = self.load_game_state()
        scene = WorldMapScene(game_state)
        scene.manager = FakeManager()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.enter_selected_region()

        self.assertEqual(game_state.current_region_id, "old_ruins")
        self.assertEqual(scene.manager.requested_scene_ids, [settings.REGION_SCENE])

    def test_world_map_starts_unlocked_assault(self):
        """Проверяет сценарий: мир карта starts открытые штурм.

        Returns:
            None.
        """
        game_state = self.load_game_state()
        game_state.mark_assault_unlocked("old_ruins")
        scene = WorldMapScene(game_state)
        scene.manager = FakeManager()
        scene.selected_index = scene.region_ids.index("old_ruins")

        scene.start_selected_assault()

        self.assertEqual(game_state.current_region_id, "old_ruins")
        self.assertEqual(scene.manager.requested_scene_ids, [settings.CASTLE_ASSAULT_SCENE])

    def test_asset_pipeline_parse_helpers(self):
        """Проверяет сценарий: ассет pipeline parse helpers.

        Returns:
            None.
        """
        self.assertEqual(parse_csv(" idle, run ,, attack "), ["idle", "run", "attack"])
        self.assertEqual(parse_hex_color("#ff00aa"), (255, 0, 170))

    def test_asset_pipeline_grid_boxes_exact_mode(self):
        """Проверяет сценарий: ассет pipeline сетка области exact mode.

        Returns:
            None.
        """
        boxes = get_grid_boxes((64, 32), cols=2, rows=1)

        self.assertEqual(boxes, [(0, 0, 32, 32), (32, 0, 64, 32)])
