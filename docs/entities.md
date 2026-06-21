# Игровые сущности

## Назначение документа

Этот документ описывает текущее состояние игровых сущностей в ECS-архитектуре Crown Reclaim.

Сущности не должны возвращаться к отдельным классам игровых объектов. На текущем этапе игрок и враг являются числовыми `entity_id` с набором компонентов.

---

## Player

Игрок — ECS-сущность, создаваемая через `EntityFactory.create_player()`.

Текущий набор компонентов:

```text
Player = entity_id + Position + Velocity + Collider + Renderable + Sprite + Health + PlayerControlled + AttackIntent + FacingDirection + AttackHitbox + MeleeAttack
```

На текущем этапе игрок:

- управляется через `PlayerInputSystem`;
- двигается через `MovementSystem`;
- сталкивается со стенами через `CollisionSystem`;
- отправляет намерение атаки через `PlayerAttackInputSystem`;
- хранит последнее направление движения в `FacingDirection`;
- наносит урон врагу через направленный `AttackHitbox` в `MeleeAttackSystem`;
- кратко показывает active attack hitbox после атаки;
- видит feedback cooldown атаки в `HUD`;
- может получать урон от врага;
- помечается `PlayerDefeated`, если `Health.current <= 0`;
- рисуется через `RenderSystem`;
- отображает здоровье через `HUD`;
- может показываться в `DebugOverlay`.

Размер collider/render игрока меньше `TILE_SIZE`, чтобы проходы не требовали пиксель-в-пиксель выравнивания.

Если здоровье игрока падает до `0`, игрок получает `PlayerDefeated`. После этого `RegionScene` не запускает gameplay-системы, а `HUD` показывает сообщение поражения. По `R` текущая `RegionScene` восстанавливает игрока на spawn tile без полного сброса региона.

После recover в `RegionScene` сохраняются cleared outpost, completed NPC quest и уже удалённые enemies.

Игрок не удаляется через `CleanupSystem`. `Dead` не используется для игрока. GameState поражения пока не реализован.

Игрок не является отдельным классом `Player`.

`AttackHitbox.width/height` у игрока — runtime-rect активного удара для отрисовки. Базовый размер атаки берётся из `PlayerSettings`.

Close-contact melee fallback не добавляет новые компоненты и не меняет entity schema игрока. Если enemy AABB пересекается с body AABB игрока, `MeleeAttackSystem` может засчитать попадание как safety-case для физического overlap, но visible attack hitbox остаётся направленным.

Save snapshot обычного региона тоже не добавляет новые ECS components.

---

## Enemy

Враг — ECS-сущность, создаваемая через `EntityFactory.create_enemy()`.

Текущий набор компонентов:

```text
Enemy = entity_id + Position + Velocity + Collider + Renderable + Sprite + Health + Enemy + ChaseBehavior + MeleeAttack + AttackHitbox + EnemyAttackState (+ PatrolRoute)
```

На текущем этапе враг:

- создаётся в `RegionScene`;
- может существовать в нескольких экземплярах в одной сцене;
- может иметь `PatrolRoute`;
- в замке может появляться как подкрепление после захвата точки;
- замечает игрока в радиусе обнаружения;
- двигается к игроку через `EnemyChaseSystem`, `MovementSystem` и `CollisionSystem`;
- готовит удар через `EnemyAttackState`;
- показывает AABB hitbox атаки через `AttackHitbox`;
- наносит урон игроку через `EnemyAttackSystem` после windup, если игрок остался внутри hitbox;
- помечается `Dead`, если `Health.current <= 0`;
- удаляется через `CleanupSystem`, если помечен `Dead`;
- рисуется через `RenderSystem`;
- отображает HP bar через `RenderSystem.draw_enemy_health_bars()`, пока не помечен `Dead`;
- учитывается в `DebugOverlay` как живая сущность.

Размер collider/render врага меньше `TILE_SIZE`, чтобы враги стабильнее проходили по тайловым коридорам.

`ChaseBehavior` хранит только параметры преследования. Логика преследования находится в `EnemyChaseSystem`.

`EnemyAttackState` хранит только runtime-состояние вражеской атаки: длительность подготовки, текущий windup timer, recovery timer и флаг pending.

`AttackHitbox` у врага — runtime-прямоугольник предупреждения и короткой flash-отрисовки после resolve атаки. Прямоугольник фиксируется в момент начала windup и не следует за игроком.

Если игрок выходит из enemy attack hitbox до конца windup, атака промахивается и урон не наносится.

`AttackHitbox` используется и игроком, и врагом, но игровая логика разная: игрок строит hitbox по `FacingDirection` в `MeleeAttackSystem`, враг строит hitbox по направлению к игроку в `EnemyAttackSystem`.

`PatrolRoute` хранит только список patrol tiles, текущий индекс и optional wait timer.

Логика patrol находится в `EnemyChaseSystem`, а не в компоненте.

Маршрут с менее чем двумя tile не считается полноценным patrol-маршрутом: враг останавливается, а path cache для него очищается.

В `RegionScene` и `CastleAssaultScene` враг использует LOS по тайлам, last seen memory, A* pathfinding и patrol fallback.

Враг начинает A* преследование только если игрок находится в радиусе обнаружения и есть line of sight.

Если игрок пропал за стеной после обнаружения, враг короткое время идёт к last seen tile.

Last seen memory хранится внутри `EnemyChaseSystem`.

Last seen memory не является компонентом и не хранится в `ChaseBehavior`.

Если игрок не виден и active last seen memory нет, враг с `PatrolRoute` идёт по маршруту.

Если путь к last seen tile недоступен или устарел, враг очищает last seen memory и переходит к patrol fallback или останавливается.

Системы работают с врагами через ECS-запросы, а не через один общий `enemy_id`.

Подкрепление в замке — это всё ещё обычные Enemy ECS-сущности.

Враг может получать урон от игрока. Если здоровье врага падает до `0`, он помечается `Dead` и удаляется через `CleanupSystem`.

При попадании игрока враг может получить небольшой knockback. Если в `MeleeAttackSystem` передан `tile_map`, knockback не двигает врага в стену.

Если центры игрока и врага совпали, knockback использует `FacingDirection` атаки, а не фиксированное направление вправо.

При первом переходе врага в `Dead` публикуется `EnemyKilledEvent`. Это событие может менять влияние региона через `InfluenceSystem`.

Враг не является отдельным классом `Enemy`.

Save snapshot сохраняет defeated enemies как indexes внутри `RegionScene.enemy_ids`, а не как raw entity objects и не как полный ECS dump.

---

## Outpost

Аванпост — ECS-сущность, создаваемая через `EntityFactory.create_outpost()`.

Текущий набор компонентов:

```text
Outpost = entity_id + Position + Renderable + Sprite + Outpost
```

На текущем этапе аванпост:

- создаётся в `RegionScene`;
- не блокирует движение, потому что у него нет `Collider`;
- не имеет здоровья;
- хранит `clear_duration`;
- хранит текущий `clear_progress`;
- очищается через короткое удержание `E`, если игрок находится рядом и рядом нет живых врагов;
- не очищается автоматически только из-за близости игрока;
- меняет цвет после зачистки;
- публикует `OutpostClearedEvent` при первой зачистке.

`Outpost.cleared` остаётся финальным state-флагом зачистки.

`clear_progress` сбрасывается, если игрок ушёл, перестал удерживать `E` или рядом есть живой враг.

`OutpostClearedEvent` может менять влияние региона через `InfluenceSystem`.

Аванпост не является `CapturePoint`. Точки захвата используются только в `CastleAssaultScene`.

## NPC

NPC — ECS-сущность, создаваемая через `EntityFactory.create_npc()`.

Текущий набор компонентов:

```text
NPC = entity_id + Position + Renderable + Sprite + NPC
```

На текущем этапе NPC:

- создаётся в `RegionScene`;
- не блокирует движение, потому что у него нет `Collider`;
- не имеет здоровья;
- хранит простой `quest_id`;
- хранит id аванпоста, который должен быть зачищен;
- хранит `report_duration`;
- хранит текущий `report_progress`;
- завершает задание через короткое удержание `E`, если игрок рядом и аванпост зачищен;
- меняет цвет после завершения задания;
- публикует `QuestCompletedEvent` при первом завершении задания.

`NPC.quest_completed` остаётся финальным state-флагом завершения задания.

`report_progress` сбрасывается, если игрок ушёл, перестал удерживать `E` или требуемый аванпост ещё не зачищен.

`QuestCompletedEvent` может менять влияние региона через `InfluenceSystem`.

NPC не является полноценным `QuestSystem`. Диалоги пока не реализованы.

---

## CapturePoint

Точка захвата — ECS-сущность, создаваемая через `EntityFactory.create_capture_point()`.

Текущий набор компонентов:

```text
CapturePoint = entity_id + Position + Renderable + Sprite + CapturePoint
```

На текущем этапе точка захвата:

- создаётся только в `CastleAssaultScene`;
- не блокирует движение, потому что у неё нет `Collider`;
- не имеет здоровья;
- хранит радиус захвата;
- хранит прогресс захвата от `0` до `100`;
- хранит владельца;
- считается захваченной, если игрок находится рядом достаточно времени и рядом нет живых врагов;
- меняет цвет после захвата;
- публикует `CapturePointTakenEvent` при первом захвате.

Если все точки захвата в замке захвачены, `CaptureSystem` публикует `RegionLiberatedEvent`.

После захвата всех точек `CastleAssaultScene` локально завершает штурм через `assault_completed`.

`CaptureSystem` не знает про `GameState`. `RegionLiberationSystem` получает `RegionLiberatedEvent` через `EventBus` и вызывает `GameState.mark_liberated()`.

---

## Sprite

`Sprite` — простой ECS-компонент для sprite-ready rendering.

Текущий формат:

```text
Sprite = asset_key
```

Компонент хранит только строковый ключ asset.

`Sprite` не хранит `pygame.Surface`, путь к файлу, sprite sheet index, animation state или runtime-кэш.

`Renderable` остаётся рядом со `Sprite` и продолжает задавать размер и fallback-цвет.

Если `RenderSystem` получает `ResourceManager`, он может получить surface по `Sprite.asset_key`.

Сейчас default keys `player`, `enemy`, `outpost_enemy`, `npc_active` и `capture_point_enemy` могут загружать static PNG из `assets/images/entities/`.

Если `ResourceManager` не передан или реального изображения нет, сущность всё равно рисуется через generated placeholder или старый rectangle fallback.

`Sprite` пока не управляет кадрами walk/attack animation.

---

## TileMap

Карта хранится как двумерный список тайлов.

Текущие типы тайлов:

- `FLOOR`;
- `WALL`;
- `GRASS`;
- `DIRT`;
- `ROAD`;
- `RUINS_FLOOR`;
- `WATER`;
- `FOREST`;
- `BRIDGE`.
- `CASTLE_FLOOR`;
- `CASTLE_WALL`;
- `CRACKED_STONE_FLOOR`;
- `DARK_CORRIDOR_FLOOR`.

`WALL`, `WATER`, `FOREST` и `CASTLE_WALL` блокируют движение.

`FLOOR`, `GRASS`, `DIRT`, `ROAD`, `RUINS_FLOOR`, `BRIDGE`, `CASTLE_FLOOR`, `CRACKED_STONE_FLOOR` и `DARK_CORRIDOR_FLOOR` проходимы.

`TileMap` отвечает за:

- перевод координат тайлов в пиксели;
- перевод пикселей в координаты тайлов;
- проверку блокировки точки;
- проверку блокировки прямоугольника;
- отрисовку тайлов;
- отрисовку с optional camera offset;
- отрисовку через optional `ResourceManager`.

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
- `unlocks_on_liberation`.

`RegionState` используется глобальным `GameState`.

`WorldMapScene` отображает регионы из `GameState`. Выбор открытого региона меняет `current_region_id`. Закрытый регион выбрать для входа нельзя.

`WorldMapScene` отображает `player_influence`, `enemy_influence` и `assault_unlocked` выбранного региона.

`RegionScene` тоже показывает текущее влияние региона в gameplay HUD.

Возврат из `RegionScene` на карту не пересоздаёт `GameState`.

Повторный вход в тот же region_id в рамках текущего запуска не пересоздаёт `RegionScene`: `Game` хранит in-memory cache сцен по `region_id`.

Это сохраняет runtime progress внутри объекта сцены и дополняется минимальным disk snapshot для Continue.

Save snapshot обычного региона хранит defeated enemy indexes, cleared outpost keys, completed NPC keys, player position и player health.

Save snapshot не сериализует ECS напрямую и не хранит PyGame objects.

`InfluenceSystem` меняет `player_influence` и `enemy_influence` при `EnemyKilledEvent`, `OutpostClearedEvent` и `QuestCompletedEvent`. Если влияние врага падает достаточно низко, выставляется `assault_unlocked`.

Если `assault_unlocked == True`, `WorldMapScene` может открыть `CastleAssaultScene` по `C`.

Сам флаг `assault_unlocked` не освобождает регион.

Регион освобождается после `RegionLiberatedEvent`, который публикуется при захвате всех точек в `CastleAssaultScene`.

После освобождения регион может открыть следующие регионы из `unlocks_on_liberation`.

Это явный список в данных, а не граф маршрутов, дороги или система распространения влияния.

`RegionState` не является игровой ECS-сущностью, не содержит компонентов и не рисуется через `RenderSystem`.

---

## Runtime SpatialIndex

`SpatialIndex` и `UniformGrid` не являются ECS-сущностями и не добавляются как компоненты.

Они хранят только runtime `entity_id` и AABB объектов, построенные из текущего ECS-состояния сцены.

`SpatialIndexSystem` строит enemy index из живых врагов с `Enemy`, `Position` и `Collider`.

Индекс временный: `RegionScene` и `CastleAssaultScene` перестраивают его во время update после движения и столкновений.

Сами сущности не меняются. Компоненты `Enemy`, `Position`, `Collider`, `Dead` остаются источником правды.

---

## Текущее правило для сущностей

Компоненты хранят данные и не содержат игровой логики.

Текущее MVP-состояние проекта описано в `docs/mvp_checkpoint.md`. Этот checkpoint не добавляет новые компоненты и не меняет entity schema; он фиксирует, какие gameplay loops уже связаны через существующие сущности, события и системы.

Системы выполняют логику:

- ввод;
- движение;
- преследование врага;
- атака игрока;
- атака врага;
- поражение игрока;
- зачистка аванпоста;
- взаимодействие с NPC;
- захват точек в замке;
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
- открытие соседних регионов;
- полноценные связи и дороги регионов;
- граф регионов;
- генерация замка.
