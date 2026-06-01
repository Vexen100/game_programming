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
- `src/core/camera.py`
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
- `docs/mvp_checkpoint.md`
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

По `F11` переключает windowed/fullscreen через `pygame.display.set_mode(...)`.

Это минимальный fullscreen toggle без `SettingsScene`, `SettingsManager` и сохранения настройки.

### `src/core/camera.py`

Содержит минимальную `Camera`.

Камера следует за целью, clamp-ится по границам карты и умеет смещать world coordinates в screen coordinates через `apply(x, y)`.

Если карта меньше viewport, camera остаётся в `(0, 0)`.

HUD и меню не смещаются камерой.

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

Также хранит `mouse_position`, одноразовые `mouse_buttons_pressed` и отдаёт `was_mouse_pressed(button=1)`.

Мышь используется для кликов в `MainMenuScene`, `PauseScene` и `WorldMapScene`.

Mouse aiming в gameplay не добавлялся.

### `src/core/scene_manager.py`

Регистрирует scene factories и переключает текущую сцену по запросу.

`SceneManager` сам не импортирует конкретные сцены. Текущая сцена создаётся через зарегистрированную фабрику.

Также умеет временно сохранить текущую gameplay-сцену в `paused_scene` и восстановить её через `resume_scene()`.

Это минимальная пауза без полноценного stack-сцен и без overlay-rendering.

Также содержит минимальную поддержку открытия `WorldMapScene` как обзора поверх текущей gameplay-сцены:

- `open_world_map(return_scene=...)`;
- `has_world_map_return_scene()`;
- `return_from_world_map()`.

Это не полноценный stack сцен. Хранится только одна return scene для карты мира.

### `src/scenes/main_menu_scene.py`

Минимальное главное меню.

Содержит видимые пункты `Новая игра`, `Продолжить (недоступно)`, `Настройки (недоступны)` и `Выход`.

На текущем этапе `Новая игра` открывает `WorldMapScene`, а `Продолжить` и `Настройки` являются заглушками.

Пункты меню можно выбирать клавиатурой или кликом мыши по конкретному пункту.

Клик мышью вне пунктов меню ничего не активирует.

### `src/scenes/pause_scene.py`

Минимальное меню паузы.

Содержит видимые пункты `Продолжить`, `Карта регионов` и `Главное меню`.

`Продолжить` возвращает сохранённую gameplay-сцену через `SceneManager.resume_scene()`.

Пункты паузы можно выбирать клавиатурой или кликом мыши по конкретному пункту.

Клик мышью вне пунктов паузы ничего не активирует.

### `src/scenes/region_scene.py`

Создаёт крупную ручную карту, ECS-слой, игрока, несколько врагов, аванпост, одного тестового NPC, системы, HUD, camera follow и debug overlay.

Критические проходы ручной карты расширены минимум до двух adjacent floor tiles.

Может получать `GameState` и показывает название текущего региона в HUD.

HUD в `RegionScene` показывает влияние игрока, влияние врага, статус доступности штурма и флаг освобождения региона, если регион уже освобождён.

HUD не зависит напрямую от `GameState`: `RegionScene` готовит status lines, а `HUD` только отрисовывает текст.

По `M` открывает `WorldMapScene` как обзор с return scene. При возврате `GameState` сохраняется, потому что принадлежит `Game`, а не сцене.

По `Esc` может запросить `PauseScene`.

Если у текущего региона `assault_unlocked == True`, по `C` можно запросить переход в `CastleAssaultScene` прямо из региона.

В обычном регионе враги теперь используют tile-map AI через `EnemyChaseSystem.update(ecm, tile_map, dt)`: detection radius, LOS, A*, path cache, last seen memory и patrol route.

При создании проверяет достижимость player spawn, стартовых enemies, outpost, NPC и patrol route tiles через `src/algorithms/flood_fill.py`.

Если игрок побеждён, `R` восстанавливает игрока на spawn tile без полного сброса региона: cleared outpost, completed NPC quest и удалённые enemies сохраняются внутри текущей `RegionScene`.

`CapturePoint` в обычную `RegionScene` не добавлялся.

NPC завершает простое задание после зачистки аванпоста через короткое удержание `E`.

Аванпост очищается через короткое удержание `E`, если игрок рядом и рядом нет живых врагов.

`OutpostSystem` и `NPCInteractionSystem` используют progress-based hold interaction через `dt`: прогресс растёт только при удержании `E` и сбрасывается, если игрок ушёл, условие не выполнено или рядом появились блокирующие враги.

`OutpostClearedEvent` и `QuestCompletedEvent` по-прежнему публикуются один раз и остаются источником изменения влияния региона через `EventBus` и `InfluenceSystem`.

### `src/scenes/world_map_scene.py`

Показывает простую placeholder-карту регионов из `GameState`.

Позволяет выбрать открытый регион и запросить переход в `RegionScene`.

Регион можно выбрать клавиатурой или кликом мыши.

Показывает influence выбранного региона и текстовый статус `assault_unlocked`.

Если выбранный регион открыт и `assault_unlocked == True`, по `C` можно перейти в `CastleAssaultScene`.

Если карта открыта поверх gameplay-сцены, `Esc` или `M` возвращают к сохранённой gameplay-сцене.

### `src/scenes/castle_assault_scene.py`

Статическая сцена штурма замка.

Создаёт простую ручную карту замка, ECS-слой, игрока, несколько врагов, две точки захвата, базовые gameplay-системы, HUD и debug overlay.

`CastleAssaultScene` хранит список `enemy_ids`.

`enemy_id` оставлен только как alias первого врага для совместимости старого кода и тестов.

Существующие ECS-системы работают со всеми врагами через компоненты и ECS-запросы.

При создании и локальном restart проверяет достижимость игрока, всех врагов и всех точек захвата через `src/algorithms/flood_fill.py`.

Также проверяет patrol tiles стартовых врагов.

Эта проверка нужна только для validation карты замка и не используется для движения врагов.

`CastleWaveSystem` локально используется внутри `CastleAssaultScene`.

Он не подписывается на глобальный `EventBus`, не хранит `GameState` и создаёт обычных врагов через `EntityFactory`.

Это минимальная локальная механика подкреплений, а не полноценный `EnemySpawner` или `WaveManager`.

После захвата всех точек сцена переходит в локальное состояние `assault_completed`.

В состоянии `assault_completed` gameplay-системы больше не обновляются.

`M` продолжает возвращать на `WorldMapScene`, а `Esc` продолжает открывать `PauseScene`.

До завершения штурма `M` открывает карту мира как обзор с return scene.

После `assault_completed` `M` может вести на карту мира как финальный выход.

По `Esc` может запросить `PauseScene`.

Если игрок побеждён, по `R` сцена локально перезапускает штурм.

`CastleAssaultScene` не освобождает регион напрямую и не знает про `InfluenceSystem`.

Точки захвата обрабатывает `CaptureSystem`. После захвата всех точек публикуется `RegionLiberatedEvent`.

Глобальное liberation региона по-прежнему идёт через `RegionLiberatedEvent` и `RegionLiberationSystem`.

### `src/ecs/entity_component_manager.py`

Хранит сущности, теги и компоненты по типам.

### `src/components/components.py`

Содержит dataclass-компоненты: `Position`, `Velocity`, `Collider`, `Renderable`, `Health`, `PlayerControlled`, `PlayerDefeated`, `Enemy`, `EnemyAttackState`, `Outpost`, `NPC`, `CapturePoint`, `Dead`, `ChaseBehavior`, `PatrolRoute`, `AttackIntent`, `FacingDirection`, `AttackHitbox`, `MeleeAttack`.

### `src/entities/entity_factory.py`

Создаёт типовые ECS-сущности и добавляет им компоненты.

Сейчас фабрика создаёт игрока с `AttackIntent`, `FacingDirection`, `AttackHitbox` и `MeleeAttack`, базового врага с `ChaseBehavior`, `MeleeAttack`, `AttackHitbox` и `EnemyAttackState`, простой аванпост, NPC с простым заданием и точку захвата.

### `src/entities/entities_settings.py`

Хранит простые настройки сущностей: скорость, здоровье, размер и цвет.

`PlayerSettings.SIZE` и `EnemySettings.SIZE` меньше `settings.TILE_SIZE`, чтобы игрок и враги проходили по тайловым коридорам без пиксель-в-пиксель зазора.

### `src/algorithms/`

Содержит отдельные алгоритмы, которые не зависят от PyGame-сцен и ECS-систем.

`src/algorithms/flood_fill.py` реализует простой Flood fill / BFS по тайлам в 4 направлениях.

Сейчас алгоритм используется в `RegionScene` и `CastleAssaultScene` для проверки, что важные тайлы ручных карт достижимы.

Алгоритм использует tile-coordinate API `TileMap.is_tile_blocked()`.

Он не является A* и не управляет движением врагов.

`src/algorithms/pathfinding.py` содержит A* по tile coordinates.

`pathfinding.py` не зависит от PyGame, ECS и сцен.

`src/algorithms/line_of_sight.py` содержит проверку line of sight по tile coordinates.

`line_of_sight.py` не зависит от PyGame, ECS, компонентов и сцен.

`src/algorithms/spatial_index.py` содержит минимальный interface пространственного индекса.

`src/algorithms/uniform_grid.py` содержит первый backend `UniformGrid`.

`UniformGrid` работает с pixel coordinates, хранит только `entity_id` и runtime AABB объектов, не импортирует ECS и не знает про компоненты.

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
- `SpatialIndexSystem`;
- `EnemyAttackSystem`;
- `PlayerDeathSystem`;
- `CleanupSystem`;
- `RenderSystem`.

Также содержит `InfluenceSystem`, который слушает `EnemyKilledEvent`, `OutpostClearedEvent`, `QuestCompletedEvent` и меняет глобальное влияние регионов через `GameState`.

`CaptureSystem` работает только с ECS и `EventBus`: захватывает точки и публикует события.

`CastleWaveSystem` работает локально в `CastleAssaultScene`: после захвата не финальной точки создаёт небольшое подкрепление обычных врагов.

`SpatialIndexSystem` строит временный enemy index для сцены из текущего ECS-состояния.

Он создаёт `UniformGrid`, добавляет живых врагов с `Enemy`, `Position`, `Collider` и пропускает `Dead`.

`RegionScene` и `CastleAssaultScene` перестраивают enemy spatial index каждый update после `MovementSystem` и `CollisionSystem`, но до melee/capture/enemy attack checks.

`MeleeAttackSystem`, `EnemyAttackSystem`, `OutpostSystem` и `CaptureSystem` принимают optional spatial index.

Если index не передан, эти системы сохраняют старый full-scan fallback.

Если index передан, он используется только для получения кандидатов; точная проверка AABB или distance остаётся внутри системы.

В `OutpostSystem` и `CaptureSystem` spatial index используется как broadphase через `query_rect()`, а не как окончательная radius-фильтрация.

Точная distance-проверка между `Position` outpost/capture point и `Position` enemy остаётся внутри system, чтобы indexed path совпадал со старой full-scan семантикой.

`EnemyChaseSystem` сохраняет прямое преследование без `tile_map`.

В `RegionScene` и `CastleAssaultScene` враги используют LOS + A* через `EnemyChaseSystem.update(ecm, tile_map, dt)`.

Перед построением A* враг проверяет, находится ли игрок в радиусе обнаружения и есть ли line of sight по тайлам.

Tile detection для A*/LOS берёт центр collider, а не top-left координату entity.

Target position для движения по A* центрируется внутри следующего tile с учётом collider врага.

Если враг видел игрока, а потом потерял прямую видимость, он короткое время идёт к last seen tile.

Cache путей хранится внутри `EnemyChaseSystem`.

Cache не является компонентом и не хранится в `ChaseBehavior`.

Last seen memory тоже хранится внутри `EnemyChaseSystem`.

Last seen memory не является компонентом и не хранится в `ChaseBehavior`.

Если игрок не виден и active last seen memory нет, враг с `PatrolRoute` идёт по patrol tiles.

Если path к last seen tile недоступен или устарел, enemy AI очищает last seen memory и сразу переходит к patrol fallback или останавливается.

`PatrolRoute` хранит только данные маршрута. Логика patrol находится в `EnemyChaseSystem`.

`PatrolRoute` с менее чем двумя tile не запускает pathfinding и явно останавливает врага.

Если текущий patrol target недоступен, `EnemyChaseSystem` пробует следующий target маршрута без бесконечного цикла.

`MeleeAttackSystem` использует направленный AABB hitbox игрока по `FacingDirection`.

`AttackHitbox` кратко активируется для визуальной обратной связи.

`AttackHitbox.width/height` — runtime-rect активного удара для отрисовки, а не базовый конфиг размера атаки.

При попадании `MeleeAttackSystem` может применить небольшой knockback, не проталкивая врага в стену при переданном `tile_map`.

Если центры игрока и врага совпали, fallback-направление knockback берётся из `FacingDirection`.

`EnemyAttackSystem` использует `EnemyAttackState` и `AttackHitbox` для читаемой атаки врага: сначала запускается короткий windup, на земле виден зафиксированный AABB hitbox, а урон наносится только после windup, если игрок всё ещё внутри этого прямоугольника.

Enemy attack telegraph не является Behavior Tree, sprite animation, sound feedback или системой эффектов. Это минимальная runtime-визуализация прямоугольника удара.

`RenderSystem` умеет рисовать сущности с camera offset, enemy HP bars живых врагов и active attack hitboxes.

Enemy attack hitboxes рисуются отдельным warning/landed цветом, player attack hitboxes сохраняют свой цвет.

Сущности с `Dead` пропускаются при отрисовке enemy HP bars и active attack hitboxes.

`RegionLiberationSystem` слушает `RegionLiberatedEvent` и обновляет `GameState`.

`RegionLiberationSystem` не знает конкретные связи регионов и только вызывает `GameState.mark_liberated()`.

### `src/events/`

Содержит dataclass-события игры. Сейчас есть `EnemyKilledEvent`, `OutpostClearedEvent`, `QuestCompletedEvent`, `CapturePointTakenEvent` и `RegionLiberatedEvent`.

### `src/ui/`

Содержит простой `HUD`, `DebugOverlay` и `texts.py`.

`texts.py` хранит русские строковые константы для основных visible UI strings.

Это не полноценная localization/i18n-system: нет выбора языка, JSON-переводов и настроек локализации.

`HUD` показывает здоровье, название сцены/региона, cooldown атаки, дополнительные status lines и contextual prompts.

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

### `docs/mvp_checkpoint.md`

Фиксирует текущее milestone-состояние vertical prototype, честно отделяет уже работающие loops от ещё не реализованных систем и задаёт ближайший roadmap.

### `tests/`

Содержит тесты для карты, ECM, фабрики сущностей, систем, UI, сцен и acceptance-level vertical slice.

`tests/test_mvp_vertical_slice.py` проверяет текущий игровой цикл на уровне `GameState`, `EventBus`, `InfluenceSystem`, `RegionLiberationSystem` и `WorldMapScene` без запуска реального окна.

---

## Что ещё не реализовано

Следующие механики ещё не являются существующей архитектурой и должны добавляться отдельными шагами:

- GameState поражения и глобальная логика смерти игрока;
- SettingsScene;
- SettingsManager;
- SaveManager;
- Continue и реальные сохранения;
- полноценный QuestSystem;
- диалоги;
- BSP-генерация замка;
- полноценные связи и дороги между регионами;
- граф регионов;
- дальнейшая оптимизация pathfinding при необходимости;
- SpatialHashing backend;
- QuadTree backend;
- Behavior Tree;
- полноценные sprite animations;
- sound / hit effects;
- сохранения.
