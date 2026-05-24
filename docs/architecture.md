# Архитектура проекта

## Назначение документа

Этот документ описывает текущую структуру проекта Crown Reclaim.

Цель архитектуры — держать код простым и расширяемым, не возвращаясь к отдельным OOP-классам игровых объектов.

---

## Общая идея архитектуры

Проект строится вокруг простого игрового цикла:

1. обработка системных событий;
2. обработка ввода;
3. обновление ECS-систем;
4. обработка столкновений;
5. отрисовка карты, сущностей и UI.

Игрок и враг не являются отдельными классами `Player`/`Enemy`. Они являются `entity_id` с набором компонентов.

Компоненты хранят данные. Системы выполняют логику. `EntityFactory` создаёт типовые наборы компонентов.

---

## Актуальная структура проекта

- `main.py`
- `settings.py`
- `src/core/game.py`
- `src/core/event_bus.py`
- `src/core/game_state.py`
- `src/core/input_manager.py`
- `src/core/scene_manager.py`
- `src/scenes/main_menu_scene.py`
- `src/scenes/pause_scene.py`
- `src/scenes/world_map_scene.py`
- `src/scenes/region_scene.py`
- `src/scenes/castle_assault_scene.py`
- `src/ecs/entity_component_manager.py`
- `src/components/components.py`
- `src/entities/entity_factory.py`
- `src/entities/entities_settings.py`
- `src/algorithms/`
- `src/systems/`
- `src/events/`
- `src/ui/`
- `src/world/`
- `data/regions/regions.json`
- `tests/`

---

## Основные модули

### `main.py`

Точка входа в игру. Создаёт `Game` и запускает главный цикл.

### `settings.py`

Файл с базовыми настройками и action-константами.

### `src/core/game.py`

Создаёт окно, `InputManager`, `GameState`, `EventBus`, `InfluenceSystem`, `RegionLiberationSystem`, `SceneManager`, регистрирует `MainMenuScene`, `WorldMapScene`, `RegionScene`, `CastleAssaultScene` и `PauseScene`, затем запускает цикл `handle_events -> update -> draw`.

Стартовая сцена — `MainMenuScene`.

`InfluenceSystem` подписывается на игровые события через `EventBus`.

`RegionLiberationSystem` подписывается на `RegionLiberatedEvent` через `EventBus`.

### `src/core/event_bus.py`

Содержит простую шину игровых событий. `EventBus` хранит подписчиков и публикует события, но не знает про ECS, сцены или `GameState`.

### `src/core/game_state.py`

Хранит глобальное состояние регионов: открытие, контроль, влияние, доступность штурма и освобождение.

Загружает стартовые данные из `data/regions/regions.json`.

`GameState.mark_liberated()` открывает регионы из списка `unlocks_on_liberation` освобождённого региона.

### `src/core/input_manager.py`

Обрабатывает клавиатуру и отдаёт действия через строковые action-константы.

### `src/core/scene_manager.py`

Регистрирует scene factories и переключает текущую сцену по запросу.

`SceneManager` сам не импортирует конкретные сцены. Текущая сцена создаётся через зарегистрированную фабрику.

Также умеет временно сохранить текущую gameplay-сцену в `paused_scene` и восстановить её через `resume_scene()`.

Это минимальная пауза без полноценного stack-сцен и без overlay-rendering.

### `src/scenes/main_menu_scene.py`

Минимальное главное меню.

Содержит пункты `Start Game`, `Continue (not available)`, `Settings (not available)` и `Exit`.

На текущем этапе `Start Game` открывает `WorldMapScene`, а `Continue` и `Settings` являются заглушками.

### `src/scenes/pause_scene.py`

Минимальное меню паузы.

Содержит пункты `Resume`, `World Map` и `Main Menu`.

`Resume` возвращает сохранённую gameplay-сцену через `SceneManager.resume_scene()`.

### `src/scenes/region_scene.py`

Создаёт тестовую карту, ECS-слой, игрока, врага, аванпост, одного тестового NPC, системы, HUD и debug overlay.

Может получать `GameState` и показывает название текущего региона в HUD.

По `M` может запросить возврат на `WorldMapScene`. При возврате `GameState` сохраняется, потому что принадлежит `Game`, а не сцене.

По `Esc` может запросить `PauseScene`.

NPC завершает простое задание после зачистки аванпоста и взаимодействия по `E`.

### `src/scenes/world_map_scene.py`

Показывает простую placeholder-карту регионов из `GameState`.

Позволяет выбрать открытый регион и запросить переход в `RegionScene`.

Показывает influence выбранного региона и текстовый статус `assault_unlocked`.

Если выбранный регион открыт и `assault_unlocked == True`, по `C` можно перейти в `CastleAssaultScene`.

### `src/scenes/castle_assault_scene.py`

Статическая сцена штурма замка.

Создаёт простую ручную карту замка, ECS-слой, игрока, несколько врагов, две точки захвата, базовые gameplay-системы, HUD и debug overlay.

`CastleAssaultScene` хранит список `enemy_ids`.

`enemy_id` оставлен только как alias первого врага для совместимости старого кода и тестов.

Существующие ECS-системы работают со всеми врагами через компоненты и ECS-запросы.

При создании и локальном restart проверяет достижимость игрока, всех врагов и всех точек захвата через `src/algorithms/flood_fill.py`.

Эта проверка нужна только для validation карты замка и не используется для движения врагов.

`CastleWaveSystem` локально используется внутри `CastleAssaultScene`.

Он не подписывается на глобальный `EventBus`, не хранит `GameState` и создаёт обычных врагов через `EntityFactory`.

Это минимальная локальная механика подкреплений, а не полноценный `EnemySpawner` или `WaveManager`.

После захвата всех точек сцена переходит в локальное состояние `assault_completed`.

В состоянии `assault_completed` gameplay-системы больше не обновляются.

`M` продолжает возвращать на `WorldMapScene`, а `Esc` продолжает открывать `PauseScene`.

По `M` может запросить возврат на `WorldMapScene`.

По `Esc` может запросить `PauseScene`.

Если игрок побеждён, по `R` сцена локально перезапускает штурм.

`CastleAssaultScene` не освобождает регион напрямую и не знает про `InfluenceSystem`.

Точки захвата обрабатывает `CaptureSystem`. После захвата всех точек публикуется `RegionLiberatedEvent`.

Глобальное liberation региона по-прежнему идёт через `RegionLiberatedEvent` и `RegionLiberationSystem`.

### `src/ecs/entity_component_manager.py`

Хранит сущности, теги и компоненты по типам.

### `src/components/components.py`

Содержит dataclass-компоненты: `Position`, `Velocity`, `Collider`, `Renderable`, `Health`, `PlayerControlled`, `PlayerDefeated`, `Enemy`, `Outpost`, `NPC`, `CapturePoint`, `Dead`, `ChaseBehavior`, `AttackIntent`, `MeleeAttack`.

### `src/entities/entity_factory.py`

Создаёт типовые ECS-сущности и добавляет им компоненты.

Сейчас фабрика создаёт игрока с `AttackIntent`/`MeleeAttack`, базового врага с `ChaseBehavior`/`MeleeAttack`, простой аванпост, NPC с простым заданием и точку захвата.

### `src/entities/entities_settings.py`

Хранит простые настройки сущностей: скорость, здоровье, размер и цвет.

### `src/algorithms/`

Содержит отдельные алгоритмы, которые не зависят от PyGame-сцен и ECS-систем.

`src/algorithms/flood_fill.py` реализует простой Flood fill / BFS по тайлам в 4 направлениях.

Сейчас алгоритм используется в `CastleAssaultScene` для проверки, что важные тайлы статического замка достижимы.

Алгоритм использует tile-coordinate API `TileMap.is_tile_blocked()`.

Он не является A* и не управляет движением врагов.

### `src/systems/`

Содержит текущие ECS-системы:

- `PlayerInputSystem`;
- `PlayerAttackInputSystem`;
- `EnemyChaseSystem`;
- `MovementSystem`;
- `CollisionSystem`;
- `MeleeAttackSystem`;
- `EnemyDeathSystem`;
- `OutpostSystem`;
- `NPCInteractionSystem`;
- `CaptureSystem`;
- `CastleWaveSystem`;
- `EnemyAttackSystem`;
- `PlayerDeathSystem`;
- `CleanupSystem`;
- `RenderSystem`.

Также содержит `InfluenceSystem`, который слушает `EnemyKilledEvent`, `OutpostClearedEvent`, `QuestCompletedEvent` и меняет глобальное влияние регионов через `GameState`.

`CaptureSystem` работает только с ECS и `EventBus`: захватывает точки и публикует события.

`CastleWaveSystem` работает локально в `CastleAssaultScene`: после захвата не финальной точки создаёт небольшое подкрепление обычных врагов.

`RegionLiberationSystem` слушает `RegionLiberatedEvent` и обновляет `GameState`.

`RegionLiberationSystem` не знает конкретные связи регионов и только вызывает `GameState.mark_liberated()`.

### `src/events/`

Содержит dataclass-события игры. Сейчас есть `EnemyKilledEvent`, `OutpostClearedEvent`, `QuestCompletedEvent`, `CapturePointTakenEvent` и `RegionLiberatedEvent`.

### `src/ui/`

Содержит простой `HUD` и `DebugOverlay`.

### `src/world/`

Содержит тайловую карту и типы тайлов.

`TileMap.is_tile_blocked(tile_x, tile_y)` проверяет блокировку по tile coordinates.

`TileMap.is_point_blocked(x, y)` проверяет блокировку по pixel coordinates.

`TileMap.is_blocked(x, y)` оставлен как compatibility alias для старого pixel-coordinate API.

Алгоритмы вроде Flood fill используют tile-coordinate API.

Также содержит `RegionState` — модель глобального состояния региона, которая не является ECS-сущностью.

`RegionState` хранит `unlocks_on_liberation` — явный список регионов, которые нужно открыть после освобождения текущего региона.

### `data/regions/regions.json`

Содержит стартовые данные 5 регионов Crown Reclaim.

### `tests/`

Содержит тесты для карты, ECM, фабрики сущностей, систем, UI и сцены региона.

---

## Что ещё не реализовано

Следующие механики ещё не являются существующей архитектурой и должны добавляться отдельными шагами:

- GameState поражения и глобальная логика смерти игрока;
- SettingsScene;
- SettingsManager;
- SaveManager;
- Continue и реальные сохранения;
- камера;
- полноценный QuestSystem;
- диалоги;
- BSP-генерация замка;
- полноценные связи и дороги между регионами;
- граф регионов;
- A*;
- Behavior Tree;
- Spatial Grid;
- сохранения.
