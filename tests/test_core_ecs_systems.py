import unittest

import pygame

import settings
from src.components.components import (
    Animation,
    AnimationRequest,
    AttackHitbox,
    AttackIntent,
    CapturePoint,
    ChaseBehavior,
    Collider,
    Dead,
    Enemy,
    FacingDirection,
    Health,
    HitFlash,
    DamagePopup,
    MeleeAttack,
    NPC,
    Outpost,
    PlayerControlled,
    PlayerDefeated,
    Position,
    Renderable,
    Sprite,
    SupplyCache,
    TemporaryVisualEffect,
    Velocity,
)
from src.ecs.entity_component_manager import EntityComponentManager
from src.entities.entity_factory import EntityFactory
from src.events.game_events import (
    CapturePointTakenEvent,
    OutpostClearedEvent,
    QuestCompletedEvent,
    SupplyCacheDestroyedEvent,
)
from src.systems.capture_system import CaptureSystem
from src.systems.cleanup_system import CleanupSystem
from src.systems.collision_system import CollisionSystem
from src.systems.enemy_chase_system import EnemyChaseSystem
from src.systems.enemy_attack_system import EnemyAttackSystem
from src.systems.enemy_death_system import EnemyDeathSystem
from src.systems.melee_attack_system import MeleeAttackSystem
from src.systems.movement_system import MovementSystem
from src.systems.npc_interaction_system import NPCInteractionSystem
from src.systems.outpost_system import OutpostSystem
from src.systems.player_death_system import PlayerDeathSystem
from src.systems.player_input_system import PlayerInputSystem
from src.systems.supply_cache_system import SupplyCacheSystem
from src.systems.animation_system import AnimationSystem
from src.systems.visual_effect_system import VisualEffectSystem
from src.world.tile_map import TileMap
from src.world.tile_types import FLOOR, WALL


class FakeInputManager:
    """Управляет подсистемой: fake ввод manager.

    """

    def __init__(self, direction=(0, 0), interact=False):
        """Инициализирует `FakeInputManager` и сохраняет начальные зависимости.

        Args:
            direction: Значение `direction`, используемое в логике метода.
            interact: Значение `interact`, используемое в логике метода.

        Returns:
            None.
        """
        self.direction = pygame.Vector2(direction)
        self.interact = interact

    def get_velocity_direction(self):
        """Возвращает нормализованное направление движения по вводу.

        Returns:
            Найденное или вычисленное значение: скорость direction.
        """
        return self.direction

    def is_pressed(self, action):
        """Проверяет, удерживается ли действие прямо сейчас.

        Args:
            action: Имя игрового действия из таблицы привязок ввода.

        Returns:
            `True`, если условие выполнено, иначе `False`.
        """
        return action == settings.INTERACT and self.interact


class EventCollector:
    """Описывает объект проекта: событие collector.

    """

    def __init__(self):
        """Инициализирует `EventCollector` и сохраняет начальные зависимости.

        Returns:
            None.
        """
        self.events = []

    def publish(self, event):
        """Публикует событие всем подписчикам его типа.

        Args:
            event: Событие PyGame или событие внутренней игровой шины.

        Returns:
            None.
        """
        self.events.append(event)


class TestCoreECSSystems(unittest.TestCase):
    """Проверяет ключевое поведение: test core ecs systems.

    """

    def create_ecm_and_factory(self):
        """Создает ECM и фабрику сущностей.

        Returns:
            Пара `(ecm, factory)`.
        """
        ecm = EntityComponentManager()
        return ecm, EntityFactory(ecm)

    def create_open_tile_map(self):
        """Создает маленькую проходимую TileMap.

        Returns:
            TileMap с полом.
        """
        return TileMap([[FLOOR for _ in range(5)] for _ in range(5)])

    def test_ecm_lifecycle_add_query_and_destroy(self):
        """Проверяет сценарий: ecm lifecycle add query and destroy.

        Returns:
            None.
        """
        ecm = EntityComponentManager()

        entity = ecm.create_entity(tag="player")
        ecm.add_component(entity, Position(10, 20))
        ecm.add_component(entity, Velocity(1, 0))
        ecm.destroy_entity(entity)

        self.assertNotIn(entity, ecm.alive_entities)
        self.assertIsNone(ecm.get_component(entity, Position))

    def test_entity_factory_creates_player_archetype(self):
        """Проверяет сценарий: сущность фабрика creates игрок archetype.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()

        player = factory.create_player(32, 32)

        for component_type in (
            Position,
            Velocity,
            Collider,
            Renderable,
            Sprite,
            Animation,
            Health,
            PlayerControlled,
            AttackIntent,
            FacingDirection,
            AttackHitbox,
        ):
            self.assertTrue(ecm.has_component(player, component_type))

    def test_entity_factory_creates_enemy_and_objectives(self):
        """Проверяет сценарий: сущность фабрика creates враг and objectives.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()

        enemy = factory.create_enemy(64, 64)
        outpost = factory.create_outpost(96, 64)
        npc = factory.create_npc(128, 64, quest_id="quest", required_outpost_id=outpost)
        supply_cache = factory.create_supply_cache(192, 64, key="cache")
        capture_point = factory.create_capture_point(160, 64)

        self.assertTrue(ecm.has_component(enemy, Enemy))
        self.assertTrue(ecm.has_component(enemy, Animation))
        self.assertTrue(ecm.has_component(enemy, ChaseBehavior))
        self.assertTrue(ecm.has_component(outpost, Outpost))
        self.assertTrue(ecm.has_component(npc, NPC))
        self.assertTrue(ecm.has_component(supply_cache, SupplyCache))
        self.assertTrue(ecm.has_component(capture_point, CapturePoint))

    def test_create_supply_cache_has_expected_components(self):
        """Проверяет минимальный ECS-набор склада снабжения.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()

        supply_cache = factory.create_supply_cache(96, 64, key="cache")

        for component_type in (SupplyCache, Position, Collider, Renderable, Sprite):
            self.assertTrue(ecm.has_component(supply_cache, component_type))

        for forbidden_component_type in (Enemy, Health, NPC, CapturePoint, Animation):
            self.assertFalse(ecm.has_component(supply_cache, forbidden_component_type))

    def test_only_player_and_enemy_have_animation_component(self):
        """Проверяет, что Animation есть только у player/enemy archetypes.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()

        player = factory.create_player(32, 32)
        enemy = factory.create_enemy(64, 64)
        outpost = factory.create_outpost(96, 64)
        npc = factory.create_npc(128, 64, quest_id="quest", required_outpost_id=outpost)
        supply_cache = factory.create_supply_cache(192, 64, key="cache")
        capture_point = factory.create_capture_point(160, 64)

        self.assertTrue(ecm.has_component(player, Animation))
        self.assertTrue(ecm.has_component(enemy, Animation))
        self.assertFalse(ecm.has_component(outpost, Animation))
        self.assertFalse(ecm.has_component(npc, Animation))
        self.assertFalse(ecm.has_component(supply_cache, Animation))
        self.assertFalse(ecm.has_component(capture_point, Animation))

    def test_player_input_updates_velocity_and_facing(self):
        """Проверяет сценарий: игрок ввод updates скорость and facing.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)

        PlayerInputSystem(speed=100).update(ecm, FakeInputManager(direction=(1, 0)))

        velocity = ecm.get_component(player, Velocity)
        facing = ecm.get_component(player, FacingDirection)
        self.assertEqual((velocity.x, velocity.y), (100, 0))
        self.assertEqual((facing.x, facing.y), (1, 0))

    def test_movement_system_moves_entity_and_returns_previous_position(self):
        """Проверяет сценарий: movement system moves сущность and returns previous position.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, Position(10, 20))
        ecm.add_component(entity, Velocity(5, -5))

        previous_positions = MovementSystem().update(ecm, dt=2)

        position = ecm.get_component(entity, Position)
        self.assertEqual(previous_positions[entity], (10, 20))
        self.assertEqual((position.x, position.y), (20, 10))

    def test_collision_system_blocks_wall_overlap(self):
        """Проверяет сценарий: collision system blocks wall overlap.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, Position(0, 0))
        ecm.add_component(entity, Collider(32, 32))
        tile_map = TileMap([[FLOOR, WALL], [FLOOR, FLOOR]])

        CollisionSystem().update(ecm, tile_map, {entity: (0, 0)})

        position = ecm.get_component(entity, Position)
        self.assertEqual((position.x, position.y), (0, 0))

    def test_melee_attack_damages_enemy_and_activates_hitbox(self):
        """Проверяет сценарий: melee атака damages враг and activates hitbox.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        enemy = factory.create_enemy(60, 32)
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem().update(ecm, dt=0.1)

        self.assertLess(ecm.get_component(enemy, Health).current, ecm.get_component(enemy, Health).maximum)
        self.assertTrue(ecm.get_component(player, AttackHitbox).active)

    def test_melee_hit_adds_hit_flash_to_enemy(self):
        """Проверяет, что реальное попадание добавляет HitFlash врагу.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        enemy = factory.create_enemy(60, 32)
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem().update(ecm, dt=0.1)

        self.assertTrue(ecm.has_component(enemy, HitFlash))

    def test_damage_popup_spawned_on_melee_hit(self):
        """Проверяет, что попадание игрока создает damage popup.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        visual_effects = VisualEffectSystem()
        player = factory.create_player(32, 32)
        factory.create_enemy(60, 32)
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem(visual_effects).update(ecm, dt=0.1)

        self.assertEqual(len(ecm.get_entities_with(DamagePopup)), 1)

    def test_slash_effect_spawned_when_player_attacks(self):
        """Проверяет, что принятая melee-атака создает slash effect.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        visual_effects = VisualEffectSystem()
        player = factory.create_player(32, 32)
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem(visual_effects).update(ecm, dt=0.1)

        effect_ids = ecm.get_entities_with(TemporaryVisualEffect)
        self.assertEqual(len(effect_ids), 1)
        effect = ecm.get_component(next(iter(effect_ids)), TemporaryVisualEffect)
        self.assertEqual(effect.effect_type, "slash")

    def test_melee_attack_adds_player_attack_animation_request(self):
        """Проверяет request attack animation при принятой атаке игрока.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem().update(ecm, dt=0.1)

        request = ecm.get_component(player, AnimationRequest)
        self.assertIsNotNone(request)
        self.assertEqual(request.state, "attack")

    def test_melee_attack_does_not_add_animation_request_when_cooldown_blocks(self):
        """Проверяет отсутствие animation request при cooldown block.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        ecm.get_component(player, MeleeAttack).cooldown_timer = 0.5
        ecm.get_component(player, AttackIntent).requested = True

        MeleeAttackSystem().update(ecm, dt=0.1)

        self.assertFalse(ecm.has_component(player, AnimationRequest))

    def test_enemy_attack_adds_attack_animation_request_when_windup_starts(self):
        """Проверяет request attack animation при старте enemy windup.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        enemy = factory.create_enemy(64, 32)

        EnemyAttackSystem().update(ecm, dt=0.01)

        request = ecm.get_component(enemy, AnimationRequest)
        self.assertIsNotNone(request)
        self.assertEqual(request.state, "attack")

    def test_enemy_attack_animation_request_not_added_every_frame_during_same_windup(self):
        """Проверяет, что enemy windup не спамит AnimationRequest.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        enemy = factory.create_enemy(64, 32)
        enemy_attack_system = EnemyAttackSystem()
        animation_system = AnimationSystem()

        enemy_attack_system.update(ecm, dt=0.01)
        animation_system.update(ecm, dt=0.01)
        enemy_attack_system.update(ecm, dt=0.01)

        self.assertFalse(ecm.has_component(enemy, AnimationRequest))

    def test_enemy_death_marks_dead_and_publishes_event(self):
        """Проверяет сценарий: враг death marks dead and publishes событие.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        enemy = factory.create_enemy(64, 64)
        ecm.get_component(enemy, Health).current = 0
        events = EventCollector()

        EnemyDeathSystem(event_bus=events).update(ecm, region_id="old_ruins")

        self.assertTrue(ecm.has_component(enemy, Dead))
        self.assertEqual(events.events[0].enemy_id, enemy)

    def test_cleanup_system_removes_dead_entities(self):
        """Проверяет сценарий: cleanup system removes dead сущности.

        Returns:
            None.
        """
        ecm = EntityComponentManager()
        entity = ecm.create_entity()
        ecm.add_component(entity, Dead())

        CleanupSystem().update(ecm)

        self.assertNotIn(entity, ecm.alive_entities)

    def test_player_death_marks_defeated(self):
        """Проверяет сценарий: игрок death marks defeated.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        ecm.get_component(player, Health).current = 0

        PlayerDeathSystem().update(ecm)

        self.assertTrue(ecm.has_component(player, PlayerDefeated))

    def test_outpost_clears_when_player_interacts_without_enemies(self):
        """Проверяет сценарий: аванпост clears when игрок interacts without враги.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        outpost = factory.create_outpost(32, 32)
        events = EventCollector()

        OutpostSystem(event_bus=events).update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=10,
        )

        self.assertTrue(ecm.get_component(outpost, Outpost).cleared)
        self.assertIsInstance(events.events[0], OutpostClearedEvent)

    def test_outpost_does_not_clear_with_living_enemy_nearby(self):
        """Проверяет сценарий: аванпост does not clear with живой враг nearby.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        outpost = factory.create_outpost(32, 32)
        factory.create_enemy(32, 32)

        OutpostSystem().update(ecm, FakeInputManager(interact=True), dt=10)

        self.assertFalse(ecm.get_component(outpost, Outpost).cleared)

    def test_npc_completes_quest_after_required_outpost(self):
        """Проверяет сценарий: NPC completes задание after required аванпост.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        outpost = factory.create_outpost(64, 64)
        ecm.get_component(outpost, Outpost).cleared = True
        npc = factory.create_npc(32, 32, quest_id="quest", required_outpost_id=outpost)
        events = EventCollector()

        NPCInteractionSystem(event_bus=events).update(
            ecm,
            FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=10,
        )

        self.assertTrue(ecm.get_component(npc, NPC).quest_completed)
        self.assertIsInstance(events.events[0], QuestCompletedEvent)

    def test_supply_cache_progresses_when_player_near_and_interacting(self):
        """Проверяет progress склада при удержании interaction без врагов.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        supply_cache = factory.create_supply_cache(32, 32, key="cache")

        SupplyCacheSystem().update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=0.5,
        )

        self.assertEqual(ecm.get_component(supply_cache, SupplyCache).destroy_progress, 0.5)

    def test_supply_cache_progress_resets_when_player_leaves_or_releases_interact(self):
        """Проверяет reset progress при уходе игрока или отпускании interaction.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        player = factory.create_player(32, 32)
        supply_cache = factory.create_supply_cache(32, 32, key="cache")
        supply_cache_component = ecm.get_component(supply_cache, SupplyCache)
        supply_cache_component.destroy_progress = 0.4

        SupplyCacheSystem().update(
            ecm,
            input_manager=FakeInputManager(interact=False),
            region_id="old_ruins",
            dt=0.2,
        )

        self.assertEqual(supply_cache_component.destroy_progress, 0)

        supply_cache_component.destroy_progress = 0.4
        ecm.get_component(player, Position).x = 300
        SupplyCacheSystem().update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=0.2,
        )

        self.assertEqual(supply_cache_component.destroy_progress, 0)

    def test_supply_cache_does_not_progress_when_living_enemy_nearby(self):
        """Проверяет, что живой враг рядом блокирует склад.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        supply_cache = factory.create_supply_cache(32, 32, key="cache")
        factory.create_enemy(96, 32)

        SupplyCacheSystem().update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=0.5,
        )

        self.assertEqual(ecm.get_component(supply_cache, SupplyCache).destroy_progress, 0)

    def test_dead_enemy_does_not_block_supply_cache(self):
        """Проверяет, что мёртвый враг рядом не блокирует уничтожение склада.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        supply_cache = factory.create_supply_cache(32, 32, key="cache")
        enemy = factory.create_enemy(96, 32)
        ecm.add_component(enemy, Dead())

        SupplyCacheSystem().update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=0.5,
        )

        self.assertEqual(ecm.get_component(supply_cache, SupplyCache).destroy_progress, 0.5)

    def test_supply_cache_destroyed_publishes_event_once(self):
        """Проверяет публикацию события уничтожения склада один раз.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        supply_cache = factory.create_supply_cache(32, 32, key="cache")
        events = EventCollector()
        system = SupplyCacheSystem(event_bus=events)

        system.update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=10,
        )
        system.update(
            ecm,
            input_manager=FakeInputManager(interact=True),
            region_id="old_ruins",
            dt=10,
        )

        self.assertTrue(ecm.get_component(supply_cache, SupplyCache).destroyed)
        self.assertEqual(len(events.events), 1)
        self.assertIsInstance(events.events[0], SupplyCacheDestroyedEvent)
        self.assertEqual(events.events[0].supply_cache_key, "cache")

    def test_capture_system_captures_point_and_publishes_event(self):
        """Проверяет сценарий: точка захвата system captures точка and publishes событие.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        capture_point = factory.create_capture_point(32, 32)
        events = EventCollector()

        CaptureSystem(event_bus=events).update(ecm, dt=10, region_id="old_ruins")

        self.assertTrue(ecm.get_component(capture_point, CapturePoint).captured)
        self.assertIsInstance(events.events[0], CapturePointTakenEvent)

    def test_capture_system_waits_when_enemy_is_nearby(self):
        """Проверяет сценарий: точка захвата system waits when враг is nearby.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        capture_point = factory.create_capture_point(32, 32)
        factory.create_enemy(32, 32)

        CaptureSystem().update(ecm, dt=10, region_id="old_ruins")

        self.assertFalse(ecm.get_component(capture_point, CapturePoint).captured)

    def test_enemy_chase_without_tile_map_moves_towards_player(self):
        """Проверяет сценарий: враг chase without тайл карта moves towards игрок.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        factory.create_player(32, 32)
        enemy = factory.create_enemy(96, 32)

        EnemyChaseSystem().update(ecm)

        velocity = ecm.get_component(enemy, Velocity)
        self.assertLess(velocity.x, 0)
        self.assertEqual(velocity.y, 0)

    def test_enemy_chase_stops_without_player(self):
        """Проверяет сценарий: враг chase stops without игрок.

        Returns:
            None.
        """
        ecm, factory = self.create_ecm_and_factory()
        enemy = factory.create_enemy(96, 32)
        ecm.get_component(enemy, Velocity).x = 10

        EnemyChaseSystem().update(ecm)

        velocity = ecm.get_component(enemy, Velocity)
        self.assertEqual((velocity.x, velocity.y), (0, 0))
