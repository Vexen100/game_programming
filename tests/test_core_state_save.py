import json
import tempfile
import unittest
from pathlib import Path

import settings
from src.core.event_bus import EventBus
from src.core.game import Game
from src.core.game_state import GameState
from src.core.resource_manager import ResourceManager
from src.core.save_manager import SaveData, SaveManager
from src.core.scene_manager import SceneManager
from src.events.game_events import (
    EnemyKilledEvent,
    OutpostClearedEvent,
    QuestCompletedEvent,
    SupplyCacheDestroyedEvent,
)
from src.systems.influence_system import InfluenceSystem
from src.scenes.base_scene import BaseScene
from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL, RegionState


class FakeSaveManager:
    """Управляет подсистемой: fake сохранение manager.

    """

    def __init__(self, save_data=None, load_error=None):
        """Инициализирует `FakeSaveManager` и сохраняет начальные зависимости.

        Args:
            save_data: Значение `сохранение data`, используемое в логике метода.
            load_error: Значение `load error`, используемое в логике метода.

        Returns:
            None.
        """
        self.save_data = save_data
        self.load_error = load_error
        self.save_called = False
        self.delete_save_called = False

    def has_save(self):
        """Проверяет, есть ли сохранение.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.save_data is not None or self.load_error is not None

    def save(self, game_state, region_runtime=None):
        """Сохраняет текущее состояние во внешний источник.

        Args:
            game_state: Глобальное состояние мира, регионов и прогресса игрока.
            region_runtime: Значение `регион runtime`, используемое в логике метода.

        Returns:
            None.
        """
        self.save_called = True

    def load(self):
        """Загружает данные из внешнего источника.

        Returns:
            Загруженные данные или `None`, если источника нет.
        """
        if self.load_error is not None:
            raise self.load_error
        return self.save_data

    def delete_save(self):
        """Удаляет файл сохранения или отмечает удаление в тестовом фейке.

        Returns:
            None.
        """
        self.delete_save_called = True


class FakeSceneManager:
    """Управляет подсистемой: fake сцена manager.

    """

    def __init__(self):
        """Инициализирует `FakeSceneManager` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.requested_scene_ids = []

    def request_change(self, scene_id):
        """Запрашивает переход на другую сцену.

        Args:
            scene_id: Идентификатор сцены в реестре SceneManager.

        Returns:
            None.
        """
        self.requested_scene_ids.append(scene_id)


class DummyScene(BaseScene):
    """Описывает игровую сцену: dummy сцена.

    """

    def __init__(self):
        """Инициализирует `DummyScene` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.handled_events = False
        self.updated = False
        self.drawn = False

    def handle_events(self, events):
        """Обрабатывает события текущего кадра.

        Args:
            events: Список событий PyGame за текущий кадр.

        Returns:
            None.
        """
        self.handled_events = True

    def update(self, dt, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
        self.updated = True

    def draw(self, screen):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        self.drawn = True


class TestCoreStateSave(unittest.TestCase):
    """Проверяет ключевое поведение: test core состояние сохранение.

    """

    def make_region(self, region_id="r1", unlocked=True, unlocks=None):
        """Создает тестовый RegionState.

        Args:
            region_id: Идентификатор региона на карте мира.
            unlocked: Флаг, показывающий, открыт ли регион.
            unlocks: Значение `unlocks`, используемое в логике метода.

        Returns:
            Результат выполнения `make_region`.
        """
        return RegionState(
            id=region_id,
            name=region_id.title(),
            unlocked=unlocked,
            control_state=PLAYER_CONTROL if unlocked else LOCKED_CONTROL,
            player_influence=100 if unlocked else 0,
            enemy_influence=0 if unlocked else 100,
            assault_unlocked=False,
            liberated=unlocked,
            unlocks_on_liberation=unlocks or [],
        )

    def write_save(self, path, data):
        """Записывает JSON save-файл для теста.

        Args:
            path: Путь к файлу или список тайлов пути, в зависимости от контекста.
            data: Словарь или структура данных из JSON или другого источника.

        Returns:
            None.
        """
        path.write_text(json.dumps(data), encoding="utf-8")

    def create_game_shell(self, save_manager):
        """Создает игра shell.

        Args:
            save_manager: Менеджер сохранений, который читает и записывает прогресс игры.

        Returns:
            Созданный результат: игра shell.
        """
        game = Game.__new__(Game)
        game.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game.save_manager = save_manager
        game.resource_manager = ResourceManager()
        game.region_scene_cache = {}
        game.region_runtime_snapshots = {}
        game.scene_manager = FakeSceneManager()
        return game

    def test_region_state_roundtrip_preserves_fields(self):
        """Проверяет сценарий: регион состояние roundtrip preserves fields.

        Returns:
            None.
        """
        region = self.make_region("old_ruins", unlocks=["mountain_mines"])

        restored = RegionState.from_dict(region.to_dict())

        self.assertEqual(restored.id, "old_ruins")
        self.assertEqual(restored.unlocks_on_liberation, ["mountain_mines"])

    def test_initial_world_state_loads_start_region(self):
        """Проверяет сценарий: initial мир состояние loads start регион.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

        self.assertEqual(game_state.current_region_id, "border_forest")
        self.assertEqual(game_state.get_region("old_ruins").control_state, ENEMY_CONTROL)

    def test_locked_region_cannot_be_selected(self):
        """Проверяет сценарий: locked регион cannot be выбранный.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

        with self.assertRaises(ValueError):
            game_state.set_current_region("mountain_mines")

    def test_mark_liberated_unlocks_next_region(self):
        """Проверяет сценарий: mark liberated unlocks next регион.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

        game_state.mark_liberated("old_ruins")

        self.assertTrue(game_state.get_region("old_ruins").liberated)
        self.assertTrue(game_state.get_region("mountain_mines").unlocked)

    def test_change_influence_is_clamped(self):
        """Проверяет сценарий: change influence is clamped.

        Returns:
            None.
        """
        game_state = GameState([self.make_region("r1")])

        game_state.change_influence("r1", delta_player=50, delta_enemy=-50)

        region = game_state.get_region("r1")
        self.assertEqual(region.player_influence, 100)
        self.assertEqual(region.enemy_influence, 0)

    def test_require_region_raises_for_unknown_id(self):
        """Проверяет сценарий: require регион raises for unknown id.

        Returns:
            None.
        """
        game_state = GameState([self.make_region("r1")])

        with self.assertRaises(ValueError):
            game_state.require_region("missing")

    def test_event_bus_publish_and_unsubscribe(self):
        """Проверяет сценарий: событие bus publish and unsubscribe.

        Returns:
            None.
        """
        event_bus = EventBus()
        received = []

        def handler(event):
            """Обрабатывает событие внутри теста.

            Args:
                event: Событие PyGame или событие внутренней игровой шины.

            Returns:
                None.
            """
            received.append(event)

        event_bus.subscribe(EnemyKilledEvent, handler)
        event_bus.publish(EnemyKilledEvent(1, "r1"))
        event_bus.unsubscribe(EnemyKilledEvent, handler)
        event_bus.publish(EnemyKilledEvent(2, "r1"))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].enemy_id, 1)

    def test_supply_cache_destroyed_event_changes_influence(self):
        """Проверяет влияние события уничтожения склада снабжения.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        event_bus = EventBus()
        InfluenceSystem(game_state).subscribe(event_bus)

        event_bus.publish(SupplyCacheDestroyedEvent("old_ruins", "east_supply_cache"))

        region = game_state.get_region("old_ruins")
        self.assertEqual(region.player_influence, 4)
        self.assertEqual(region.enemy_influence, 96)

    def test_supply_cache_alone_does_not_unlock_assault(self):
        """Проверяет, что один склад не открывает штурм региона.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        event_bus = EventBus()
        InfluenceSystem(game_state).subscribe(event_bus)

        event_bus.publish(SupplyCacheDestroyedEvent("old_ruins", "east_supply_cache"))

        self.assertFalse(game_state.get_region("old_ruins").assault_unlocked)

    def test_supply_cache_keeps_non_combat_objectives_below_assault_unlock(self):
        """Проверяет баланс objectives без отдельного combat contribution.

        Returns:
            None.
        """
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        event_bus = EventBus()
        InfluenceSystem(game_state).subscribe(event_bus)

        event_bus.publish(OutpostClearedEvent(1, "old_ruins"))
        event_bus.publish(OutpostClearedEvent(2, "old_ruins"))
        event_bus.publish(QuestCompletedEvent("quest_a", 1, "old_ruins"))
        event_bus.publish(QuestCompletedEvent("quest_b", 2, "old_ruins"))
        event_bus.publish(SupplyCacheDestroyedEvent("old_ruins", "east_supply_cache"))

        region = game_state.get_region("old_ruins")
        self.assertEqual(region.enemy_influence, 26)
        self.assertFalse(region.assault_unlocked)

    def test_game_autosaves_after_supply_cache_destroyed_event(self):
        """Проверяет autosave после события уничтожения склада.

        Returns:
            None.
        """
        save_manager = FakeSaveManager()
        game = self.create_game_shell(save_manager)
        game.event_bus = EventBus()
        Game.subscribe_autosave_events(game)

        game.event_bus.publish(SupplyCacheDestroyedEvent("old_ruins", "east_supply_cache"))

        self.assertTrue(save_manager.save_called)

    def test_scene_manager_ignores_calls_without_current_scene(self):
        """Проверяет сценарий: сцена manager ignores calls without текущий сцена.

        Returns:
            None.
        """
        scene_manager = SceneManager()

        scene_manager.handle_events([])
        scene_manager.update(0.1, None)
        scene_manager.draw(None)

        self.assertIsNone(scene_manager.current_scene)

    def test_scene_manager_rejects_unregistered_scene(self):
        """Проверяет сценарий: сцена manager rejects unregistered сцена.

        Returns:
            None.
        """
        scene_manager = SceneManager()

        with self.assertRaises(ValueError):
            scene_manager.request_change("missing")

    def test_scene_manager_processes_registered_scene(self):
        """Проверяет сценарий: сцена manager processes registered сцена.

        Returns:
            None.
        """
        scene_manager = SceneManager()
        scene_manager.register_scenes({"dummy": DummyScene})

        scene_manager.request_change("dummy")
        scene_manager.process_scene_change()

        self.assertIsInstance(scene_manager.current_scene, DummyScene)
        self.assertIs(scene_manager.current_scene.manager, scene_manager)

    def test_save_manager_returns_none_when_file_missing(self):
        """Проверяет сценарий: сохранение manager returns none when file missing.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_manager = SaveManager(Path(tmp) / "missing.json")

            self.assertIsNone(save_manager.load())

    def test_save_manager_roundtrip_preserves_state_and_runtime(self):
        """Проверяет сценарий: сохранение manager roundtrip preserves состояние and runtime.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            save_manager = SaveManager(save_path)
            game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)

            save_manager.save(game_state, region_runtime={"old_ruins": {"player": {"x": 1}}})
            loaded = save_manager.load()

            self.assertEqual(loaded.game_state.current_region_id, "border_forest")
            self.assertEqual(loaded.region_runtime["old_ruins"]["player"]["x"], 1)

    def test_save_manager_rejects_top_level_list(self):
        """Проверяет сценарий: сохранение manager rejects top level list.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            self.write_save(save_path, [])

            with self.assertRaises(ValueError):
                SaveManager(save_path).load()

    def test_save_manager_rejects_missing_game_state(self):
        """Проверяет сценарий: сохранение manager rejects missing игра состояние.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            self.write_save(save_path, {"version": SaveManager.SAVE_VERSION})

            with self.assertRaises(ValueError):
                SaveManager(save_path).load()

    def test_save_manager_rejects_game_state_without_regions(self):
        """Проверяет сценарий: сохранение manager rejects игра состояние without регионы.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            self.write_save(save_path, {"version": SaveManager.SAVE_VERSION, "game_state": {}})

            with self.assertRaises(ValueError):
                SaveManager(save_path).load()

    def test_save_manager_rejects_region_runtime_list(self):
        """Проверяет сценарий: сохранение manager rejects регион runtime list.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            self.write_save(
                save_path,
                {
                    "version": SaveManager.SAVE_VERSION,
                    "game_state": {"regions": []},
                    "region_runtime": [],
                },
            )

            with self.assertRaises(ValueError):
                SaveManager(save_path).load()

    def test_save_manager_wraps_malformed_region_data(self):
        """Проверяет сценарий: сохранение manager wraps malformed регион data.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "save.json"
            self.write_save(
                save_path,
                {
                    "version": SaveManager.SAVE_VERSION,
                    "game_state": {"regions": [{"id": "broken"}]},
                    "region_runtime": {},
                },
            )

            with self.assertRaises(ValueError):
                SaveManager(save_path).load()

    def test_continue_game_returns_false_for_corrupted_save(self):
        """Проверяет сценарий: continue игра returns false for corrupted сохранение.

        Returns:
            None.
        """
        save_manager = FakeSaveManager(load_error=ValueError("bad save"))
        game = self.create_game_shell(save_manager)

        result = game.continue_game()

        self.assertFalse(result)
        self.assertFalse(save_manager.delete_save_called)
        self.assertFalse(save_manager.save_called)
        self.assertEqual(game.scene_manager.requested_scene_ids, [])
