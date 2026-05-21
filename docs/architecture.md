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
- `src/core/game_state.py`
- `src/core/input_manager.py`
- `src/core/scene_manager.py`
- `src/scenes/region_scene.py`
- `src/ecs/entity_component_manager.py`
- `src/components/components.py`
- `src/entities/entity_factory.py`
- `src/entities/entities_settings.py`
- `src/systems/`
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

Создаёт окно, `InputManager`, `GameState`, `SceneManager`, регистрирует `RegionScene` и запускает цикл `handle_events -> update -> draw`.

`GameState` пока не управляет сценами, но готовит основу для будущей `WorldMapScene`.

### `src/core/game_state.py`

Хранит глобальное состояние регионов: открытие, контроль, влияние, доступность штурма и освобождение.

Загружает стартовые данные из `data/regions/regions.json`.

### `src/core/input_manager.py`

Обрабатывает клавиатуру и отдаёт действия через строковые action-константы.

### `src/core/scene_manager.py`

Регистрирует scene factories и переключает текущую сцену по запросу.

`SceneManager` сам не импортирует конкретные сцены. Текущая сцена создаётся через зарегистрированную фабрику.

### `src/scenes/region_scene.py`

Создаёт тестовую карту, ECS-слой, игрока, врага, системы, HUD и debug overlay.

### `src/ecs/entity_component_manager.py`

Хранит сущности, теги и компоненты по типам.

### `src/components/components.py`

Содержит dataclass-компоненты: `Position`, `Velocity`, `Collider`, `Renderable`, `Health`, `PlayerControlled`, `PlayerDefeated`, `Enemy`, `Dead`, `ChaseBehavior`, `AttackIntent`, `MeleeAttack`.

### `src/entities/entity_factory.py`

Создаёт типовые ECS-сущности и добавляет им компоненты.

Сейчас фабрика создаёт игрока с `AttackIntent`/`MeleeAttack` и базового врага с `ChaseBehavior`/`MeleeAttack`.

### `src/entities/entities_settings.py`

Хранит простые настройки сущностей: скорость, здоровье, размер и цвет.

### `src/systems/`

Содержит текущие ECS-системы:

- `PlayerInputSystem`;
- `PlayerAttackInputSystem`;
- `EnemyChaseSystem`;
- `MovementSystem`;
- `CollisionSystem`;
- `MeleeAttackSystem`;
- `EnemyDeathSystem`;
- `EnemyAttackSystem`;
- `PlayerDeathSystem`;
- `CleanupSystem`;
- `RenderSystem`.

### `src/ui/`

Содержит простой `HUD` и `DebugOverlay`.

### `src/world/`

Содержит тайловую карту и типы тайлов.

Также содержит `RegionState` — модель глобального состояния региона, которая не является ECS-сущностью.

### `data/regions/regions.json`

Содержит стартовые данные 5 регионов Crown Reclaim.

### `tests/`

Содержит тесты для карты, ECM, фабрики сущностей, систем, UI и сцены региона.

---

## Что ещё не реализовано

Следующие механики ещё не являются существующей архитектурой и должны добавляться отдельными шагами:

- WorldMapScene;
- переход карта регионов -> RegionScene;
- EventBus;
- InfluenceSystem;
- GameState поражения и глобальная логика смерти игрока;
- меню;
- камера;
- NPC;
- аванпосты;
- CastleAssaultScene;
- точки захвата в замке.
