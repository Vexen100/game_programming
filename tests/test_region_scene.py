import unittest
from unittest.mock import patch

import pygame
import settings

from src.components.components import (
    AttackHitbox,
    AttackIntent,
    ChaseBehavior,
    Enemy,
    FacingDirection,
    Health,
    MeleeAttack,
    NPC,
    Outpost,
    PatrolRoute,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Velocity,
)
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem
from src.ui import texts
from src.world.tile_types import FLOOR, WALL


class FakeSceneManager:
    def __init__(self):
        self.requested_scene_id = None
        self.pause_requested_scene_id = None
        self.world_map_return_scene = None

    def request_change(self, scene_id):
        self.requested_scene_id = scene_id

    def request_pause(self, scene_id):
        self.pause_requested_scene_id = scene_id

    def open_world_map(self, return_scene=None):
        self.requested_scene_id = settings.WORLD_MAP_SCENE
        self.world_map_return_scene = return_scene


class FakeInputManager:
    def was_pressed(self, action):
        return False

    def is_pressed(self, action):
        return False

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeAttackInputManager:
    def was_pressed(self, action):
        return action == settings.ATTACK

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeRestartInputManager:
    def was_pressed(self, action):
        return action == settings.RESTART

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeWorldMapInputManager:
    def was_pressed(self, action):
        return action == settings.OPEN_WORLD_MAP

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeInteractInputManager:
    def was_pressed(self, action):
        return action == settings.INTERACT

    def is_pressed(self, action):
        return action == settings.INTERACT

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakePauseInputManager:
    def was_pressed(self, action):
        return action == settings.PAUSE

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class FakeStartAssaultInputManager:
    def was_pressed(self, action):
        return action == settings.START_ASSAULT

    def get_velocity_direction(self):
        return pygame.Vector2(0, 0)


class TestRegionScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_region_scene_creates_player_and_enemy(self):
        scene = RegionScene()

        self.assertTrue(hasattr(scene, "ecs_player_id"))
        self.assertTrue(hasattr(scene, "enemy_id"))
        self.assertTrue(hasattr(scene, "enemy_ids"))
        self.assertTrue(hasattr(scene, "camera"))
        self.assertTrue(hasattr(scene, "enemy_chase_system"))
        self.assertTrue(hasattr(scene, "player_attack_input_system"))
        self.assertTrue(hasattr(scene, "melee_attack_system"))
        self.assertTrue(hasattr(scene, "enemy_death_system"))
        self.assertTrue(hasattr(scene, "outpost_system"))
        self.assertTrue(hasattr(scene, "npc_interaction_system"))
        self.assertTrue(hasattr(scene, "enemy_attack_system"))
        self.assertTrue(hasattr(scene, "player_death_system"))
        self.assertTrue(hasattr(scene, "cleanup_system"))
        self.assertTrue(hasattr(scene, "npc_id"))
        self.assertEqual(len(scene.enemy_ids), 3)
        self.assertEqual(scene.enemy_id, scene.enemy_ids[0])
        self.assertEqual(len(scene.ecm.alive_entities), 6)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackIntent))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, FacingDirection))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackHitbox))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, PatrolRoute))
        self.assertTrue(scene.ecm.has_component(scene.outpost_id, Outpost))
        self.assertTrue(scene.ecm.has_component(scene.npc_id, NPC))

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Health))
        self.assertTrue(scene.ecm.has_component(scene.outpost_id, Position))
        self.assertTrue(scene.ecm.has_component(scene.npc_id, Position))

    def test_region_scene_update_moves_enemy_towards_player(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_enemy_x = enemy_position.x
        old_enemy_y = enemy_position.y

        scene.update(0.1, FakeInputManager())

        self.assertLess(enemy_position.x, old_enemy_x)
        self.assertGreaterEqual(enemy_position.y, old_enemy_y)

    def test_region_scene_update_player_attack_damages_enemy(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_health = enemy_health.current

        scene.update(0.1, FakeAttackInputManager())

        self.assertLess(enemy_health.current, old_health)

    def test_region_scene_update_removes_dead_enemy_after_attack(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())

        self.assertNotIn(scene.enemy_id, scene.ecm.alive_entities)

    def test_region_scene_update_enemy_attack_damages_player(self):
        scene = RegionScene()

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_health = player_health.current

        scene.update(0.1, FakeInputManager())

        self.assertLess(player_health.current, old_health)

    def test_region_scene_marks_player_defeated_when_health_is_zero(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

    def test_region_scene_does_not_update_gameplay_when_player_defeated(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())

        old_x = player_position.x
        old_y = player_position.y

        scene.update(0.1, FakeInputManager())

        self.assertEqual(player_position.x, old_x)
        self.assertEqual(player_position.y, old_y)

    def test_region_scene_recover_after_defeat_keeps_current_ecm(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        old_ecm = scene.ecm
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

        scene.update(0.1, FakeRestartInputManager())

        new_player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        self.assertIs(scene.ecm, old_ecm)
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertEqual(new_player_health.current, new_player_health.maximum)

    def test_region_scene_recover_after_defeat_restores_spawn_position(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health.current = 0
        player_position.x = settings.TILE_SIZE * 20
        player_position.y = settings.TILE_SIZE * 20

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        spawn_x, spawn_y = scene.tile_map.coord_tile_to_pixels(*scene.player_spawn_tile)

        self.assertEqual(player_position.x, spawn_x)
        self.assertEqual(player_position.y, spawn_y)

    def test_region_scene_recover_after_defeat_resets_player_velocity_and_attack_state(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_velocity = scene.ecm.get_component(scene.ecs_player_id, Velocity)
        attack_intent = scene.ecm.get_component(scene.ecs_player_id, AttackIntent)
        attack_hitbox = scene.ecm.get_component(scene.ecs_player_id, AttackHitbox)
        player_health.current = 0
        player_velocity.x = 10
        player_velocity.y = 20
        attack_intent.requested = True
        attack_hitbox.active = True
        attack_hitbox.timer = 0.1
        attack_hitbox.hit_landed = True

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        self.assertEqual(player_velocity.x, 0)
        self.assertEqual(player_velocity.y, 0)
        self.assertFalse(attack_intent.requested)
        self.assertFalse(attack_hitbox.active)
        self.assertEqual(attack_hitbox.timer, 0)
        self.assertFalse(attack_hitbox.hit_landed)

    def test_region_scene_recover_after_defeat_preserves_outpost_cleared(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        outpost.cleared = True
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        self.assertTrue(outpost.cleared)

    def test_region_scene_recover_after_defeat_preserves_npc_quest_completed(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        npc = scene.ecm.get_component(scene.npc_id, NPC)
        npc.quest_completed = True
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        self.assertTrue(npc.quest_completed)

    def test_region_scene_recover_after_defeat_does_not_restore_removed_enemies(self):
        scene = RegionScene()

        removed_enemy_id = scene.enemy_id
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        scene.ecm.destroy_entity(removed_enemy_id)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        self.assertNotIn(removed_enemy_id, scene.ecm.alive_entities)

    def test_region_scene_recover_after_defeat_clears_enemy_ai_memory(self):
        scene = RegionScene()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0
        scene.enemy_chase_system.cached_paths[scene.enemy_id] = [(1, 1), (2, 1)]
        scene.enemy_chase_system.cached_goal_tiles[scene.enemy_id] = (2, 1)
        scene.enemy_chase_system.path_rebuild_timers[scene.enemy_id] = 0.5
        scene.enemy_chase_system.last_seen_player_tiles[scene.enemy_id] = (2, 1)
        scene.enemy_chase_system.last_seen_timers[scene.enemy_id] = 0.5

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeRestartInputManager())

        self.assertEqual(scene.enemy_chase_system.cached_paths, {})
        self.assertEqual(scene.enemy_chase_system.cached_goal_tiles, {})
        self.assertEqual(scene.enemy_chase_system.path_rebuild_timers, {})
        self.assertEqual(scene.enemy_chase_system.last_seen_player_tiles, {})
        self.assertEqual(scene.enemy_chase_system.last_seen_timers, {})

    def test_region_scene_uses_current_region_name_from_game_state(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = RegionScene(game_state)

        self.assertEqual(scene.get_region_title(), "Old Ruins")

    def test_region_scene_without_game_state_uses_default_title(self):
        scene = RegionScene()

        self.assertEqual(scene.get_region_title(), "Регион")

    def test_region_scene_status_lines_show_current_influence(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        region = game_state.get_region("old_ruins")
        region.player_influence = 25
        region.enemy_influence = 75
        scene = RegionScene(game_state)

        status_lines = scene.get_region_status_lines()

        self.assertIn(f"{texts.REGION_INFLUENCE_PLAYER}: 25", status_lines)
        self.assertIn(f"{texts.REGION_INFLUENCE_ENEMY}: 75", status_lines)
        self.assertIn(texts.ASSAULT_LOCKED, status_lines)

    def test_region_scene_status_lines_show_assault_ready_and_liberated(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        region = game_state.get_region("old_ruins")
        region.assault_unlocked = True
        region.liberated = True
        scene = RegionScene(game_state)

        status_lines = scene.get_region_status_lines()

        self.assertIn(texts.ASSAULT_READY, status_lines)
        self.assertIn(texts.REGION_LIBERATED, status_lines)

    def test_region_scene_enemy_death_publishes_influence_event(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())
        region = game_state.get_region("old_ruins")
        status_lines = scene.get_region_status_lines()

        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)
        self.assertIn(f"{texts.REGION_INFLUENCE_PLAYER}: 25", status_lines)
        self.assertIn(f"{texts.REGION_INFLUENCE_ENEMY}: 75", status_lines)

    def test_region_scene_open_world_map_requests_world_map_scene(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)
        self.assertIs(scene.manager.world_map_return_scene, scene)

    def test_region_scene_open_world_map_skips_gameplay_update(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_region_scene_open_world_map_without_manager_does_not_crash(self):
        scene = RegionScene()

        scene.update(0.1, FakeWorldMapInputManager())

    def test_region_scene_open_world_map_works_when_player_defeated(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))

        scene.update(0.1, FakeWorldMapInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.WORLD_MAP_SCENE)

    def test_region_scene_pause_requests_pause_scene(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakePauseInputManager())

        self.assertEqual(scene.manager.pause_requested_scene_id, settings.PAUSE_SCENE)

    def test_region_scene_pause_skips_gameplay_update(self):
        scene = RegionScene()
        scene.manager = FakeSceneManager()

        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        old_x = enemy_position.x
        old_y = enemy_position.y

        scene.update(0.1, FakePauseInputManager())

        self.assertEqual(enemy_position.x, old_x)
        self.assertEqual(enemy_position.y, old_y)

    def test_region_scene_pause_without_manager_does_not_crash(self):
        scene = RegionScene()

        scene.update(0.1, FakePauseInputManager())

    def test_region_influence_is_preserved_when_returning_to_world_map(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        enemy_health = scene.ecm.get_component(scene.enemy_id, Health)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6
        outpost_position.x = settings.TILE_SIZE * 20
        outpost_position.y = settings.TILE_SIZE * 20
        enemy_health.current = 10

        scene.update(0.1, FakeAttackInputManager())
        region = game_state.get_region("old_ruins")
        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)

        world_map_scene = WorldMapScene(game_state)
        status = world_map_scene.get_region_status_text(region)

        self.assertIn("игрок 25", status)
        self.assertIn("враг 75", status)

    def test_region_scene_outpost_clear_changes_influence(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)

        scene.update(outpost.clear_duration, FakeInteractInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(outpost.cleared)
        self.assertEqual(region.player_influence, 50)
        self.assertEqual(region.enemy_influence, 50)
        self.assertTrue(region.assault_unlocked)

    def test_region_scene_outpost_does_not_clear_without_interact(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        enemy_position.x = outpost_position.x + outpost.radius + settings.TILE_SIZE
        enemy_position.y = outpost_position.y

        scene.update(0.1, FakeInputManager())

        self.assertFalse(outpost.cleared)

    def test_region_scene_outpost_does_not_clear_when_player_health_is_zero(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        enemy_position.x = outpost_position.x + outpost.radius + settings.TILE_SIZE
        enemy_position.y = outpost_position.y
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertFalse(outpost.cleared)
        self.assertEqual(region.player_influence, 0)
        self.assertEqual(region.enemy_influence, 100)

    def test_region_scene_completes_npc_quest_after_outpost_cleared(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        npc_position = scene.ecm.get_component(scene.npc_id, Position)
        npc = scene.ecm.get_component(scene.npc_id, NPC)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        outpost.cleared = True
        player_position.x = npc_position.x
        player_position.y = npc_position.y

        scene.update(npc.report_duration, FakeInteractInputManager())
        region = game_state.get_region("old_ruins")

        self.assertTrue(npc.quest_completed)
        self.assertEqual(region.player_influence, 25)
        self.assertEqual(region.enemy_influence, 75)

    def test_region_scene_npc_quest_does_not_complete_before_outpost_cleared(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        npc_position = scene.ecm.get_component(scene.npc_id, Position)
        npc = scene.ecm.get_component(scene.npc_id, NPC)

        player_position.x = npc_position.x
        player_position.y = npc_position.y

        scene.update(0.1, FakeInteractInputManager())
        region = game_state.get_region("old_ruins")

        self.assertFalse(npc.quest_completed)
        self.assertEqual(region.player_influence, 0)
        self.assertEqual(region.enemy_influence, 100)

    def test_region_scene_start_assault_requests_castle_when_unlocked(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        region = game_state.get_region("old_ruins")
        region.assault_unlocked = True
        scene = RegionScene(game_state)
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertEqual(scene.manager.requested_scene_id, settings.CASTLE_ASSAULT_SCENE)

    def test_region_scene_start_assault_does_nothing_when_locked(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = RegionScene(game_state)
        scene.manager = FakeSceneManager()

        scene.update(0.1, FakeStartAssaultInputManager())

        self.assertIsNone(scene.manager.requested_scene_id)

    def test_region_scene_calls_enemy_chase_with_tile_map(self):
        scene = RegionScene()

        with patch.object(scene.enemy_chase_system, "update") as mock_update:
            scene.update(0.1, FakeInputManager())

        mock_update.assert_called_once_with(scene.ecm, scene.tile_map, 0.1)

    def test_region_scene_contextual_prompts_do_not_crash(self):
        scene = RegionScene()

        prompts = scene.get_contextual_prompts()

        self.assertIsInstance(prompts, list)

    def test_region_scene_contextual_prompts_show_outpost_hold_hint(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)

        prompts = scene.get_contextual_prompts()

        self.assertIn(texts.OUTPOST_HOLD_TO_CLEAR, prompts)

    def test_region_scene_contextual_prompts_show_outpost_progress(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)
        outpost.clear_progress = outpost.clear_duration / 2

        prompts = scene.get_contextual_prompts()

        self.assertIn(texts.OUTPOST_CLEAR_PROGRESS.format(percent=50), prompts)

    def test_region_scene_contextual_prompts_show_npc_hold_hint(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        npc_position = scene.ecm.get_component(scene.npc_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        outpost.cleared = True

        player_position.x = npc_position.x
        player_position.y = npc_position.y

        prompts = scene.get_contextual_prompts()

        self.assertIn(texts.NPC_HOLD_TO_REPORT, prompts)

    def test_region_scene_contextual_prompts_show_npc_progress(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        npc_position = scene.ecm.get_component(scene.npc_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        npc = scene.ecm.get_component(scene.npc_id, NPC)
        outpost.cleared = True
        npc.report_progress = npc.report_duration / 2

        player_position.x = npc_position.x
        player_position.y = npc_position.y

        prompts = scene.get_contextual_prompts()

        self.assertIn(texts.NPC_REPORT_PROGRESS.format(percent=50), prompts)

    def test_region_scene_camera_follow_does_not_crash(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_position.x = settings.TILE_SIZE * 40
        player_position.y = settings.TILE_SIZE * 20

        scene.update_camera()

        self.assertGreaterEqual(scene.camera.x, 0)
        self.assertGreaterEqual(scene.camera.y, 0)

    def test_region_scene_patrol_tiles_are_floor(self):
        scene = RegionScene()

        for enemy_id in scene.enemy_ids:
            patrol_route = scene.ecm.get_component(enemy_id, PatrolRoute)
            self.assertIsNotNone(patrol_route)

            for tile_x, tile_y in patrol_route.patrol_tiles:
                self.assertEqual(scene.tile_map.matrix[tile_y][tile_x], FLOOR)

    def test_region_scene_critical_openings_are_two_tiles_wide(self):
        scene = RegionScene()

        expected_openings = [
            ((12, 10), (12, 11)),
            ((26, 14), (27, 14)),
            ((34, 16), (34, 17)),
            ((18, 24), (19, 24)),
            ((46, 22), (46, 23)),
        ]

        for first_tile, second_tile in expected_openings:
            first_x, first_y = first_tile
            second_x, second_y = second_tile
            self.assertEqual(scene.tile_map.matrix[first_y][first_x], FLOOR)
            self.assertEqual(scene.tile_map.matrix[second_y][second_x], FLOOR)

    def test_region_scene_validate_region_layout_does_not_fail(self):
        scene = RegionScene()

        scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_enemy_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.enemy_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_patrol_tile_is_unreachable(self):
        scene = RegionScene()
        patrol_route = scene.ecm.get_component(scene.enemy_id, PatrolRoute)
        tile_x, tile_y = patrol_route.patrol_tiles[1]
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_outpost_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.outpost_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_npc_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.npc_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "unreachable important tiles"):
            scene.validate_region_layout()

    def test_region_scene_npc_quest_does_not_complete_when_player_defeated(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        npc_position = scene.ecm.get_component(scene.npc_id, Position)
        npc = scene.ecm.get_component(scene.npc_id, NPC)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)

        outpost.cleared = True
        player_position.x = npc_position.x
        player_position.y = npc_position.y
        player_health.current = 0

        scene.update(0.1, FakeInputManager())
        scene.update(0.1, FakeInteractInputManager())

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertFalse(npc.quest_completed)

    def move_enemies_far_from(self, scene, position):
        for index, enemy_id in enumerate(scene.enemy_ids):
            enemy_position = scene.ecm.get_component(enemy_id, Position)
            if enemy_position is not None:
                enemy_position.x = settings.TILE_SIZE * (50 + index)
                enemy_position.y = settings.TILE_SIZE * 30


if __name__ == "__main__":
    unittest.main()
