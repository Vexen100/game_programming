import pygame
import settings
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.core.input_manager import InputManager
from src.core.save_manager import SaveManager
from src.core.scene_manager import SceneManager
from src.events.game_events import (
    EnemyKilledEvent,
    OutpostClearedEvent,
    QuestCompletedEvent,
    RegionLiberatedEvent,
)
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.scenes.main_menu_scene import MainMenuScene
from src.scenes.pause_scene import PauseScene
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem
from src.systems.region_liberation_system import RegionLiberationSystem


class Game:
    """Основной игровой цикл"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = False
        self.dt = 0
        self.input_manager = InputManager()
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        self.save_manager = SaveManager(settings.SAVE_FILE_PATH)
        self.region_scene_cache = {}
        self.region_runtime_snapshots = {}
        self.rebuild_world_systems()
        self.scene_manager = SceneManager()
        self.scene_manager.register_scenes(self.build_scene_registry())
        self.scene_manager.request_change(settings.MAIN_MENU_SCENE)
        self.scene_manager.process_scene_change()

    def build_scene_registry(self):
        return {
            settings.MAIN_MENU_SCENE: lambda: MainMenuScene(
                on_new_game=self.start_new_game,
                on_continue=self.continue_game,
                has_save=self.save_manager.has_save(),
            ),
            settings.WORLD_MAP_SCENE: lambda: WorldMapScene(self.game_state),
            settings.REGION_SCENE: self.get_region_scene,
            settings.CASTLE_ASSAULT_SCENE: lambda: CastleAssaultScene(
                self.game_state,
                self.event_bus,
            ),
            settings.PAUSE_SCENE: lambda: PauseScene(),
        }

    def rebuild_world_systems(self):
        self.event_bus = EventBus()
        self.influence_system = InfluenceSystem(self.game_state)
        self.influence_system.subscribe(self.event_bus)
        self.region_liberation_system = RegionLiberationSystem(self.game_state)
        self.region_liberation_system.subscribe(self.event_bus)
        self.subscribe_autosave_events()

    def subscribe_autosave_events(self):
        self.event_bus.subscribe(EnemyKilledEvent, self.on_world_progress_changed)
        self.event_bus.subscribe(OutpostClearedEvent, self.on_world_progress_changed)
        self.event_bus.subscribe(QuestCompletedEvent, self.on_world_progress_changed)
        self.event_bus.subscribe(RegionLiberatedEvent, self.on_world_progress_changed)

    def on_world_progress_changed(self, event):
        self.save_current_progress()

    def collect_region_runtime_snapshots(self):
        snapshots = dict(self.region_runtime_snapshots)

        for region_id, scene in self.region_scene_cache.items():
            snapshots[region_id] = scene.export_runtime_state()

        return snapshots

    def save_current_progress(self):
        self.save_manager.save(
            self.game_state,
            region_runtime=self.collect_region_runtime_snapshots(),
        )

    def reset_world_for_new_game(self):
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        self.region_scene_cache = {}
        self.region_runtime_snapshots = {}
        self.rebuild_world_systems()

    def load_saved_game(self):
        save_data = self.save_manager.load()

        if save_data is None:
            return False

        self.game_state = save_data.game_state
        self.region_runtime_snapshots = save_data.region_runtime
        self.region_scene_cache = {}
        self.rebuild_world_systems()
        return True

    def start_new_game(self):
        self.save_manager.delete_save()
        self.reset_world_for_new_game()
        self.save_current_progress()
        self.scene_manager.request_change(settings.WORLD_MAP_SCENE)
        return True

    def continue_game(self):
        try:
            loaded = self.load_saved_game()
        except ValueError:
            return False

        if not loaded:
            return False

        self.scene_manager.request_change(settings.WORLD_MAP_SCENE)
        return True

    def get_region_scene(self):
        region_id = self.game_state.current_region_id

        if region_id not in self.region_scene_cache:
            scene = RegionScene(self.game_state, self.event_bus)
            scene.apply_runtime_state(
                self.region_runtime_snapshots.get(region_id, {})
            )
            self.region_scene_cache[region_id] = scene

        return self.region_scene_cache[region_id]

    def run(self):
        """Запускает игровой цикл"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()

            # очищаем нажатые один раз и отпущенные клавиши в конце кадра
            self.input_manager.clear()

            # проводим смену сцены, если был запрос
            self.scene_manager.process_scene_change()

            self.dt = self.clock.tick(settings.FPS) / 1000

        pygame.quit()

    def handle_events(self):
        """Обрабатывает системные события и передаёт нажатия клавиш менеджеру ввода"""
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            self.input_manager.update_events(event)

        if self.input_manager.was_pressed(settings.TOGGLE_FULLSCREEN):
            self.toggle_fullscreen()

        self.scene_manager.handle_events(events)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            flags,
        )

    def update(self):
        """
        Обновление положения, анимаций (просто передаётся: менеджеру сцен -> сцене -> объектам)
        """
        self.scene_manager.update(self.dt, self.input_manager)

    def draw(self):
        self.scene_manager.draw(self.screen)
        pygame.display.flip()
