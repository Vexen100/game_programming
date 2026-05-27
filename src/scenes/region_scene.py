import pygame
import settings
from src.algorithms.flood_fill import are_tiles_reachable
from src.components.components import (
    AttackHitbox,
    AttackIntent,
    Collider,
    Health,
    NPC,
    Outpost,
    PatrolRoute,
    PlayerDefeated,
    Position,
    Velocity,
)
from src.core.camera import Camera
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.scenes.base_scene import BaseScene
from src.systems.cleanup_system import CleanupSystem
from src.systems.collision_system import CollisionSystem
from src.systems.enemy_attack_system import EnemyAttackSystem
from src.systems.enemy_chase_system import EnemyChaseSystem
from src.systems.enemy_death_system import EnemyDeathSystem
from src.systems.melee_attack_system import MeleeAttackSystem
from src.systems.movement_system import MovementSystem
from src.systems.npc_interaction_system import NPCInteractionSystem
from src.systems.outpost_system import OutpostSystem
from src.systems.player_attack_input_system import PlayerAttackInputSystem
from src.systems.player_death_system import PlayerDeathSystem
from src.systems.player_input_system import PlayerInputSystem
from src.systems.render_system import RenderSystem
from src.ui import texts
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class RegionScene(BaseScene):
    """
    Стандартная сцена региона. Поле, где бегает игрок и происходит сама игра.
    """

    def __init__(self, game_state=None, event_bus=None) -> None:
        self.game_state = game_state
        self.event_bus = event_bus
        self.player_input_system = PlayerInputSystem()
        self.player_attack_input_system = PlayerAttackInputSystem()
        self.enemy_chase_system = EnemyChaseSystem()
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem()
        self.melee_attack_system = MeleeAttackSystem()
        self.enemy_death_system = EnemyDeathSystem(self.event_bus)
        self.outpost_system = OutpostSystem(self.event_bus)
        self.npc_interaction_system = NPCInteractionSystem(self.event_bus)
        self.enemy_attack_system = EnemyAttackSystem()
        self.player_death_system = PlayerDeathSystem()
        self.cleanup_system = CleanupSystem()
        self.render_system = RenderSystem()
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None
        self.player_spawn_tile = (3, 3)
        self.restart_region()

    def check_entity_components(self, entity_id, entity_name, *component_types):
        """Проверяет, что сущность создана с нужными компонентами"""
        for component_type in component_types:
            component = self.ecm.get_component(entity_id, component_type)
            if component is None:
                raise RuntimeError(
                    f"{entity_name} was created without {component_type.__name__} component"
                )

    def create_test_map(self):
        """Создаёт крупную ручную карту региона"""
        width = 60
        height = 36
        matrix = []

        for row in range(height):
            map_row = []
            for tile in range(width):
                is_border = row == 0 or tile == 0 or row == height - 1 or tile == width - 1
                is_inner_wall = (
                    (tile == 12 and 4 <= row <= 18 and row not in (10, 11))
                    or (row == 14 and 18 <= tile <= 36 and tile not in (26, 27))
                    or (tile == 34 and 6 <= row <= 24 and row not in (16, 17))
                    or (row == 24 and 8 <= tile <= 28 and tile not in (18, 19))
                    or (tile == 46 and 10 <= row <= 30 and row not in (22, 23))
                )
                if is_border or is_inner_wall:
                    map_row.append(WALL)
                else:
                    map_row.append(FLOOR)
            matrix.append(map_row)

        return matrix

    def handle_events(self, events):
        pass

    def is_player_defeated(self):
        return self.ecm.has_component(self.ecs_player_id, PlayerDefeated)

    def request_world_map(self):
        if self.manager is not None:
            if hasattr(self.manager, "open_world_map"):
                self.manager.open_world_map(return_scene=self)
            else:
                self.manager.request_change(settings.WORLD_MAP_SCENE)

    def request_pause(self):
        if self.manager is not None:
            self.manager.request_pause(settings.PAUSE_SCENE)

    def get_region_title(self):
        if self.game_state is None:
            return "Регион"

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return "Регион"

        return region.name

    def get_region_status_lines(self):
        if self.game_state is None:
            return []

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return []

        status_lines = [
            f"{texts.REGION_INFLUENCE_PLAYER}: {region.player_influence}",
            f"{texts.REGION_INFLUENCE_ENEMY}: {region.enemy_influence}",
        ]

        if region.unlocked and region.assault_unlocked:
            status_lines.append(texts.ASSAULT_READY)
        else:
            status_lines.append(texts.ASSAULT_LOCKED)

        if region.liberated:
            status_lines.append(texts.REGION_LIBERATED)

        return status_lines

    def get_current_region_id(self):
        if self.game_state is None:
            return None

        return self.game_state.current_region_id

    def is_assault_unlocked(self):
        if self.game_state is None:
            return False

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return False

        return region.unlocked and region.assault_unlocked

    def request_castle_assault(self):
        if not self.is_assault_unlocked():
            return False

        if self.manager is not None:
            self.manager.request_change(settings.CASTLE_ASSAULT_SCENE)
        return True

    def restart_region(self):
        self.tile_map = TileMap(self.create_test_map())
        self.camera = Camera(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        player_x, player_y = self.tile_map.coord_tile_to_pixels(*self.player_spawn_tile)

        self.ecs_player_id = self.entity_factory.create_player(
            x=player_x,
            y=player_y,
        )
        self.check_entity_components(self.ecs_player_id, "ECS player", Position, Health)

        self.enemy_ids = [
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 6,
                y=settings.TILE_SIZE * 6,
            ),
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 18,
                y=settings.TILE_SIZE * 10,
            ),
            self.entity_factory.create_enemy(
                x=settings.TILE_SIZE * 38,
                y=settings.TILE_SIZE * 20,
            ),
        ]
        self.enemy_id = self.enemy_ids[0]
        self.add_patrol_routes()

        for enemy_id in self.enemy_ids:
            self.check_entity_components(enemy_id, "ECS enemy", Position, Health)

        self.outpost_id = self.entity_factory.create_outpost(
            x=settings.TILE_SIZE * 8,
            y=settings.TILE_SIZE * 6,
        )
        self.check_entity_components(self.outpost_id, "ECS outpost", Position, Outpost)

        self.npc_id = self.entity_factory.create_npc(
            x=settings.TILE_SIZE * 4,
            y=settings.TILE_SIZE * 6,
            quest_id="clear_old_ruins_outpost",
            required_outpost_id=self.outpost_id,
        )
        self.check_entity_components(self.npc_id, "NPC", Position, NPC)
        self.validate_region_layout()
        self.update_camera()

    def get_entity_tile(self, entity_id):
        position = self.ecm.get_component(entity_id, Position)

        if position is None:
            return None

        collider = self.ecm.get_component(entity_id, Collider)

        if collider is None:
            return self.tile_map.coord_pixels_to_tile(position.x, position.y)

        return self.tile_map.coord_pixels_to_tile(
            position.x + collider.width / 2,
            position.y + collider.height / 2,
        )

    def validate_region_layout(self):
        start_tile = self.get_entity_tile(self.ecs_player_id)
        target_tiles = []

        for enemy_id in self.enemy_ids:
            enemy_tile = self.get_entity_tile(enemy_id)

            if enemy_tile is not None:
                target_tiles.append(enemy_tile)

            patrol_route = self.ecm.get_component(enemy_id, PatrolRoute)

            if patrol_route is not None:
                target_tiles.extend(patrol_route.patrol_tiles)

        outpost_tile = self.get_entity_tile(self.outpost_id)
        npc_tile = self.get_entity_tile(self.npc_id)

        if outpost_tile is not None:
            target_tiles.append(outpost_tile)

        if npc_tile is not None:
            target_tiles.append(npc_tile)

        if not are_tiles_reachable(self.tile_map, start_tile, target_tiles):
            raise ValueError("Region layout has unreachable important tiles")

    def add_patrol_routes(self):
        patrol_routes = [
            [(6, 6), (6, 9), (9, 9), (9, 6)],
            [(18, 10), (22, 10), (22, 12), (18, 12)],
            [(38, 20), (42, 20), (42, 22), (38, 22)],
        ]

        for enemy_id, patrol_tiles in zip(self.enemy_ids, patrol_routes):
            self.ecm.add_component(
                enemy_id,
                PatrolRoute(
                    patrol_tiles=patrol_tiles,
                    wait_duration=0.2,
                ),
            )

    def update_camera(self):
        player_position = self.ecm.get_component(self.ecs_player_id, Position)
        player_collider = self.ecm.get_component(self.ecs_player_id, Collider)

        if player_position is None:
            return

        if player_collider is None:
            center_x = player_position.x + settings.TILE_SIZE / 2
            center_y = player_position.y + settings.TILE_SIZE / 2
        else:
            center_x = player_position.x + player_collider.width / 2
            center_y = player_position.y + player_collider.height / 2

        self.camera.follow(
            center_x,
            center_y,
            self.tile_map.width * self.tile_map.tile_size,
            self.tile_map.height * self.tile_map.tile_size,
        )

    def respawn_player_after_defeat(self):
        player_health = self.ecm.get_component(self.ecs_player_id, Health)
        player_position = self.ecm.get_component(self.ecs_player_id, Position)
        player_velocity = self.ecm.get_component(self.ecs_player_id, Velocity)
        attack_intent = self.ecm.get_component(self.ecs_player_id, AttackIntent)
        attack_hitbox = self.ecm.get_component(self.ecs_player_id, AttackHitbox)

        if player_health is not None:
            player_health.current = player_health.maximum

        if player_position is not None:
            player_position.x, player_position.y = self.tile_map.coord_tile_to_pixels(
                *self.player_spawn_tile,
            )

        if player_velocity is not None:
            player_velocity.x = 0
            player_velocity.y = 0

        self.ecm.remove_component(self.ecs_player_id, PlayerDefeated)

        if attack_intent is not None:
            attack_intent.requested = False

        if attack_hitbox is not None:
            attack_hitbox.active = False
            attack_hitbox.x = 0
            attack_hitbox.y = 0
            attack_hitbox.width = 0
            attack_hitbox.height = 0
            attack_hitbox.timer = 0
            attack_hitbox.hit_landed = False

        self.enemy_chase_system.clear_path_cache()
        self.enemy_chase_system.clear_ai_memory()
        self.enemy_chase_system.stop_enemies(self.ecm)
        self.update_camera()

    def update(self, dt, input_manager):
        self.current_dt = dt

        if input_manager.was_pressed(settings.DEBUG):
            self.debug_overlay.toggle()

        if input_manager.was_pressed(settings.PAUSE):
            self.request_pause()
            return

        if input_manager.was_pressed(settings.OPEN_WORLD_MAP):
            self.request_world_map()
            return

        if (
            input_manager.was_pressed(settings.START_ASSAULT)
            and self.request_castle_assault()
        ):
            return

        if self.is_player_defeated():
            if input_manager.was_pressed(settings.RESTART):
                self.respawn_player_after_defeat()
            return

        self.player_input_system.update(self.ecm, input_manager)
        self.player_attack_input_system.update(self.ecm, input_manager)
        self.enemy_chase_system.update(self.ecm, self.tile_map, dt)
        previous_positions = self.movement_system.update(self.ecm, dt)
        self.collision_system.update(self.ecm, self.tile_map, previous_positions)
        self.melee_attack_system.update(self.ecm, dt, self.tile_map)
        self.enemy_death_system.update(self.ecm, self.get_current_region_id())
        self.enemy_attack_system.update(self.ecm, dt)
        self.player_death_system.update(self.ecm)

        if not self.is_player_defeated():
            self.outpost_system.update(
                self.ecm,
                input_manager,
                self.get_current_region_id(),
                dt,
            )
            self.npc_interaction_system.update(
                self.ecm,
                input_manager,
                self.get_current_region_id(),
                dt,
            )

        self.cleanup_system.update(self.ecm)
        self.update_camera()

    def get_contextual_prompts(self):
        prompts = []

        if self.is_assault_unlocked():
            prompts.append(texts.CASTLE_ASSAULT_START)

        player_position = self.ecm.get_component(self.ecs_player_id, Position)

        if player_position is None:
            return prompts

        self.add_outpost_prompt(prompts, player_position)
        self.add_npc_prompt(prompts, player_position)
        return prompts

    def add_outpost_prompt(self, prompts, player_position):
        outpost = self.ecm.get_component(self.outpost_id, Outpost)
        outpost_position = self.ecm.get_component(self.outpost_id, Position)

        if outpost is None or outpost_position is None:
            return

        if self.get_distance(player_position, outpost_position) > outpost.radius:
            return

        if outpost.cleared:
            prompts.append(texts.OUTPOST_CLEARED)
            return

        if self.outpost_system.has_living_enemy_near_outpost(
            self.ecm,
            outpost_position,
            outpost.radius,
        ):
            prompts.append(texts.OUTPOST_CLEAR_ENEMIES)
        elif outpost.clear_progress > 0:
            prompts.append(
                texts.OUTPOST_CLEAR_PROGRESS.format(
                    percent=self.get_progress_percent(
                        outpost.clear_progress,
                        outpost.clear_duration,
                    )
                )
            )
        else:
            prompts.append(texts.OUTPOST_HOLD_TO_CLEAR)

    def add_npc_prompt(self, prompts, player_position):
        npc = self.ecm.get_component(self.npc_id, NPC)
        npc_position = self.ecm.get_component(self.npc_id, Position)

        if npc is None or npc_position is None:
            return

        if self.get_distance(player_position, npc_position) > npc.interaction_radius:
            return

        if npc.quest_completed:
            prompts.append(texts.NPC_QUEST_COMPLETED)
            return

        outpost = self.ecm.get_component(npc.required_outpost_id, Outpost)

        if outpost is not None and outpost.cleared:
            if npc.report_progress > 0:
                prompts.append(
                    texts.NPC_REPORT_PROGRESS.format(
                        percent=self.get_progress_percent(
                            npc.report_progress,
                            npc.report_duration,
                        )
                    )
                )
            else:
                prompts.append(texts.NPC_HOLD_TO_REPORT)
        else:
            prompts.append(texts.NPC_CLEAR_OUTPOST_FIRST)

    def get_progress_percent(self, progress, duration):
        if duration <= 0:
            return 100

        return min(100, int(100 * progress / duration))

    def get_distance(self, first_position, second_position):
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def draw(self, screen: pygame.Surface):
        self.tile_map.draw(screen, self.camera)
        self.render_system.draw(self.ecm, screen, self.camera)
        self.render_system.draw_attack_hitboxes(self.ecm, screen, self.camera)
        self.render_system.draw_enemy_health_bars(self.ecm, screen, self.camera)
        self.hud.draw(
            screen,
            self.ecm,
            self.ecs_player_id,
            self.get_region_title(),
            self.get_contextual_prompts(),
            status_lines=self.get_region_status_lines(),
        )
        if self.is_player_defeated():
            self.hud.draw_defeat_message(screen, texts.DEFEATED_RECOVER)
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
