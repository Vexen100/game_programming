import unittest
from unittest.mock import patch

import pygame
import settings

from src.components.components import (
    AttackHitbox,
    AttackIntent,
    ChaseBehavior,
    Dead,
    Enemy,
    EnemyAttackState,
    FacingDirection,
    Health,
    MeleeAttack,
    NPC,
    Outpost,
    PatrolRoute,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
    Sprite,
    Velocity,
)
from src.core.event_bus import EventBus
from src.core.game_state import GameState
from src.events.game_events import EnemyKilledEvent, OutpostClearedEvent, QuestCompletedEvent
from src.entities.entities_settings import NPCSettings, OutpostSettings
from src.scenes.region_scene import RegionScene
from src.scenes.world_map_scene import WorldMapScene
from src.systems.influence_system import InfluenceSystem
from src.ui import texts
from src.world.tile_types import BLOCKING_TILES, WALL


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
        self.assertGreaterEqual(len(scene.enemy_ids), 7)
        self.assertEqual(len(scene.outpost_ids), 2)
        self.assertEqual(len(scene.npc_ids), 2)
        self.assertEqual(scene.enemy_id, scene.enemy_ids[0])
        self.assertEqual(scene.outpost_id, scene.outpost_ids[0])
        self.assertEqual(scene.npc_id, scene.npc_ids[0])
        self.assertEqual(len(scene.ecm.alive_entities), 14)
        self.assertIn("north_ruins_outpost", scene.outpost_entity_by_key)
        self.assertIn("east_supply_outpost", scene.outpost_entity_by_key)
        self.assertIn("scout_npc", scene.npc_entity_by_key)
        self.assertIn("villager_npc", scene.npc_entity_by_key)

        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, PlayerControlled))
        self.assertFalse(scene.ecm.has_component(scene.ecs_player_id, PlayerDefeated))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackIntent))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, FacingDirection))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, AttackHitbox))
        self.assertTrue(scene.ecm.has_component(scene.ecs_player_id, Sprite))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, Enemy))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, ChaseBehavior))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, MeleeAttack))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, AttackHitbox))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, EnemyAttackState))
        self.assertTrue(scene.ecm.has_component(scene.enemy_id, PatrolRoute))
        self.assertTrue(scene.ecm.has_component(scene.outpost_id, Outpost))
        self.assertTrue(scene.ecm.has_component(scene.npc_id, NPC))

        for enemy_id in scene.enemy_ids:
            self.assertTrue(scene.ecm.has_component(enemy_id, AttackHitbox))
            self.assertTrue(scene.ecm.has_component(enemy_id, EnemyAttackState))
            self.assertTrue(scene.ecm.has_component(enemy_id, Sprite))

        for outpost_id in scene.outpost_ids:
            self.assertTrue(scene.ecm.has_component(outpost_id, Outpost))
            self.assertTrue(scene.ecm.has_component(outpost_id, Sprite))

        for npc_id in scene.npc_ids:
            self.assertTrue(scene.ecm.has_component(npc_id, NPC))
            self.assertTrue(scene.ecm.has_component(npc_id, Sprite))

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
        attack_state = scene.ecm.get_component(scene.enemy_id, EnemyAttackState)
        hitbox = scene.ecm.get_component(scene.enemy_id, AttackHitbox)

        player_position.x = settings.TILE_SIZE * 5
        player_position.y = settings.TILE_SIZE * 6
        enemy_position.x = settings.TILE_SIZE * 6
        enemy_position.y = settings.TILE_SIZE * 6

        old_health = player_health.current

        scene.update(0.1, FakeInputManager())

        self.assertEqual(player_health.current, old_health)
        self.assertTrue(attack_state.pending)
        self.assertTrue(hitbox.active)

        scene.update(attack_state.windup_duration, FakeInputManager())

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

    def test_region_scene_export_runtime_state_saves_destroyed_enemy_index(self):
        scene = RegionScene()
        scene.ecm.destroy_entity(scene.enemy_ids[1])

        runtime_state = scene.export_runtime_state()

        self.assertIn(1, runtime_state["defeated_enemy_indexes"])

    def test_region_scene_export_runtime_state_saves_dead_enemy_index(self):
        scene = RegionScene()
        scene.ecm.add_component(scene.enemy_ids[2], Dead())

        runtime_state = scene.export_runtime_state()

        self.assertIn(2, runtime_state["defeated_enemy_indexes"])

    def test_region_scene_export_runtime_state_saves_multiple_outposts(self):
        scene = RegionScene()
        north_outpost_id = scene.outpost_entity_by_key["north_ruins_outpost"]
        east_outpost_id = scene.outpost_entity_by_key["east_supply_outpost"]
        scene.ecm.get_component(north_outpost_id, Outpost).cleared = True
        scene.ecm.get_component(east_outpost_id, Outpost).cleared = True

        runtime_state = scene.export_runtime_state()

        self.assertEqual(
            runtime_state["cleared_outpost_keys"],
            ["north_ruins_outpost", "east_supply_outpost"],
        )
        self.assertNotIn("outpost_cleared", runtime_state)

    def test_region_scene_export_runtime_state_saves_multiple_npcs(self):
        scene = RegionScene()
        scout_npc_id = scene.npc_entity_by_key["scout_npc"]
        villager_npc_id = scene.npc_entity_by_key["villager_npc"]
        scene.ecm.get_component(scout_npc_id, NPC).quest_completed = True
        scene.ecm.get_component(villager_npc_id, NPC).quest_completed = True

        runtime_state = scene.export_runtime_state()

        self.assertEqual(
            runtime_state["completed_npc_keys"],
            ["scout_npc", "villager_npc"],
        )
        self.assertNotIn("npc_quest_completed", runtime_state)

    def test_region_scene_export_runtime_state_saves_player_position_and_health(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)
        player_position.x = 123
        player_position.y = 234
        player_health.current = 80

        runtime_state = scene.export_runtime_state()

        self.assertEqual(runtime_state["player"]["x"], 123)
        self.assertEqual(runtime_state["player"]["y"], 234)
        self.assertEqual(runtime_state["player"]["health"], 80)

    def test_region_scene_apply_runtime_state_removes_defeated_enemies(self):
        scene = RegionScene()
        removed_enemy_id = scene.enemy_ids[1]

        scene.apply_runtime_state({"defeated_enemy_indexes": [1]})

        self.assertNotIn(removed_enemy_id, scene.ecm.alive_entities)

    def test_region_scene_apply_runtime_state_restores_multiple_outposts(self):
        scene = RegionScene()

        scene.apply_runtime_state({
            "cleared_outpost_keys": [
                "north_ruins_outpost",
                "east_supply_outpost",
            ]
        })

        for outpost_id in scene.outpost_ids:
            outpost = scene.ecm.get_component(outpost_id, Outpost)
            renderable = scene.ecm.get_component(outpost_id, Renderable)
            self.assertTrue(outpost.cleared)
            self.assertEqual(outpost.clear_progress, outpost.clear_duration)
            self.assertEqual(renderable.color, OutpostSettings.CLEARED_COLOR)

    def test_region_scene_apply_runtime_state_restores_multiple_npcs(self):
        scene = RegionScene()

        scene.apply_runtime_state({
            "completed_npc_keys": [
                "scout_npc",
                "villager_npc",
            ]
        })

        for npc_id in scene.npc_ids:
            npc = scene.ecm.get_component(npc_id, NPC)
            renderable = scene.ecm.get_component(npc_id, Renderable)
            self.assertTrue(npc.quest_completed)
            self.assertEqual(npc.report_progress, npc.report_duration)
            self.assertEqual(renderable.color, NPCSettings.COMPLETED_COLOR)

    def test_region_scene_apply_runtime_state_supports_legacy_single_outpost_snapshot(self):
        scene = RegionScene()

        scene.apply_runtime_state({"outpost_cleared": True})
        first_outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        second_outpost = scene.ecm.get_component(scene.outpost_ids[1], Outpost)

        self.assertTrue(first_outpost.cleared)
        self.assertFalse(second_outpost.cleared)

    def test_region_scene_apply_runtime_state_supports_legacy_single_npc_snapshot(self):
        scene = RegionScene()

        scene.apply_runtime_state({"npc_quest_completed": True})
        first_npc = scene.ecm.get_component(scene.npc_id, NPC)
        second_npc = scene.ecm.get_component(scene.npc_ids[1], NPC)

        self.assertTrue(first_npc.quest_completed)
        self.assertFalse(second_npc.quest_completed)

    def test_region_scene_apply_runtime_state_restores_player_position_and_health(self):
        scene = RegionScene()

        scene.apply_runtime_state({
            "player": {
                "x": 140,
                "y": 180,
                "health": 72,
            }
        })
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        self.assertEqual(player_position.x, 140)
        self.assertEqual(player_position.y, 180)
        self.assertEqual(player_health.current, 72)

    def test_region_scene_apply_runtime_state_clamps_player_health_to_one(self):
        scene = RegionScene()

        scene.apply_runtime_state({"player": {"health": 0}})
        player_health = scene.ecm.get_component(scene.ecs_player_id, Health)

        self.assertEqual(player_health.current, 1)

    def test_region_scene_apply_runtime_state_does_not_publish_events(self):
        class RecordingEventBus:
            def __init__(self):
                self.events = []

            def publish(self, event):
                self.events.append(event)

        event_bus = RecordingEventBus()
        scene = RegionScene(event_bus=event_bus)

        scene.apply_runtime_state({
            "defeated_enemy_indexes": [0],
            "outpost_cleared": True,
            "npc_quest_completed": True,
        })

        self.assertEqual(event_bus.events, [])

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
        self.assertIn("Аванпосты: 0/2", status_lines)
        self.assertIn("Задания: 0/2", status_lines)
        self.assertIn("Враги: 9/9", status_lines)
        self.assertIn(texts.ASSAULT_LOCKED, status_lines)

    def test_region_scene_status_lines_show_objective_counts(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        scene = RegionScene(game_state)
        first_outpost = scene.ecm.get_component(scene.outpost_ids[0], Outpost)
        first_npc = scene.ecm.get_component(scene.npc_ids[0], NPC)
        first_outpost.cleared = True
        first_npc.quest_completed = True
        scene.ecm.destroy_entity(scene.enemy_ids[0])

        status_lines = scene.get_region_status_lines()

        self.assertIn("Аванпосты: 1/2", status_lines)
        self.assertIn("Задания: 1/2", status_lines)
        self.assertIn("Враги: 8/9", status_lines)

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

        self.assertEqual(region.player_influence, 5)
        self.assertEqual(region.enemy_influence, 95)
        self.assertIn(f"{texts.REGION_INFLUENCE_PLAYER}: 5", status_lines)
        self.assertIn(f"{texts.REGION_INFLUENCE_ENEMY}: 95", status_lines)

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
        self.assertEqual(region.player_influence, 5)
        self.assertEqual(region.enemy_influence, 95)

        world_map_scene = WorldMapScene(game_state)
        status = world_map_scene.get_region_status_text(region)

        self.assertIn("игрок 5", status)
        self.assertIn("враг 95", status)

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
        self.assertEqual(region.player_influence, 20)
        self.assertEqual(region.enemy_influence, 80)
        self.assertFalse(region.assault_unlocked)

    def test_region_scene_full_region_loop_unlocks_assault(self):
        game_state = GameState.load_from_file(settings.REGIONS_DATA_PATH)
        game_state.set_current_region("old_ruins")
        event_bus = EventBus()
        influence_system = InfluenceSystem(game_state)
        influence_system.subscribe(event_bus)
        scene = RegionScene(game_state, event_bus)

        for outpost_id in scene.outpost_ids:
            event_bus.publish(OutpostClearedEvent(outpost_id, "old_ruins"))

        for npc_id in scene.npc_ids:
            npc = scene.ecm.get_component(npc_id, NPC)
            event_bus.publish(
                QuestCompletedEvent(
                    quest_id=npc.quest_id,
                    npc_id=npc_id,
                    region_id="old_ruins",
                )
            )

        region = game_state.get_region("old_ruins")
        self.assertEqual(region.enemy_influence, 30)
        self.assertFalse(region.assault_unlocked)

        event_bus.publish(EnemyKilledEvent(scene.enemy_id, "old_ruins"))

        self.assertEqual(region.enemy_influence, 25)
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
        self.assertEqual(region.player_influence, 15)
        self.assertEqual(region.enemy_influence, 85)

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

    def test_region_scene_rebuild_enemy_spatial_index_creates_index(self):
        scene = RegionScene()
        enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        scene.rebuild_enemy_spatial_index()

        self.assertIsNotNone(scene.enemy_spatial_index)
        self.assertIn(
            scene.enemy_id,
            scene.enemy_spatial_index.query_rect(
                enemy_position.x,
                enemy_position.y,
                settings.TILE_SIZE,
                settings.TILE_SIZE,
            ),
        )

    def test_region_scene_update_builds_enemy_spatial_index(self):
        scene = RegionScene()

        scene.update(0.1, FakeInputManager())

        self.assertIsNotNone(scene.enemy_spatial_index)

    def test_region_scene_enemy_spatial_index_contains_living_enemies(self):
        scene = RegionScene()

        scene.rebuild_enemy_spatial_index()

        indexed_enemy_ids = scene.enemy_spatial_index.query_rect(
            0,
            0,
            scene.tile_map.width * scene.tile_map.tile_size,
            scene.tile_map.height * scene.tile_map.tile_size,
        )

        for enemy_id in scene.enemy_ids:
            self.assertIn(enemy_id, indexed_enemy_ids)

    def test_dead_enemy_does_not_block_outpost_through_spatial_index(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)
        outpost = scene.ecm.get_component(scene.outpost_id, Outpost)
        dead_enemy_position = scene.ecm.get_component(scene.enemy_id, Position)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)
        dead_enemy_position.x = outpost_position.x
        dead_enemy_position.y = outpost_position.y
        scene.ecm.add_component(scene.enemy_id, Dead())
        scene.rebuild_enemy_spatial_index()

        scene.outpost_system.update(
            scene.ecm,
            FakeInteractInputManager(),
            scene.get_current_region_id(),
            outpost.clear_duration,
            scene.enemy_spatial_index,
        )

        self.assertTrue(outpost.cleared)

    def test_region_scene_contextual_prompts_show_outpost_hold_hint(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_position = scene.ecm.get_component(scene.outpost_id, Position)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)

        prompts = scene.get_contextual_prompts()

        self.assertIn(texts.OUTPOST_HOLD_TO_CLEAR, prompts)

    def test_region_scene_outpost_prompts_work_for_multiple_outposts(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        outpost_id = scene.outpost_entity_by_key["east_supply_outpost"]
        outpost_position = scene.ecm.get_component(outpost_id, Position)

        player_position.x = outpost_position.x
        player_position.y = outpost_position.y
        self.move_enemies_far_from(scene, outpost_position)

        prompts = scene.get_contextual_prompts()

        self.assertEqual(prompts, [texts.OUTPOST_HOLD_TO_CLEAR])

    def test_region_scene_outpost_prompt_uses_nearest_relevant_outpost(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        first_outpost_id = scene.outpost_ids[0]
        second_outpost_id = scene.outpost_ids[1]
        first_outpost = scene.ecm.get_component(first_outpost_id, Outpost)
        first_position = scene.ecm.get_component(first_outpost_id, Position)
        second_position = scene.ecm.get_component(second_outpost_id, Position)
        first_outpost.cleared = True
        first_position.x = 100
        first_position.y = 100
        second_position.x = 110
        second_position.y = 100
        player_position.x = second_position.x
        player_position.y = second_position.y
        self.move_enemies_far_from(scene, second_position)

        prompts = scene.get_contextual_prompts()

        self.assertEqual(prompts, [texts.OUTPOST_HOLD_TO_CLEAR])

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

    def test_region_scene_npc_prompts_work_for_multiple_npcs(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        npc_id = scene.npc_entity_by_key["villager_npc"]
        npc = scene.ecm.get_component(npc_id, NPC)
        npc_position = scene.ecm.get_component(npc_id, Position)
        required_outpost = scene.ecm.get_component(npc.required_outpost_id, Outpost)
        required_outpost.cleared = True

        player_position.x = npc_position.x
        player_position.y = npc_position.y

        prompts = scene.get_contextual_prompts()

        self.assertEqual(prompts, [texts.NPC_HOLD_TO_REPORT])

    def test_region_scene_npc_prompt_uses_nearest_relevant_npc(self):
        scene = RegionScene()
        player_position = scene.ecm.get_component(scene.ecs_player_id, Position)
        first_npc_id = scene.npc_ids[0]
        second_npc_id = scene.npc_ids[1]
        first_npc = scene.ecm.get_component(first_npc_id, NPC)
        second_npc = scene.ecm.get_component(second_npc_id, NPC)
        first_position = scene.ecm.get_component(first_npc_id, Position)
        second_position = scene.ecm.get_component(second_npc_id, Position)
        first_npc.quest_completed = True
        scene.ecm.get_component(second_npc.required_outpost_id, Outpost).cleared = True
        first_position.x = 100
        first_position.y = 100
        second_position.x = 110
        second_position.y = 100
        player_position.x = second_position.x
        player_position.y = second_position.y

        prompts = scene.get_contextual_prompts()

        self.assertEqual(prompts, [texts.NPC_HOLD_TO_REPORT])

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

    def test_region_scene_patrol_tiles_are_walkable(self):
        scene = RegionScene()

        for enemy_id in scene.enemy_ids:
            patrol_route = scene.ecm.get_component(enemy_id, PatrolRoute)
            self.assertIsNotNone(patrol_route)

            for tile_x, tile_y in patrol_route.patrol_tiles:
                self.assertNotIn(scene.tile_map.matrix[tile_y][tile_x], BLOCKING_TILES)

    def test_region_scene_critical_openings_are_two_tiles_wide(self):
        scene = RegionScene()

        expected_openings = [
            ((44, 19), (45, 19)),
            ((45, 42), (46, 42)),
            ((32, 19), (33, 19)),
            ((71, 20), (72, 20)),
            ((56, 42), (57, 42)),
        ]

        for first_tile, second_tile in expected_openings:
            first_x, first_y = first_tile
            second_x, second_y = second_tile
            self.assertNotIn(scene.tile_map.matrix[first_y][first_x], BLOCKING_TILES)
            self.assertNotIn(scene.tile_map.matrix[second_y][second_x], BLOCKING_TILES)

    def test_region_scene_validate_region_layout_does_not_fail(self):
        scene = RegionScene()

        scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_enemy_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.enemy_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "blocked important tile"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_patrol_tile_is_unreachable(self):
        scene = RegionScene()
        patrol_route = scene.ecm.get_component(scene.enemy_id, PatrolRoute)
        tile_x, tile_y = patrol_route.patrol_tiles[1]
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "blocked important tile"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_outpost_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.outpost_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "blocked important tile"):
            scene.validate_region_layout()

    def test_region_scene_validate_region_layout_raises_if_npc_is_unreachable(self):
        scene = RegionScene()
        tile_x, tile_y = scene.get_entity_tile(scene.npc_id)
        scene.tile_map.matrix[tile_y][tile_x] = WALL

        with self.assertRaisesRegex(ValueError, "blocked important tile"):
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
