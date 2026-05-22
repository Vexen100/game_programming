# Игровые сущности

## Назначение документа

Этот документ описывает текущее состояние игровых сущностей в ECS-архитектуре Crown Reclaim.

Сущности не должны возвращаться к отдельным классам игровых объектов. На текущем этапе игрок и враг являются числовыми `entity_id` с набором компонентов.

---

## Player

Игрок — ECS-сущность, создаваемая через `EntityFactory.create_player()`.

Текущий набор компонентов:

```text
Player = entity_id + Position + Velocity + Collider + Renderable + Health + PlayerControlled + AttackIntent + MeleeAttack
```

На текущем этапе игрок:

- управляется через `PlayerInputSystem`;
- двигается через `MovementSystem`;
- сталкивается со стенами через `CollisionSystem`;
- отправляет намерение атаки через `PlayerAttackInputSystem`;
- наносит урон врагу через `MeleeAttackSystem`;
- может получать урон от врага;
- помечается `PlayerDefeated`, если `Health.current <= 0`;
- рисуется через `RenderSystem`;
- отображает здоровье через `HUD`;
- может показываться в `DebugOverlay`.

Если здоровье игрока падает до `0`, игрок получает `PlayerDefeated`. После этого `RegionScene` не запускает gameplay-системы, а `HUD` показывает сообщение поражения. По `R` текущая `RegionScene` перезапускает локальное состояние региона.

Игрок не удаляется через `CleanupSystem`. `Dead` не используется для игрока. GameState поражения пока не реализован.

Игрок не является отдельным классом `Player`.

---

## Enemy

Враг — ECS-сущность, создаваемая через `EntityFactory.create_enemy()`.

Текущий набор компонентов:

```text
Enemy = entity_id + Position + Velocity + Collider + Renderable + Health + Enemy + ChaseBehavior + MeleeAttack
```

На текущем этапе враг:

- создаётся в `RegionScene`;
- замечает игрока в радиусе обнаружения;
- двигается к игроку через `EnemyChaseSystem`, `MovementSystem` и `CollisionSystem`;
- наносит урон игроку через `EnemyAttackSystem`;
- помечается `Dead`, если `Health.current <= 0`;
- удаляется через `CleanupSystem`, если помечен `Dead`;
- рисуется через `RenderSystem`;
- учитывается в `DebugOverlay` как живая сущность.

`ChaseBehavior` хранит только параметры преследования. Логика преследования находится в `EnemyChaseSystem`.

Враг может получать урон от игрока. Если здоровье врага падает до `0`, он помечается `Dead` и удаляется через `CleanupSystem`.

При первом переходе врага в `Dead` публикуется `EnemyKilledEvent`. Это событие может менять влияние региона через `InfluenceSystem`.

Враг не является отдельным классом `Enemy`.

---

## Outpost

Аванпост — ECS-сущность, создаваемая через `EntityFactory.create_outpost()`.

Текущий набор компонентов:

```text
Outpost = entity_id + Position + Renderable + Outpost
```

На текущем этапе аванпост:

- создаётся в `RegionScene`;
- не блокирует движение, потому что у него нет `Collider`;
- не имеет здоровья;
- считается зачищенным, если игрок находится рядом и рядом нет живых врагов;
- меняет цвет после зачистки;
- публикует `OutpostClearedEvent` при первой зачистке.

`OutpostClearedEvent` может менять влияние региона через `InfluenceSystem`.

Аванпост не является `CapturePoint`. Точки захвата относятся к будущей `CastleAssaultScene`.

## NPC

NPC — ECS-сущность, создаваемая через `EntityFactory.create_npc()`.

Текущий набор компонентов:

```text
NPC = entity_id + Position + Renderable + NPC
```

На текущем этапе NPC:

- создаётся в `RegionScene`;
- не блокирует движение, потому что у него нет `Collider`;
- не имеет здоровья;
- хранит простой `quest_id`;
- хранит id аванпоста, который должен быть зачищен;
- завершает задание при взаимодействии по `E`, если игрок рядом и аванпост зачищен;
- меняет цвет после завершения задания;
- публикует `QuestCompletedEvent` при первом завершении задания.

`QuestCompletedEvent` может менять влияние региона через `InfluenceSystem`.

NPC не является полноценным `QuestSystem`. Диалоги пока не реализованы.

---

## TileMap

Карта хранится как двумерный список тайлов.

Текущие типы тайлов:

- `FLOOR`;
- `WALL`.

`TileMap` отвечает за:

- перевод координат тайлов в пиксели;
- перевод пикселей в координаты тайлов;
- проверку блокировки точки;
- проверку блокировки прямоугольника;
- отрисовку тайлов.

---

## RegionState

`RegionState` хранит глобальное состояние региона:

- `id`;
- `name`;
- `unlocked`;
- `control_state`;
- `player_influence`;
- `enemy_influence`;
- `assault_unlocked`;
- `liberated`.

`RegionState` используется глобальным `GameState`.

`WorldMapScene` отображает регионы из `GameState`. Выбор открытого региона меняет `current_region_id`. Закрытый регион выбрать для входа нельзя.

`WorldMapScene` отображает `player_influence`, `enemy_influence` и `assault_unlocked` выбранного региона.

Возврат из `RegionScene` на карту не пересоздаёт `GameState`.

`InfluenceSystem` меняет `player_influence` и `enemy_influence` при `EnemyKilledEvent`, `OutpostClearedEvent` и `QuestCompletedEvent`. Если влияние врага падает достаточно низко, выставляется `assault_unlocked`.

Если `assault_unlocked == True`, `WorldMapScene` может открыть `CastleAssaultScene` по `C`.

Сам флаг `assault_unlocked` не освобождает регион.

Освобождение региона и точки захвата будут отдельным шагом.

`RegionState` не является игровой ECS-сущностью, не содержит компонентов и не рисуется через `RenderSystem`.

---

## Текущее правило для сущностей

Компоненты хранят данные и не содержат игровой логики.

Системы выполняют логику:

- ввод;
- движение;
- преследование врага;
- атака игрока;
- атака врага;
- поражение игрока;
- зачистка аванпоста;
- взаимодействие с NPC;
- cleanup мёртвых сущностей;
- столкновения;
- отрисовка.

`EntityFactory` только создаёт `entity_id`, добавляет компоненты и возвращает созданную сущность.

---

## Будущие шаги

Позже отдельными шагами могут быть добавлены:

- GameState поражения;
- полноценный QuestSystem;
- диалоги;
- CapturePoint;
- точки захвата в замке;
- освобождение региона.
