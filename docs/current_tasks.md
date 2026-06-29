# Текущие задачи ядра проекта

## Цель первого прототипа

Создать минимальную играбельную версию игры без графики, сюжета, красивого интерфейса и сложных систем.

Прототип должен ответить на главный вопрос:

> «Работает ли основной игровой цикл и интересно ли в это играть?»

Все объекты на данном этапе всё ещё должны быть максимально простыми:
- игрок, враги, аванпосты и NPC уже могут использовать static PNG через `ResourceManager`;
- игрок и враги уже могут использовать минимальную idle/walk animation через `Animation`;
- player attack и enemy windup могут запрашивать visual-only attack animation;
- `ResourceManager` сохраняет generated placeholder fallback, если PNG отсутствует;
- `Renderable` остаётся fallback для прямоугольной отрисовки.

На этом этапе НЕ нужны:
- attack animation events;
- animation events;
- hitbox timing sync;
- сложные эффекты;
- звук;
- финальный production art pass карты;
- сюжет;
- полноценный QuestSystem;
- диалоги;
- сложная система сохранений;
- настройки.

---

# Минимальное играбельное ядро

Текущее состояние зафиксировано как playable vertical prototype в `docs/mvp_checkpoint.md`.

Дальше разработка должна ориентироваться на milestone-цели, а не на буквальное совпадение номера шага со старым крупным планом.

## 1. Управление игроком

Реализовать:
- движение в 4 направлениях;
- столкновения со стенами;
- направленную атаку;
- видимый hitbox атаки;
- здоровье;
- HP bars живых врагов;
- knockback при попадании;
- feedback cooldown атаки;
- смерть/recover в обычном регионе;
- restart challenge-сцены замка.

Цель:
- получить базовое ощущение управления и движения.

---

## 2. Базовый ИИ врага

Реализовать один тип врага:
- патрулирует;
- замечает игрока в радиусе;
- проверяет LOS по тайлам;
- преследует игрока через A* вокруг стен;
- коротко помнит last seen tile;
- атакует;
- умирает при потере здоровья.

Цель:
- протестировать бой и взаимодействие.

---

## 3. Обычная карта региона

Создать одну вручную сделанную карту Old Ruins:
- больше viewport, чтобы camera реально использовалась;
- несколько типов тайлов для читаемости;
- forest/water blockers;
- дороги, мосты и руины;
- открытые зоны для боя;
- больше пространства для перемещения;
- критические проходы минимум в два adjacent walkable tiles;
- минимум два аванпоста;
- минимум два NPC с простыми заданиями на зачистку связанных аванпостов;
- точка появления игрока;
- несколько групп врагов и patrol routes.

Цель:
- получить контролируемую среду для тестирования механик.

---

## 4. Система боя

Реализовать:
- нанесение урона;
- задержку между атаками;
- здоровье игрока и врагов;
- enemy HP bars для живых врагов;
- направленный AABB hitbox игрока;
- краткую визуализацию hitbox;
- видимый AABB telegraph атаки врага с коротким windup;
- knockback;
- HUD feedback cooldown;
- смерть объектов.

Nearby enemy checks в `MeleeAttackSystem` и `EnemyAttackSystem` могут использовать временный enemy spatial index на базе `UniformGrid`.

Spatial index используется только как candidate source. Exact gameplay checks остаются внутри систем.

Enemy attack feedback больше не полностью невидимый: обычные враги получают `EnemyAttackState` и `AttackHitbox`, сначала показывают прямоугольник удара, а урон наносят после windup только если игрок остался внутри hitbox. Enemy windup также может запрашивать visual-only attack animation, если frames есть. Это всё ещё не sound feedback и не сложная effects system.

Цель:
- проверить, насколько работает экшен-составляющая игры.

---

## 5. Ослабление обычного региона

В обычной `RegionScene` используются:
- несколько групп врагов;
- два аванпоста;
- один supply cache / склад снабжения;
- две NPC-задачи после зачистки связанных аванпостов.

Ручная карта обычного региона проходит Flood fill / BFS validation при создании.

Смерть игрока в обычном регионе ведёт к recover/respawn без полного сброса зачистки.

Аванпост:
- очищается через короткое удержание `E`, если игрок находится рядом и рядом нет живых врагов;
- показывает progress зачистки в contextual prompt;
- не очищается автоматически;
- меняет цвет после зачистки;
- публикует `OutpostClearedEvent`.

Supply cache:
- создаётся из `RegionLayout`;
- уничтожается через короткое удержание `E`, если игрок рядом и рядом нет живой охраны;
- показывает progress уничтожения или просьбу зачистить охрану в contextual prompt;
- публикует `SupplyCacheDestroyedEvent`;
- меняет influence через существующую цепочку `EventBus -> InfluenceSystem`;
- сохраняется в runtime snapshot как destroyed key, без сериализации ECS.

NPC:
- завершает простое задание через короткое удержание `E`, если игрок рядом и аванпост уже зачищен;
- показывает progress сдачи задания в contextual prompt;
- публикует `QuestCompletedEvent`.

Цель:
- проверить обычный цикл ослабления региона перед будущим штурмом замка.

`CapturePoint` не добавляется в обычную `RegionScene`. Точки захвата используются в `CastleAssaultScene`.

Nearby enemy check для outpost может использовать временный enemy spatial index на базе `UniformGrid`.

Для outpost spatial index работает как broadphase через `query_rect()`, а старая exact distance-проверка остаётся в `OutpostSystem`.

---

## 6. Навигационный каркас

На текущем этапе уже есть:
- минимальное главное меню;
- рабочий `Продолжить`, если single-slot save существует;
- подтверждение удаления прогресса при `Новая игра`, если save уже есть;
- минимальная пауза;
- mouse click по конкретным пунктам в главном меню, паузе и карте мира;
- старт игры через видимый пункт `Новая игра`;
- возврат из паузы через видимый пункт `Продолжить`;
- выход из паузы на карту регионов;
- возврат из Pause -> WorldMap назад в ту же gameplay-сцену через `Esc` или `M`;
- выход из паузы в главное меню.
- открытие карты мира поверх gameplay по `M`;
- возврат из карты мира назад в gameplay по `Esc` или `M`;
- fullscreen toggle по `F11`.

Основные visible UI strings в HUD, меню, паузе и карте мира переведены на русский через простой файл констант `src/ui/texts.py`.

`Продолжить` загружает single-slot save через `SaveManager`.

`Настройки` в главном меню пока является заглушкой до SettingsScene.

---

## 7. Базовая система влияния

Минимальная реализация:
- у территории есть значение влияния;
- игрок увеличивает своё влияние через игровые события;
- убийство врага, зачистка аванпоста, уничтожение supply cache и завершение NPC-задачи меняют влияние региона.
- влияние текущего региона видно прямо в gameplay HUD `RegionScene`.

Без сложной стратегии и симуляции фронта.

Цель:
- проверить основу механики «живой войны».

---

## 8. Штурм замка

В `CastleAssaultScene` уже есть:
- procedural BSP layout замка;
- layout 72x48 тайлов, который больше viewport;
- camera follow для просмотра большого замка;
- castle-specific visual tile ids: stone floor, cracked stone, dark corridor и castle wall;
- короткий `castle_layout_fingerprint` для диагностики layout;
- widened corridors for playability;
- игрок;
- несколько обычных врагов;
- точки захвата, включая финальную точку в final room;
- стартовые enemies рядом с capture points как guards;
- минимальная волна подкрепления после захвата не финальной точки;
- проверка достижимости важных тайлов через Flood fill / BFS;
- A* преследование врагов вокруг стен;
- простой path cache и rebuild interval для A* в замке;
- LOS по тайлам перед началом преследования;
- last seen / hysteresis для врагов в замке;
- patrol routes из нескольких точек для стартовых врагов;
- базовый бой;
- локальный restart;
- возврат на карту.

API `TileMap` теперь явно различает tile checks и pixel checks.

При создании и локальном restart procedural castle layout проверяет, что игрок, все враги, все точки захвата, wave spawn tiles и final room tile находятся на достижимых тайлах.

BSP core реализован и подключён к `CastleAssaultScene`.

Static castle test map заменён на procedural BSP layout.

Procedural castle теперь не просто подключён: generator задаёт playability constraints для ширины коридоров, финальной capture point, guard enemy spawns и wave spawn tiles.

Текущий штурм всё ещё минимальный: capture points, waves и liberation.

Doors, traps, decorations, lighting, room themes, boss/final room gameplay и сохранение runtime штурма ещё не реализованы.

Behavior Tree, глобальные контратаки, оборона регионов и разные типы врагов ещё не реализованы.

Более сложная оптимизация pathfinding, Behavior Tree, SpatialHashing и QuadTree ещё не реализованы.

Первый `SpatialIndex` backend уже реализован отдельно от pathfinding: `UniformGrid` используется для nearby enemy queries в combat/outpost/capture checks.

Точки захвата:
- захватываются, если игрок находится рядом и рядом нет живых врагов;
- меняют цвет после захвата;
- публикуют `CapturePointTakenEvent`.

Nearby enemy check для capture points может использовать временный enemy spatial index.

Для capture points spatial index тоже работает как broadphase через `query_rect()`, а старая exact distance-проверка остаётся в `CaptureSystem`.

После захвата всех точек:
- публикуется `RegionLiberatedEvent`;
- `RegionLiberationSystem` обновляет `GameState`;
- регион становится освобождённым и контролируется игроком.
- следующие регионы из `unlocks_on_liberation` становятся доступными.
- `CastleAssaultScene` локально завершает штурм через `assault_completed`;
- игрок видит сообщение вернуться на карту мира.

Отдельная `VictoryScene` пока не реализована.

Автоматическое вычисление соседних регионов пока не реализовано.

Полноценные связи регионов, дороги, графовая логика и распространение влияния по сети регионов пока не реализованы.

## 9. Обычный регион после readability pass

В `RegionScene` теперь есть:
- большая ручная карта;
- несколько readable tile types;
- camera follow за игроком;
- несколько enemy groups;
- два outposts;
- один supply cache;
- два NPC;
- LOS по тайлам;
- A* pathfinding;
- path cache и rebuild interval через `EnemyChaseSystem`;
- last seen / hysteresis;
- fallback к patrol/stop, если last seen path недоступен;
- patrol routes;
- layout validation через Flood fill / BFS;
- recover после defeat без полного сброса региона;
- contextual prompts для outpost, supply cache и NPC с progress при удержании `E`;
- gameplay HUD с текущим влиянием игрока/врага, счётчиками objectives/enemies и статусом штурма;
- sprite-ready PNG rendering через `ResourceManager`, `Sprite` и `Renderable` fallback;
- idle/walk animation для player/enemy через `AnimationSystem`;
- visual-only attack animation request для player attack и enemy windup;
- normalized animation frame footprint для player/enemy, чтобы static/walk/attack не меняли визуальный размер;
- chroma/alpha cleanup animation frames в asset pipeline, чтобы bright chroma remnants, dark/medium green-dominant remnants и hidden RGB garbage не попадали в runtime;
- runtime combat feedback: hit flash, damage popup и короткий slash effect;
- временный enemy spatial index на базе `UniformGrid` для nearby enemy checks;
- видимый AABB telegraph атаки врага;
- in-session continuity через cached `RegionScene` по `region_id`;
- minimal disk persistence через `SaveManager`;
- partial runtime snapshot обычной `RegionScene`;
- запуск штурма по `C`, если `assault_unlocked == True`.

Assault unlock стал сложнее: outpost alone, supply cache alone, one outpost + one NPC quest и полный non-combat objective loop без combat contribution больше не открывают штурм.

Ожидаемый путь к unlock теперь требует более полного регионального цикла: два outposts, supply cache, два NPC quests и combat contribution.

Повторный выбор того же региона на карте больше не сбрасывает текущую `RegionScene` в рамках одного запуска игры: cleared outposts, destroyed supply cache, completed NPC quests, removed enemies, позиция игрока и runtime timers остаются внутри cached scene object.

Close-contact melee overlap исправлен: если enemy пересекается с player body AABB, направленная атака игрока попадает даже в ситуации физического наложения collider-ов.

Partial region resurgence / reinforcements while away пока не реализованы. Уход из региона сам по себе не создаёт новых врагов и не меняет influence автоматически.

Disk persistence сохраняет `GameState` и минимальный snapshot обычной `RegionScene`: defeated enemy indexes, cleared outpost keys, destroyed supply cache keys, completed NPC keys, player position и player health.

Corrupted save не чинится и не удаляется автоматически. `Continue` при повреждённом save-файле не делает fallback в `New Game`, не сбрасывает world state и не открывает `WorldMapScene`; полноценный UI ошибки save-файла пока не реализован.

CastleAssaultScene runtime, waves state, path cache, AI memory, attack hitbox timers и partial outpost/supply cache/NPC progress не сохраняются.

Это всё ещё ручной прототип: первый static PNG pass, idle/walk animation, visual-only attack animation, normalized animation frame footprint, chroma/alpha cleanup animation frames включая dark/medium green remnants и базовый combat feedback подключены, но полноценный production art pass, animation events, hitbox timing sync, sound, screen shake, полноценный QuestSystem, диалоговые окна, multi-slot save UI, SettingsScene и procedural ordinary regions ещё не реализованы.

## 10. MVP checkpoint

Текущий vertical prototype уже соединяет:
- стартовую карту мира;
- вход в enemy region;
- ослабление региона через enemies/outpost/NPC;
- показ influence в gameplay HUD и WorldMap;
- unlock штурма;
- вход в `CastleAssaultScene`;
- capture points;
- liberation event;
- unlock next region.

Это не означает, что игра готова. Multi-slot save UI, manual save menu, CastleAssault runtime save, partial region resurgence while away, SettingsScene, Behavior Tree, room theming, doors/traps/decorations, полноценный production art pass, animations и sound ещё не реализованы.

---

# Критерии успешного прототипа

Первый прототип считается успешным, если:
- управление ощущается нормально;
- бой работает;
- враг умеет преследовать и атаковать;
- влияние региона меняется через события обычного региона;
- `assault_unlocked` может открыться после ослабления врага;
- игровой цикл понятен и воспроизводим.

---

# Что НЕ нужно на этом этапе

Не нужно делать:
- сюжет;
- полноценные квесты;
- прокачку;
- doors/traps/decorations/room themes для процедурного замка;
- сложную систему сохранений со слотами;
- звук;
- красивый интерфейс;
- сложную графику;
- сложное меню;
- полноценные диалоги;
- полноценный QuestSystem;
- CapturePoint в обычной `RegionScene`.

---

# Приоритет разработки

## Сначала
- движение;
- столкновения;
- карта;
- бой;
- ИИ врага.

## Потом
- влияние через врагов, аванпост, supply cache и NPC-задачу;
- вход в `CastleAssaultScene` после ослабления региона;
- захват точек внутри замка;
- освобождение региона после штурма;
- несколько врагов;
- волны атак.

## Позже
- карта мира;
- polish карты мира;
- прокачка;
- квесты;
- save slots UI;
- manual save/load menu;
- SettingsScene и SettingsManager;
- полноценный SettingsManager;
- звук;
- animation events / hitbox timing sync;
- оборона территорий;
- полноценные связи регионов;
- дороги регионов;
- распространение влияния по сети регионов;
- room theming / doors / traps / decorations для процедурного замка;
- partial region resurgence while away;
- SpatialHashing;
- QuadTree;
- Behavior Tree;
- сложный ИИ.

---

# Главное правило

Не тратить время на графику слишком рано.

Квадрат, который интересно управляется и взаимодействует с механиками — уже хороший прототип.

Красивый спрайт без работающего геймплея — бесполезен.

Сначала механики.
Потом всё остальное.
