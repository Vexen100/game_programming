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
- `tests/`

---

## Основные модули

### `main.py`

Точка входа в игру. Создаёт `Game` и запускает главный цикл.

### `settings.py`

Файл с базовыми настройками и action-константами.

### `src/core/game.py`

Создаёт окно, `InputManager`, `SceneManager`, регистрирует `RegionScene` и запускает цикл `handle_events -> update -> draw`.

### `src/core/input_manager.py`

Обрабатывает клавиатуру и отдаёт действия через строковые action-константы.

### `src/core/scene_manager.py`

Регистрирует сцены и переключает текущую сцену по запросу.

### `src/scenes/region_scene.py`

Создаёт тестовую карту, ECS-слой, игрока, врага, системы, HUD и debug overlay.

### `src/ecs/entity_component_manager.py`

Хранит сущности, теги и компоненты по типам.

### `src/components/components.py`

Содержит dataclass-компоненты: `Position`, `Velocity`, `Collider`, `Renderable`, `Health`, `PlayerControlled`, `Enemy`, `Dead`, `ChaseBehavior`, `AttackIntent`, `MeleeAttack`.

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
- `CleanupSystem`;
- `RenderSystem`.

### `src/ui/`

Содержит простой `HUD` и `DebugOverlay`.

### `src/world/`

Содержит тайловую карту и типы тайлов.

### `tests/`

Содержит тесты для карты, ECM, фабрики сущностей, систем, UI и сцены региона.

---

## Что ещё не реализовано

Следующие механики ещё не являются существующей архитектурой и должны добавляться отдельными шагами:

- смерть игрока и GameState поражения;
- GameState;
- EventBus;
- меню;
- камера;
- точки захвата;
- NPC;
- аванпосты.
