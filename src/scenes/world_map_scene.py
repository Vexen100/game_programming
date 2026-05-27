import pygame
import settings
from src.scenes.base_scene import BaseScene
from src.ui import texts
from src.world.region import ENEMY_CONTROL, LOCKED_CONTROL, PLAYER_CONTROL


class WorldMapScene(BaseScene):
    """Простая карта регионов"""

    PLAYER_COLOR = (220, 190, 40)
    ENEMY_COLOR = (160, 40, 40)
    LOCKED_COLOR = (90, 90, 90)
    SELECTED_COLOR = (255, 255, 255)
    TEXT_COLOR = (240, 240, 240)
    BACKGROUND_COLOR = (20, 20, 30)

    def __init__(self, game_state):
        self.game_state = game_state
        self.region_ids = list(self.game_state.regions.keys())
        self.selected_index = self.get_initial_selected_index()
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 42)
        self.manager = None
        self.region_positions = {
            "border_forest": (220, 360),
            "old_ruins": (430, 300),
            "mountain_mines": (650, 220),
            "swamp_lands": (650, 430),
            "capital_fortress": (900, 330),
        }

    def get_initial_selected_index(self):
        if self.game_state.current_region_id in self.region_ids:
            return self.region_ids.index(self.game_state.current_region_id)
        return 0

    def get_selected_region(self):
        return self.game_state.get_region(self.region_ids[self.selected_index])

    def update(self, dt, input_manager):
        if self.should_return_to_gameplay(input_manager):
            self.manager.return_from_world_map()
            return

        if input_manager.was_pressed(settings.MOVE_LEFT) or input_manager.was_pressed(settings.MOVE_UP):
            self.selected_index = (self.selected_index - 1) % len(self.region_ids)

        if input_manager.was_pressed(settings.MOVE_RIGHT) or input_manager.was_pressed(settings.MOVE_DOWN):
            self.selected_index = (self.selected_index + 1) % len(self.region_ids)

        self.update_mouse_selection(input_manager)

        if input_manager.was_pressed(settings.SELECT):
            self.enter_selected_region()

        if input_manager.was_pressed(settings.START_ASSAULT):
            self.start_selected_assault()

    def should_return_to_gameplay(self, input_manager):
        if self.manager is None:
            return False

        if not hasattr(self.manager, "has_world_map_return_scene"):
            return False

        if not self.manager.has_world_map_return_scene():
            return False

        return (
            input_manager.was_pressed(settings.PAUSE)
            or input_manager.was_pressed(settings.OPEN_WORLD_MAP)
        )

    def update_mouse_selection(self, input_manager):
        if not hasattr(input_manager, "was_mouse_pressed"):
            return

        if not input_manager.was_mouse_pressed(1):
            return

        mouse_position = getattr(input_manager, "mouse_position", None)
        clicked_index = self.get_region_index_at_position(mouse_position)

        if clicked_index is None:
            return

        if clicked_index == self.selected_index:
            self.enter_selected_region()
            return

        self.selected_index = clicked_index

    def get_region_index_at_position(self, mouse_position):
        if mouse_position is None:
            return None

        mouse_x, mouse_y = mouse_position

        for index, region_id in enumerate(self.region_ids):
            x, y = self.region_positions[region_id]
            dx = mouse_x - x
            dy = mouse_y - y

            if (dx ** 2 + dy ** 2) ** 0.5 <= 34:
                return index

        return None

    def enter_selected_region(self):
        selected_region = self.get_selected_region()

        if self.manager is None:
            return

        if selected_region.unlocked:
            self.game_state.set_current_region(selected_region.id)
            self.manager.request_change(settings.REGION_SCENE)

    def start_selected_assault(self):
        selected_region = self.get_selected_region()

        if self.manager is None:
            return

        if selected_region.unlocked and selected_region.assault_unlocked:
            self.game_state.set_current_region(selected_region.id)
            self.manager.request_change(settings.CASTLE_ASSAULT_SCENE)

    def draw(self, screen):
        screen.fill(self.BACKGROUND_COLOR)
        self.draw_title(screen)
        self.draw_regions(screen)
        self.draw_selected_region_info(screen)
        self.draw_hint(screen)

    def draw_title(self, screen):
        title_surface = self.title_font.render("Crown Reclaim", True, self.TEXT_COLOR)
        screen.blit(title_surface, (40, 32))

    def draw_regions(self, screen):
        for index, region_id in enumerate(self.region_ids):
            region = self.game_state.get_region(region_id)
            x, y = self.region_positions[region_id]
            color = self.get_region_color(region)

            pygame.draw.circle(screen, color, (x, y), 28)

            if index == self.selected_index:
                pygame.draw.circle(screen, self.SELECTED_COLOR, (x, y), 34, 3)

            name_surface = self.font.render(region.name, True, self.TEXT_COLOR)
            screen.blit(name_surface, (x - 60, y + 42))

    def draw_hint(self, screen):
        selected_region = self.get_selected_region()
        hint_text = texts.WORLD_MAP_ENTER_REGION

        if not selected_region.unlocked:
            hint_text = texts.WORLD_MAP_LOCKED
        elif selected_region.assault_unlocked:
            hint_text = f"{texts.WORLD_MAP_ENTER_REGION} | {texts.WORLD_MAP_START_ASSAULT}"

        if self.manager is not None and hasattr(self.manager, "has_world_map_return_scene"):
            if self.manager.has_world_map_return_scene():
                hint_text = f"{hint_text} | {texts.WORLD_MAP_BACK}"

        hint_surface = self.font.render(hint_text, True, self.TEXT_COLOR)
        screen.blit(hint_surface, (40, settings.SCREEN_HEIGHT - 64))

    def draw_selected_region_info(self, screen):
        selected_region = self.get_selected_region()
        name_surface = self.font.render(selected_region.name, True, self.TEXT_COLOR)
        status_surface = self.font.render(
            self.get_region_status_text(selected_region),
            True,
            self.TEXT_COLOR,
        )

        screen.blit(name_surface, (40, settings.SCREEN_HEIGHT - 132))
        screen.blit(status_surface, (40, settings.SCREEN_HEIGHT - 104))

    def get_region_status_text(self, region):
        assault_status = texts.ASSAULT_READY if region.assault_unlocked else texts.ASSAULT_LOCKED

        return (
            f"{texts.CONTROL_LABEL}: {self.get_control_text(region.control_state)} | "
            f"{texts.INFLUENCE_STATUS.format(player=region.player_influence, enemy=region.enemy_influence)} | "
            f"{assault_status}"
        )

    def get_control_text(self, control_state):
        if control_state == PLAYER_CONTROL:
            return texts.CONTROL_PLAYER
        if control_state == ENEMY_CONTROL:
            return texts.CONTROL_ENEMY
        if control_state == LOCKED_CONTROL:
            return texts.CONTROL_LOCKED
        return control_state

    def get_region_color(self, region):
        if region.control_state == PLAYER_CONTROL:
            return self.PLAYER_COLOR
        if region.control_state == ENEMY_CONTROL:
            return self.ENEMY_COLOR
        if region.control_state == LOCKED_CONTROL:
            return self.LOCKED_COLOR
        return self.LOCKED_COLOR
