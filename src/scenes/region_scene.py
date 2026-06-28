import pygame
import settings
from src.algorithms.flood_fill import are_tiles_reachable
from src.components.components import (
    AttackHitbox,
    AttackIntent,
    Collider,
    Dead,
    Health,
    NPC,
    Outpost,
    PatrolRoute,
    PlayerDefeated,
    Position,
    Renderable,
    Velocity,
)
from src.core.camera import Camera
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entities_settings import NPCSettings, OutpostSettings
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
from src.systems.spatial_index_system import SpatialIndexSystem
from src.systems.visual_effect_system import VisualEffectSystem
from src.ui import texts
from src.ui.debug_overlay import DebugOverlay
from src.ui.hud import HUD
from src.world.region_layout import create_old_ruins_region_layout
from src.world.tile_map import TileMap


class RegionScene(BaseScene):
    """Запускает региональную сцену с игроком, врагами и объектами прогресса.

    """

    def __init__(
        self,
        game_state=None,
        event_bus=None,
        region_layout=None,
        resource_manager=None,
    ) -> None:
        """Инициализирует `RegionScene` и сохраняет начальные зависимости.

        Args:
            game_state: Глобальное состояние мира, регионов и прогресса игрока.
            event_bus: Шина событий для связи систем без прямых зависимостей.
            region_layout: Описание карты региона, точек интереса и стартовых позиций.
            resource_manager: Менеджер графических ресурсов и placeholder-изображений.

        Returns:
            None.
        """
        self.game_state = game_state
        self.event_bus = event_bus
        self.region_layout = region_layout or create_old_ruins_region_layout()
        self.resource_manager = resource_manager
        self.player_input_system = PlayerInputSystem()
        self.player_attack_input_system = PlayerAttackInputSystem()
        self.enemy_chase_system = EnemyChaseSystem()
        self.movement_system = MovementSystem()
        self.collision_system = CollisionSystem()
        self.visual_effect_system = VisualEffectSystem()
        self.melee_attack_system = MeleeAttackSystem(self.visual_effect_system)
        self.enemy_death_system = EnemyDeathSystem(self.event_bus)
        self.outpost_system = OutpostSystem(self.event_bus)
        self.npc_interaction_system = NPCInteractionSystem(self.event_bus)
        self.enemy_attack_system = EnemyAttackSystem()
        self.player_death_system = PlayerDeathSystem()
        self.spatial_index_system = SpatialIndexSystem()
        self.cleanup_system = CleanupSystem()
        self.render_system = RenderSystem(self.resource_manager)
        self.hud = HUD()
        self.debug_overlay = DebugOverlay()
        self.current_dt = 0
        self.manager = None
        self.enemy_spatial_index = None
        self.restart_region()

    def check_entity_components(self, entity_id, entity_name, *component_types):
        """Проверяет обязательные компоненты сущности.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.
            entity_name: Человекочитаемое имя сущности для диагностики.
            *component_types: Типы компонентов, наличие которых нужно проверить.

        Returns:
            None.
        """
        for component_type in component_types:
            component = self.ecm.get_component(entity_id, component_type)
            if component is None:
                raise RuntimeError(
                    f"{entity_name} was created without {component_type.__name__} component"
                )

    def handle_events(self, events):
        """Обрабатывает события текущего кадра.

        Args:
            events: Список событий PyGame за текущий кадр.

        Returns:
            None.
        """
        pass

    def is_player_defeated(self):
        """Проверяет, побежден ли игрок.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return self.ecm.has_component(self.ecs_player_id, PlayerDefeated)

    def request_world_map(self):
        """Запрашивает переход на карту мира.

        Returns:
            None.
        """
        if self.manager is not None:
            if hasattr(self.manager, "open_world_map"):
                self.manager.open_world_map(return_scene=self)
            else:
                self.manager.request_change(settings.WORLD_MAP_SCENE)

    def request_pause(self):
        """Запрашивает переход в сцену паузы.

        Returns:
            None.
        """
        if self.manager is not None:
            self.manager.request_pause(settings.PAUSE_SCENE)

    def get_region_title(self):
        """Возвращает регион заголовок.

        Returns:
            Найденное или вычисленное значение: регион заголовок.
        """
        if self.game_state is None:
            return "Регион"

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return "Регион"

        return region.name

    def get_region_status_lines(self):
        """Возвращает регион статус lines.

        Returns:
            Найденное или вычисленное значение: регион статус lines.
        """
        if self.game_state is None:
            return []

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return []

        status_lines = [
            f"{texts.REGION_INFLUENCE_PLAYER}: {region.player_influence}",
            f"{texts.REGION_INFLUENCE_ENEMY}: {region.enemy_influence}",
            texts.REGION_OUTPOSTS_STATUS.format(
                cleared=self.get_cleared_outpost_count(),
                total=len(self.outpost_ids),
            ),
            texts.REGION_QUESTS_STATUS.format(
                completed=self.get_completed_npc_count(),
                total=len(self.npc_ids),
            ),
            texts.REGION_ENEMIES_STATUS.format(
                alive=self.get_alive_enemy_count(),
                total=len(self.enemy_ids),
            ),
        ]

        if region.unlocked and region.assault_unlocked:
            status_lines.append(texts.ASSAULT_READY)
        else:
            status_lines.append(texts.ASSAULT_LOCKED)

        if region.liberated:
            status_lines.append(texts.REGION_LIBERATED)

        return status_lines

    def get_cleared_outpost_count(self):
        """Возвращает cleared аванпост count.

        Returns:
            Найденное или вычисленное значение: cleared аванпост count.
        """
        count = 0

        for outpost_id in self.outpost_ids:
            outpost = self.ecm.get_component(outpost_id, Outpost)
            if outpost is not None and outpost.cleared:
                count += 1

        return count

    def get_completed_npc_count(self):
        """Возвращает completed NPC count.

        Returns:
            Найденное или вычисленное значение: completed NPC count.
        """
        count = 0

        for npc_id in self.npc_ids:
            npc = self.ecm.get_component(npc_id, NPC)
            if npc is not None and npc.quest_completed:
                count += 1

        return count

    def get_alive_enemy_count(self):
        """Возвращает alive враг count.

        Returns:
            Найденное или вычисленное значение: alive враг count.
        """
        count = 0

        for enemy_id in self.enemy_ids:
            if self.is_enemy_alive(enemy_id):
                count += 1

        return count

    def is_enemy_alive(self, enemy_id):
        """Проверяет, жив ли враг.

        Args:
            enemy_id: Идентификатор сущности врага.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if enemy_id not in self.ecm.alive_entities:
            return False

        if self.ecm.has_component(enemy_id, Dead):
            return False

        enemy_health = self.ecm.get_component(enemy_id, Health)

        if enemy_health is not None and enemy_health.current <= 0:
            return False

        return True

    def get_current_region_id(self):
        """Возвращает текущий регион id.

        Returns:
            Найденное или вычисленное значение: текущий регион id.
        """
        if self.game_state is None:
            return None

        return self.game_state.current_region_id

    def is_assault_unlocked(self):
        """Проверяет, открыт ли штурм региона.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        if self.game_state is None:
            return False

        region = self.game_state.get_region(self.game_state.current_region_id)

        if region is None:
            return False

        return region.unlocked and region.assault_unlocked

    def request_castle_assault(self):
        """Запрашивает переход к штурму замка.

        Returns:
            Результат выполнения `request_castle_assault`.
        """
        if not self.is_assault_unlocked():
            return False

        if self.manager is not None:
            self.manager.request_change(settings.CASTLE_ASSAULT_SCENE)
        return True

    def restart_region(self):
        """Перезапускает текущий регион.

        Returns:
            None.
        """
        self.enemy_spatial_index = None
        self.tile_map = TileMap(self.region_layout.matrix)
        self.camera = Camera(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.ecm = EntityComponentManager()
        self.entity_factory = EntityFactory(self.ecm)
        self.player_spawn_tile = self.region_layout.player_spawn_tile
        self.enemy_ids = []
        self.outpost_ids = []
        self.npc_ids = []
        self.outpost_entity_by_key = {}
        self.npc_entity_by_key = {}
        self.outpost_key_by_entity_id = {}
        self.npc_key_by_entity_id = {}
        player_x, player_y = self.tile_map.coord_tile_to_pixels(*self.player_spawn_tile)

        self.ecs_player_id = self.entity_factory.create_player(
            x=player_x,
            y=player_y,
        )
        self.check_entity_components(self.ecs_player_id, "ECS player", Position, Health)

        for enemy_spawn in self.region_layout.enemy_spawns:
            enemy_x, enemy_y = self.tile_map.coord_tile_to_pixels(*enemy_spawn.tile)
            enemy_id = self.entity_factory.create_enemy(x=enemy_x, y=enemy_y)
            self.enemy_ids.append(enemy_id)
            self.ecm.add_component(
                enemy_id,
                PatrolRoute(
                    patrol_tiles=list(enemy_spawn.patrol_tiles),
                    wait_duration=0.2,
                ),
            )

        self.enemy_id = self.enemy_ids[0] if self.enemy_ids else None

        for enemy_id in self.enemy_ids:
            self.check_entity_components(enemy_id, "ECS enemy", Position, Health)

        for outpost_spawn in self.region_layout.outposts:
            outpost_x, outpost_y = self.tile_map.coord_tile_to_pixels(*outpost_spawn.tile)
            outpost_id = self.entity_factory.create_outpost(x=outpost_x, y=outpost_y)
            self.outpost_ids.append(outpost_id)
            self.outpost_entity_by_key[outpost_spawn.key] = outpost_id
            self.outpost_key_by_entity_id[outpost_id] = outpost_spawn.key
            self.check_entity_components(outpost_id, "ECS outpost", Position, Outpost)

        self.outpost_id = self.outpost_ids[0] if self.outpost_ids else None

        for npc_spawn in self.region_layout.npcs:
            npc_x, npc_y = self.tile_map.coord_tile_to_pixels(*npc_spawn.tile)
            required_outpost_id = None
            if npc_spawn.required_outpost_key is not None:
                required_outpost_id = self.outpost_entity_by_key.get(
                    npc_spawn.required_outpost_key
                )
            npc_id = self.entity_factory.create_npc(
                x=npc_x,
                y=npc_y,
                quest_id=npc_spawn.quest_id,
                required_outpost_id=required_outpost_id,
            )
            self.npc_ids.append(npc_id)
            self.npc_entity_by_key[npc_spawn.key] = npc_id
            self.npc_key_by_entity_id[npc_id] = npc_spawn.key
            self.check_entity_components(npc_id, "NPC", Position, NPC)

        self.npc_id = self.npc_ids[0] if self.npc_ids else None
        self.validate_region_layout()
        self.update_camera()

    def rebuild_enemy_spatial_index(self):
        """Пересобирает пространственный индекс живых врагов.

        Returns:
            None.
        """
        self.enemy_spatial_index = self.spatial_index_system.build_enemy_index(
            self.ecm,
            self.tile_map.width * self.tile_map.tile_size,
            self.tile_map.height * self.tile_map.tile_size,
            settings.TILE_SIZE * 4,
        )

    def get_entity_tile(self, entity_id):
        """Возвращает сущность тайл.

        Args:
            entity_id: Идентификатор сущности в EntityComponentManager.

        Returns:
            Найденное или вычисленное значение: сущность тайл.
        """
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
        """Проверяет корректность layout региона.

        Returns:
            None.
        """
        start_tile = self.get_entity_tile(self.ecs_player_id)
        target_tiles = []

        self.validate_region_content_counts()
        self.validate_region_map_size()
        self.validate_region_tile_variety()
        self.validate_important_tile(start_tile, "player spawn")

        for enemy_id in self.enemy_ids:
            enemy_tile = self.get_entity_tile(enemy_id)

            if enemy_tile is not None:
                self.validate_important_tile(enemy_tile, "enemy spawn")
                target_tiles.append(enemy_tile)

            patrol_route = self.ecm.get_component(enemy_id, PatrolRoute)

            if patrol_route is not None:
                for patrol_tile in patrol_route.patrol_tiles:
                    self.validate_important_tile(patrol_tile, "enemy patrol")
                target_tiles.extend(patrol_route.patrol_tiles)

        for outpost_id in self.outpost_ids:
            outpost_tile = self.get_entity_tile(outpost_id)

            if outpost_tile is not None:
                self.validate_important_tile(outpost_tile, "outpost")
                self.validate_not_near_spawn(outpost_tile, "outpost")
                self.validate_outpost_guarded(outpost_tile)
                target_tiles.append(outpost_tile)

        for npc_id in self.npc_ids:
            npc_tile = self.get_entity_tile(npc_id)

            if npc_tile is not None:
                self.validate_important_tile(npc_tile, "npc")
                self.validate_not_near_spawn(npc_tile, "npc")
                target_tiles.append(npc_tile)

        if not are_tiles_reachable(self.tile_map, start_tile, target_tiles):
            raise ValueError("Region layout has unreachable important tiles")

    def validate_region_content_counts(self):
        """Проверяет количество ключевых объектов региона.

        Returns:
            None.
        """
        if len(self.outpost_ids) < 2:
            raise ValueError("Region layout must have at least two outposts")
        if len(self.npc_ids) < 2:
            raise ValueError("Region layout must have at least two NPCs")
        if len(self.enemy_ids) < 7:
            raise ValueError("Region layout must have at least seven enemies")

    def validate_region_map_size(self):
        """Проверяет размер карты региона.

        Returns:
            None.
        """
        screen_tiles_width = settings.SCREEN_WIDTH // settings.TILE_SIZE
        screen_tiles_height = settings.SCREEN_HEIGHT // settings.TILE_SIZE

        if (
            self.tile_map.width <= screen_tiles_width
            or self.tile_map.height <= screen_tiles_height
        ):
            raise ValueError("Region layout must be larger than the viewport")

    def validate_region_tile_variety(self):
        """Проверяет разнообразие тайлов региона.

        Returns:
            None.
        """
        tile_types = {
            tile
            for row in self.tile_map.matrix
            for tile in row
        }

        if len(tile_types) < 5:
            raise ValueError("Region layout must use at least five tile types")

    def validate_important_tile(self, tile, label):
        """Проверяет важный тайл региона.

        Args:
            tile: Координаты тайла в формате `(x, y)`.
            label: Человекочитаемая подпись для ошибки или проверки.

        Returns:
            None.
        """
        if tile is None or self.tile_map.is_tile_blocked(*tile):
            raise ValueError(f"Region layout has blocked important tile: {label}")

    def validate_not_near_spawn(self, tile, label):
        """Проверяет выполнение условия: validate not near появление.

        Args:
            tile: Координаты тайла в формате `(x, y)`.
            label: Человекочитаемая подпись для ошибки или проверки.

        Returns:
            None.
        """
        if self.get_tile_distance(tile, self.player_spawn_tile) <= 4:
            raise ValueError(f"Region layout {label} is too close to player spawn")

    def validate_outpost_guarded(self, outpost_tile):
        """Проверяет выполнение условия: validate аванпост guarded.

        Args:
            outpost_tile: Координаты тайла аванпоста.

        Returns:
            None.
        """
        guard_radius_tiles = max(1, OutpostSettings.RADIUS // settings.TILE_SIZE)

        for enemy_id in self.enemy_ids:
            enemy_tile = self.get_entity_tile(enemy_id)

            if (
                enemy_tile is not None
                and self.get_tile_distance(enemy_tile, outpost_tile) <= guard_radius_tiles
            ):
                return

        raise ValueError("Region layout outpost has no nearby enemy guard")

    def get_tile_distance(self, first_tile, second_tile):
        """Возвращает тайл дистанция.

        Args:
            first_tile: Координаты первого тайла.
            second_tile: Координаты второго тайла.

        Returns:
            Найденное или вычисленное значение: тайл дистанция.
        """
        first_x, first_y = first_tile
        second_x, second_y = second_tile
        return abs(first_x - second_x) + abs(first_y - second_y)

    def update_camera(self):
        """Обновляет камера.

        Returns:
            None.
        """
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
        """Возрождает игрока после поражения и сбрасывает его боевое состояние.

        Returns:
            None.
        """
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

    def export_runtime_state(self):
        """Собирает runtime-состояние сцены для сохранения.

        Returns:
            Словарь runtime-состояния сцены.
        """
        defeated_enemy_indexes = []

        for index, enemy_id in enumerate(self.enemy_ids):
            if enemy_id not in self.ecm.alive_entities:
                defeated_enemy_indexes.append(index)
                continue

            enemy_health = self.ecm.get_component(enemy_id, Health)

            if self.ecm.has_component(enemy_id, Dead):
                defeated_enemy_indexes.append(index)
            elif enemy_health is not None and enemy_health.current <= 0:
                defeated_enemy_indexes.append(index)

        cleared_outpost_keys = []
        completed_npc_keys = []

        for outpost_id in self.outpost_ids:
            outpost = self.ecm.get_component(outpost_id, Outpost)
            outpost_key = self.outpost_key_by_entity_id.get(outpost_id)

            if outpost is not None and outpost.cleared and outpost_key is not None:
                cleared_outpost_keys.append(outpost_key)

        for npc_id in self.npc_ids:
            npc = self.ecm.get_component(npc_id, NPC)
            npc_key = self.npc_key_by_entity_id.get(npc_id)

            if npc is not None and npc.quest_completed and npc_key is not None:
                completed_npc_keys.append(npc_key)

        player_position = self.ecm.get_component(self.ecs_player_id, Position)
        player_health = self.ecm.get_component(self.ecs_player_id, Health)

        player_state = {}

        if player_position is not None:
            player_state["x"] = player_position.x
            player_state["y"] = player_position.y

        if player_health is not None:
            player_state["health"] = player_health.current

        return {
            "defeated_enemy_indexes": defeated_enemy_indexes,
            "cleared_outpost_keys": cleared_outpost_keys,
            "completed_npc_keys": completed_npc_keys,
            "player": player_state,
        }

    def apply_runtime_state(self, runtime_state):
        """Применяет runtime-состояние сцены после загрузки.

        Args:
            runtime_state: Сохраненное runtime-состояние сцены региона.

        Returns:
            None.
        """
        if not runtime_state:
            return

        for enemy_index in runtime_state.get("defeated_enemy_indexes", []):
            if enemy_index < 0 or enemy_index >= len(self.enemy_ids):
                continue

            enemy_id = self.enemy_ids[enemy_index]

            if enemy_id in self.ecm.alive_entities:
                self.ecm.destroy_entity(enemy_id)

        cleared_outpost_keys = runtime_state.get("cleared_outpost_keys", [])

        for outpost_key in cleared_outpost_keys:
            outpost_id = self.outpost_entity_by_key.get(outpost_key)
            if outpost_id is not None:
                self.apply_outpost_runtime_state(outpost_id)

        if runtime_state.get("outpost_cleared") and self.outpost_id is not None:
            self.apply_outpost_runtime_state(self.outpost_id)

        completed_npc_keys = runtime_state.get("completed_npc_keys", [])

        for npc_key in completed_npc_keys:
            npc_id = self.npc_entity_by_key.get(npc_key)
            if npc_id is not None:
                self.apply_npc_runtime_state(npc_id)

        if runtime_state.get("npc_quest_completed") and self.npc_id is not None:
            self.apply_npc_runtime_state(self.npc_id)

        self.apply_player_runtime_state(runtime_state.get("player", {}))
        self.update_camera()

    def apply_outpost_runtime_state(self, outpost_id=None):
        """Применяет аванпост runtime состояние.

        Args:
            outpost_id: Идентификатор сущности аванпоста.

        Returns:
            None.
        """
        if outpost_id is None:
            outpost_id = self.outpost_id

        outpost = self.ecm.get_component(outpost_id, Outpost)
        renderable = self.ecm.get_component(outpost_id, Renderable)

        if outpost is not None:
            outpost.cleared = True
            outpost.clear_progress = outpost.clear_duration

        if renderable is not None:
            renderable.color = OutpostSettings.CLEARED_COLOR

    def apply_npc_runtime_state(self, npc_id=None):
        """Применяет NPC runtime состояние.

        Args:
            npc_id: Идентификатор сущности NPC.

        Returns:
            None.
        """
        if npc_id is None:
            npc_id = self.npc_id

        npc = self.ecm.get_component(npc_id, NPC)
        renderable = self.ecm.get_component(npc_id, Renderable)

        if npc is not None:
            npc.quest_completed = True
            npc.report_progress = npc.report_duration

        if renderable is not None:
            renderable.color = NPCSettings.COMPLETED_COLOR

    def apply_player_runtime_state(self, player_state):
        """Применяет игрок runtime состояние.

        Args:
            player_state: Сохраненное runtime-состояние игрока.

        Returns:
            None.
        """
        if not player_state:
            return

        player_position = self.ecm.get_component(self.ecs_player_id, Position)
        player_health = self.ecm.get_component(self.ecs_player_id, Health)

        if player_position is not None:
            if "x" in player_state:
                player_position.x = player_state["x"]
            if "y" in player_state:
                player_position.y = player_state["y"]

        if player_health is not None and "health" in player_state:
            player_health.current = max(
                1,
                min(player_health.maximum, player_state["health"]),
            )

            self.ecm.remove_component(self.ecs_player_id, PlayerDefeated)

    def update(self, dt, input_manager):
        """Обновляет состояние объекта за один кадр.

        Args:
            dt: Время, прошедшее с предыдущего кадра, в секундах.
            input_manager: Менеджер ввода, который хранит состояние клавиш и мыши.

        Returns:
            None.
        """
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
            else:
                self.visual_effect_system.update(self.ecm, dt)
            return

        self.visual_effect_system.update(self.ecm, dt)
        self.player_input_system.update(self.ecm, input_manager)
        self.player_attack_input_system.update(self.ecm, input_manager)
        self.enemy_chase_system.update(self.ecm, self.tile_map, dt)
        previous_positions = self.movement_system.update(self.ecm, dt)
        self.collision_system.update(self.ecm, self.tile_map, previous_positions)
        self.rebuild_enemy_spatial_index()
        self.melee_attack_system.update(
            self.ecm,
            dt,
            self.tile_map,
            self.enemy_spatial_index,
        )
        self.enemy_death_system.update(self.ecm, self.get_current_region_id())
        self.enemy_attack_system.update(self.ecm, dt, self.enemy_spatial_index)
        self.player_death_system.update(self.ecm)

        if not self.is_player_defeated():
            self.outpost_system.update(
                self.ecm,
                input_manager,
                self.get_current_region_id(),
                dt,
                self.enemy_spatial_index,
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
        """Возвращает контекстные prompts.

        Returns:
            Найденное или вычисленное значение: контекстные prompts.
        """
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
        """Добавляет аванпост prompt.

        Args:
            prompts: Список контекстных подсказок HUD.
            player_position: Позиция игрока в пикселях.

        Returns:
            None.
        """
        outpost_id = self.get_nearest_outpost_id(player_position)

        if outpost_id is None:
            return

        outpost = self.ecm.get_component(outpost_id, Outpost)
        outpost_position = self.ecm.get_component(outpost_id, Position)

        if outpost is None or outpost_position is None:
            return

        if outpost.cleared:
            prompts.append(texts.OUTPOST_CLEARED)
            return

        if self.outpost_system.has_living_enemy_near_outpost(
            self.ecm,
            outpost_position,
            outpost.radius,
            self.enemy_spatial_index,
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
        """Добавляет NPC prompt.

        Args:
            prompts: Список контекстных подсказок HUD.
            player_position: Позиция игрока в пикселях.

        Returns:
            None.
        """
        npc_id = self.get_nearest_npc_id(player_position)

        if npc_id is None:
            return

        npc = self.ecm.get_component(npc_id, NPC)
        npc_position = self.ecm.get_component(npc_id, Position)

        if npc is None or npc_position is None:
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

    def get_nearest_outpost_id(self, player_position):
        """Возвращает nearest аванпост id.

        Args:
            player_position: Позиция игрока в пикселях.

        Returns:
            Найденное или вычисленное значение: nearest аванпост id.
        """
        nearest_outpost_id = None
        nearest_distance = None

        for outpost_id in self.outpost_ids:
            outpost = self.ecm.get_component(outpost_id, Outpost)
            outpost_position = self.ecm.get_component(outpost_id, Position)

            if outpost is None or outpost_position is None:
                continue

            distance = self.get_distance(player_position, outpost_position)

            if distance > outpost.radius:
                continue

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_outpost_id = outpost_id

        return nearest_outpost_id

    def get_nearest_npc_id(self, player_position):
        """Возвращает nearest NPC id.

        Args:
            player_position: Позиция игрока в пикселях.

        Returns:
            Найденное или вычисленное значение: nearest NPC id.
        """
        nearest_npc_id = None
        nearest_distance = None

        for npc_id in self.npc_ids:
            npc = self.ecm.get_component(npc_id, NPC)
            npc_position = self.ecm.get_component(npc_id, Position)

            if npc is None or npc_position is None:
                continue

            distance = self.get_distance(player_position, npc_position)

            if distance > npc.interaction_radius:
                continue

            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_npc_id = npc_id

        return nearest_npc_id

    def get_progress_percent(self, progress, duration):
        """Возвращает прогресс percent.

        Args:
            progress: Текущий накопленный прогресс действия.
            duration: Длительность действия или таймера в секундах.

        Returns:
            Прогресс в процентах от 0 до 100.
        """
        if duration <= 0:
            return 100

        return min(100, int(100 * progress / duration))

    def get_distance(self, first_position, second_position):
        """Возвращает дистанция.

        Args:
            first_position: Позиция первого объекта в пикселях.
            second_position: Позиция второго объекта в пикселях.

        Returns:
            Расстояние между двумя позициями.
        """
        dx = second_position.x - first_position.x
        dy = second_position.y - first_position.y
        return (dx ** 2 + dy ** 2) ** 0.5

    def draw(self, screen: pygame.Surface):
        """Рисует объект на переданной поверхности.

        Args:
            screen: Поверхность PyGame, на которую выполняется отрисовка.

        Returns:
            None.
        """
        self.tile_map.draw(screen, self.camera, self.resource_manager)
        self.render_system.draw(self.ecm, screen, self.camera)
        self.render_system.draw_attack_hitboxes(self.ecm, screen, self.camera)
        self.visual_effect_system.draw(self.ecm, screen, self.camera)
        self.render_system.draw_enemy_health_bars(self.ecm, screen, self.camera)
        self.debug_overlay.draw(screen, self.ecm, self.ecs_player_id, self.tile_map, self.current_dt)
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
