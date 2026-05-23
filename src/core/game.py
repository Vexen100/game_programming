import pygame
import settings
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.core.input_manager import InputManager
from src.core.scene_manager import SceneManager
from src.scenes.castle_assault_scene import CastleAssaultScene
from src.scenes.main_menu_scene import MainMenuScene
from src.scenes.pause_scene import PauseScene
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem


class Game:
    """Основной игровой цикл"""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        self.input_manager = InputManager()
        self.game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        self.event_bus = EventBus()
        self.influence_system = InfluenceSystem(self.game_state)
        self.influence_system.subscribe(self.event_bus)
        scene_registry = {
            settings.MAIN_MENU_SCENE: lambda: MainMenuScene(),
            settings.WORLD_MAP_SCENE: lambda: WorldMapScene(self.game_state),
            settings.REGION_SCENE: lambda: RegionScene(self.game_state, self.event_bus),
            settings.CASTLE_ASSAULT_SCENE: lambda: CastleAssaultScene(
                self.game_state,
                self.event_bus,
            ),
            settings.PAUSE_SCENE: lambda: PauseScene(),
        }
        self.scene_manager = SceneManager()
        self.scene_manager.register_scenes(scene_registry)
        self.scene_manager.request_change(settings.MAIN_MENU_SCENE)
        self.scene_manager.process_scene_change()

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

        self.scene_manager.handle_events(events)

    def update(self):
        """
        Обновление положения, анимаций (просто передаётся: менеджеру сцен -> сцене -> объектам)
        """
        self.scene_manager.update(self.dt, self.input_manager)

    def draw(self):
        self.scene_manager.draw(self.screen)
        pygame.display.flip()
