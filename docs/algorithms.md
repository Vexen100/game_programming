# Планируемые алгоритмы

## Назначение документа

Этот документ описывает алгоритмы, которые могут использоваться в проекте.

Алгоритмы разделены по сложности: простые, средние и сложные.  
На первом этапе нужно реализовать только минимальный набор, необходимый для игрового ядра.

---

# Простые алгоритмы

## Движение по вектору

Используется для движения игрока и врагов.

Пример применения:
- игрок движется по нажатию клавиш;
- враг движется в сторону игрока.

Сложность: простая.

---

## Проверка столкновений

Используется для запрета прохождения через стены.

Пример применения:
- игрок упирается в стену;
- враг не проходит сквозь препятствие.

Сложность: простая.

---

## Flood fill / BFS validation

Используется для проверки достижимости важных тайлов на карте.

Пример применения:
- процедурный замок проверяет, что игрок, враги, точки захвата, wave spawns и финальная комната находятся на проходимых и достижимых тайлах;
- обычная `RegionScene` проверяет, что player spawn, стартовые enemies, outposts, NPCs и patrol route tiles достижимы;
- тесты сразу ловят сломанные ручные карты.

Сейчас реализован модуль `src/algorithms/flood_fill.py`.

Алгоритм работает по tile coordinates и обходит карту только в 4 направлениях.

Алгоритм использует `TileMap.is_tile_blocked()` и не переводит tile coordinates в pixels.

Это не A* и не поиск пути для движения врагов.

В `RegionScene` и `CastleAssaultScene` враги используют A* через `EnemyChaseSystem`, если система получает `tile_map`.

Сложность: простая.

---

## Tile variety / readable map data

Обычная `RegionScene` теперь использует несколько типов тайлов: grass, dirt, road, ruins floor, water, forest и bridge.

Это не отдельный сложный алгоритм генерации, а hand-authored readability pass поверх существующей `TileMap`.

`TileMap.is_tile_blocked()` опирается на `BLOCKING_TILES`, поэтому `WATER` и `FOREST` могут формировать препятствия, а `BRIDGE`, `ROAD` и другие walkable tiles остаются проходимыми.

Сложность: простая.

---

## ResourceManager image loading + placeholder fallback

`ResourceManager` — инфраструктура отрисовки, а не gameplay algorithm.

Он кэширует загруженные изображения и generated placeholder surfaces, чтобы `TileMap` и `RenderSystem` могли использовать PNG assets без потери fallback-пути.

Сейчас `ResourceManager` умеет брать static PNG для tile ids и `Sprite.asset_key` из `assets/images/`.

Если изображения нет, используется placeholder surface с fallback-цветом из `Renderable` или tile color.

Это не sprite sheet animation, не sound loading и не asset manifest.

Сложность: простая.

---

## Asset slicing pipeline

Asset pipeline — это tooling, а не gameplay algorithm.

Сейчас есть Pillow-based инструменты:

- `tools/asset_pipeline/slice_tilesheet.py`;
- `tools/asset_pipeline/slice_spritesheet.py`;
- `tools/asset_pipeline/process_current_assets.py`;
- `tools/asset_pipeline/export_castle_preview.py`.

Они подготавливают game-ready PNG в `assets/images/` из raw source art в `assets/source/`.

`assets/source/` не должен попадать в git.

Нарезанные walk/attack frames пока не используются runtime-анимацией.

Это не `AnimationManager`, не asset manifest, не sound pipeline и не редактор assets.

Сложность: простая.

---

## Проверка расстояния

Используется для обнаружения игрока, атаки и захвата точек.

Пример применения:
- враг замечает игрока в радиусе;
- игрок атакует врага в радиусе;
- точка захвата проверяет, находится ли игрок рядом.

Сложность: простая.

---

## Таймер перезарядки

Используется для ограничения частоты атак.

Пример применения:
- игрок не может атаковать каждый кадр;
- враг атакует с задержкой.

Сложность: простая.

---

## Progress interaction через deltaTime

Используется для коротких действий удержания, которые не должны завершаться мгновенным нажатием.

Пример применения:
- зачистка аванпоста растёт через `Outpost.clear_progress += dt`, пока игрок рядом, рядом нет живых врагов и удерживается `E`;
- сдача NPC-задачи растёт через `NPC.report_progress += dt`, пока игрок рядом, требуемый аванпост зачищен и удерживается `E`;
- если условие нарушается, progress сбрасывается в `0`;
- после достижения duration выставляется финальный state-флаг `Outpost.cleared` или `NPC.quest_completed`.

Это не новый сложный алгоритм, а простая gameplay feedback/state progression поверх обычного game loop.

Сложность: простая.

---

## AABB hitbox ближней атаки

Используется для читаемой атаки игрока.

Пример применения:
- игрок смотрит вправо и hitbox строится справа от игрока;
- враги внутри прямоугольника получают урон;
- враги вне прямоугольника не получают урон;
- active hitbox кратко рисуется через `RenderSystem`.

Hitbox строится по `FacingDirection` и проверяется через AABB intersection.

При попадании применяется небольшой knockback.

Если в `MeleeAttackSystem` передан `tile_map`, knockback не двигает врага в стену.

Это не sprite animation, не combo-system и не equipment system.

Сложность: простая.

---

## AABB telegraph атаки врага

Используется для читаемой атаки обычного врага.

Пример применения:
- враг рядом с игроком запускает короткий windup через `EnemyAttackState`;
- `EnemyAttackSystem` строит AABB hitbox в доминирующем направлении к игроку;
- hitbox фиксируется в момент начала windup и не следует за игроком;
- до конца windup урон не наносится;
- после windup система проверяет AABB intersection между игроком и сохранённым hitbox;
- если игрок остался внутри прямоугольника, он получает урон;
- если игрок вышел из прямоугольника, атака промахивается;
- active enemy hitbox кратко рисуется через `RenderSystem`.

Это простая deltaTime-логика с таймером подготовки и AABB-проверкой.

Это не Behavior Tree, не sprite animation, не sound feedback, не particles и не сложная combat state machine.

Сложность: простая.

---

## Camera offset + clamp

Используется в `RegionScene`, где карта больше viewport.

Пример применения:
- camera следует за игроком;
- camera не выходит за края карты;
- `TileMap.draw()` и `RenderSystem.draw()` получают optional camera;
- HUD остаётся в screen coordinates.

Если карта меньше viewport, camera остаётся в `(0, 0)`.

Это не smoothing, не zoom и не minimap.

Сложность: простая.

---

# Средние алгоритмы

## Конечный автомат состояний врага

Используется для управления поведением врага.

Возможные состояния:
- `idle`;
- `patrol`;
- `chase`;
- `attack`;
- `dead`.

Пример логики:
- если игрок далеко — `state = idle` или `state = patrol`;
- если игрок в радиусе обнаружения — `state = chase`;
- если игрок в радиусе атаки — `state = attack`;
- если здоровье меньше или равно нулю — `state = dead`.

Сложность: средняя.

---

## Система захвата точки

Используется для изменения контроля над территорией.

Пример логики:
- если игрок рядом и врагов рядом нет — `capture_progress` увеличивается;
- если враги рядом — `capture_progress` не растет или уменьшается;
- если `capture_progress` достиг максимума — точка становится собственностью игрока.

Сложность: средняя.

---

## Базовая система влияния

Используется для отображения контроля над регионом.

Пример логики:
- убийство врага немного повышает `player_influence` и снижает `enemy_influence`;
- зачистка outpost даёт крупный, но не решающий сдвиг влияния;
- завершение NPC quest даёт крупный, но не решающий сдвиг влияния;
- assault unlock открывается, когда `enemy_influence` достаточно низкое.

Текущий баланс специально не открывает штурм от одного outpost.

Один outpost + один NPC quest без боевого вклада тоже не открывают штурм.

Два outposts + два NPC quests без боевого вклада тоже не открывают штурм.

Ожидаемый минимальный путь к unlock сейчас: два outposts, два NPC quests и combat contribution.

Сложность: средняя.

---

## SpatialIndex interface + UniformGrid

Используется для поиска nearby candidates без полного перебора всех врагов.

Сейчас есть:
- `src/algorithms/spatial_index.py` — минимальный interface;
- `src/algorithms/uniform_grid.py` — первый backend на равномерной сетке.

`SpatialIndex` отдаёт только `entity_id`.

Он не импортирует PyGame, ECS, компоненты или сцены.

`UniformGrid` работает в pixel coordinates:
- `clear()` очищает все ячейки и словарь объектов;
- `insert(entity_id, x, y, width, height)` кладёт AABB объекта во все пересекаемые grid cells;
- `query_rect(x, y, width, height)` возвращает set кандидатов из пересекаемых cells;
- `query_radius(x, y, radius)` сначала берёт кандидатов из bounding rect, затем фильтрует их по расстоянию от центра query до центра AABB объекта.

Runtime AABB хранится внутри `UniformGrid.objects`, чтобы `query_radius()` мог отфильтровать кандидатов без обращения к ECS.

`query_radius()` является center-based query: он фильтрует по центру AABB объекта.

`SpatialIndexSystem` строит временный enemy index из ECS:
- берёт только сущности с `Enemy`, `Position`, `Collider`;
- пропускает `Dead`;
- вставляет AABB врага в `UniformGrid`.

Сейчас enemy spatial index используется как optional candidate source в:
- `MeleeAttackSystem` для кандидатов попадания hitbox;
- `EnemyAttackSystem` для кандидатов атаки по игроку;
- `OutpostSystem` для nearby enemy check;
- `CaptureSystem` для nearby enemy check.

`OutpostSystem` и `CaptureSystem` не используют center-filtered `query_radius()` как финальный источник кандидатов. Для сохранения старой `Position`-distance semantics они используют `query_rect()` как broadphase и затем делают точную проверку расстояния внутри system.

Все эти системы сохраняют fallback без spatial index и продолжают делать точную проверку расстояния/AABB после получения candidates.

SpatialHashing, QuadTree и performance profiler ещё не реализованы.

Сложность: средняя.

---

## Волны врагов

Используется для защиты или контратаки.

Пример применения:
- после захвата точки появляются враги;
- игрок должен удержать территорию некоторое время.

Минимальная локальная castle-wave механика уже реализована в `CastleAssaultScene`.

Она создаёт обычных врагов после захвата не финальной точки.

Это не глобальная система контратак и не спавнер разных типов врагов.

Сложность: средняя.

---

# Сложные алгоритмы

## A* для поиска пути

Используется для движения врагов по карте с препятствиями.

Пример применения:
- враг ищет путь к игроку;
- враг обходит стены;
- отряды движутся к точке захвата.

Сейчас реализован модуль `src/algorithms/pathfinding.py`.

Алгоритм работает по tile coordinates, использует 4 направления и Manhattan distance.

Сейчас A* применяется в `RegionScene` и `CastleAssaultScene` для преследования игрока врагами через `EnemyChaseSystem`.

`EnemyChaseSystem` не пересчитывает путь каждый кадр: используется простой path cache и rebuild interval.

Перед A* проверяется line of sight по тайлам.

Tile selection для врага и игрока берёт центр collider, а не top-left координату entity.

Target position для движения по pathfinding центрируется внутри tile с учётом collider врага.

Если last seen target стал недоступен, враг очищает last seen memory и переходит к patrol fallback или останавливается.

Fallback `EnemyChaseSystem.update(ecm)` без `tile_map` всё ещё сохраняет простое прямое преследование для тестов и совместимости.

A* не отвечает за поведение, приоритеты или состояния врага.

LOS и last seen / hysteresis реализованы отдельно: алгоритм обзора находится в `src/algorithms/line_of_sight.py`, а простая память последнего видимого тайла хранится внутри `EnemyChaseSystem`.

Behavior Tree ещё не реализован.

Сложность: сложная.

---

## Line of Sight по тайлам

Используется для проверки, видит ли враг игрока через стены.

Сейчас реализован модуль `src/algorithms/line_of_sight.py`.

Алгоритм работает по tile coordinates и использует Bresenham-style line.

Линия включает start tile и end tile.

Если start, end или любой промежуточный tile заблокирован через `TileMap.is_tile_blocked()`, line of sight считается закрытым.

Алгоритм не зависит от PyGame, ECS, компонентов и сцен.

В `RegionScene` и `CastleAssaultScene` враги используют LOS через `EnemyChaseSystem` перед построением A* пути.

Если враг видит игрока, он обновляет last seen tile.

Если игрок пропал за стеной, враг короткое время идёт к последнему видимому tile.

Last seen / hysteresis реализованы как простая память внутри `EnemyChaseSystem`.

Last seen memory не является компонентом и не хранится в `ChaseBehavior`.

LOS не является Behavior Tree, patrol-системой, FOV-системой или lighting.

Сложность: средняя.

---

## Patrol route + LOS + last seen

Используется как простой порядок поведения врага в tile-map режиме.

Порядок:
1. Если игрок в detection radius и виден по LOS — chase target равен player tile.
2. Если игрок не виден, но есть active last seen memory — target равен last seen tile.
3. Если памяти нет и у врага есть `PatrolRoute` — враг идёт по patrol tiles.
4. Если ничего из этого нет — враг останавливается.

`PatrolRoute` хранит только данные маршрута.

Логика выбора цели остаётся в `EnemyChaseSystem`.

Маршрут из менее чем двух tile не считается валидным для движения: враг останавливается, а path cache для него очищается.

Если path к текущему patrol target недоступен, система пробует следующий patrol target и останавливается, если весь маршрут недоступен.

Это не Behavior Tree, не FSM-компонент и не guard AI.

Сложность: средняя.

---

## Распространение влияния по графу регионов

Используется для живой карты войны.

Идея:
- мир состоит из регионов;
- регионы соединены дорогами;
- влияние игрока и врага распространяется между соседними регионами;
- захваченные узлы усиливают сторону владельца;
- отрезанное снабжение ослабляет врага.

Сложность: сложная.

На первом этапе не реализуется полностью.  
Сначала достаточно одной территории и одного значения влияния.

---

## Система снабжения

Используется для ослабления или усиления регионов.

Идея:
- у врага есть узлы снабжения;
- если игрок захватывает ключевой узел, враг в регионе слабеет;
- если регион отрезан от снабжения, в нем меньше врагов или ниже их сила.

Сложность: сложная.

---

## Выбор направления атаки врага

Используется для контратак.

Идея:
- враг анализирует карту;
- выбирает слабую соседнюю территорию;
- отправляет туда волну атаки.

Сложность: сложная.

---

## Процедурная генерация региона

Используется для создания карт или наполнения регионов.

Возможные варианты:
- случайная расстановка препятствий;
- генерация комнат и коридоров;
- генерация дорог между ключевыми точками;
- размещение врагов, ресурсов и объектов.

Сложность: сложная.

Для первого прототипа лучше использовать ручную тестовую карту.  
Процедурную генерацию можно добавить позже как отдельный слой.

---

## BSP dungeon generation

Используется для процедурной структуры замка.

Сейчас реализованы:
- `src/algorithms/bsp.py`;
- `src/world/castle_generator.py`.

BSP делит прямоугольник карты на leaves.

В leaf nodes создаются rooms.

Rooms соединяются L-shaped corridors.

Коридоры вырезаются шире одного tile, чтобы текущие player/enemy collider sizes не превращали procedural castle в болезненный однотайловый лабиринт.

`CastleGenerator` создаёт data-only layout: matrix, rooms, corridors, entrance tile, final room tile, capture point tiles, enemy spawn tiles и wave spawn tiles.

`final_room_tile` участвует в gameplay как последняя capture point.

Комнаты и коридоры замка используют отдельные visual tile ids: `CASTLE_FLOOR`, `CASTLE_WALL`, `CRACKED_STONE_FLOOR` и `DARK_CORRIDOR_FLOOR`.

`CastleLayout.fingerprint()` даёт короткий диагностический hash layout-матрицы и важных координат.

Enemy spawn tiles выбираются рядом с capture points как guard-позиции до появления Behavior Tree.

Wave spawn tiles выбираются около не-финальных capture points или на подходах к ним.

Layout валидируется через существующий Flood fill / BFS из `src/algorithms/flood_fill.py`.

Алгоритм работает в tile coordinates и не создаёт PyGame objects, ECS entities или scene objects.

Это сложный алгоритм.

BSP generator core подключён к `CastleAssaultScene`.

Layout всё ещё data-only: gameplay scene создаёт ECS entities по tile coordinates из `CastleLayout`.

BFS validation используется и в generator, и на уровне сцены.

Текущий scope — procedural layout для штурма.

Для визуальной диагностики layout можно экспортировать в PNG через `tools/asset_pipeline/export_castle_preview.py`.

Это не decorations, doors, traps, locked rooms, lighting, room themes или boss/final room gameplay.

---

# Минимальный набор алгоритмов для первого прототипа

Для самого первого ядра были нужны:

- движение по вектору;
- проверка столкновений;
- Flood fill / BFS validation для процедурного замка;
- проверка расстояния;
- таймеры перезарядки;
- простое поведение врага;
- система захвата точки;
- простая система влияния;
- A* + LOS для врагов;
- `UniformGrid` для nearby enemy candidate search;
- BSP generator core и интеграция procedural layout в `CastleAssaultScene`.

Текущий vertical prototype уже использует этот набор как рабочую основу. Дальше алгоритмы стоит добавлять от milestone-задач, а не просто ради увеличения списка систем.

---

# Алгоритмы, которые стоит отложить

На раннем этапе не нужно реализовывать:

- более сложную оптимизацию pathfinding при необходимости;
- Behavior Tree;
- SpatialHashing;
- QuadTree;
- полноценную симуляцию фронта;
- doors/traps/decorations/lighting для процедурного замка;
- умный выбор атак врага;
- систему снабжения;
- сложный ИИ отрядов.
- sprite sheet animation;
- полноценный production art pass и asset manifest.

Эти алгоритмы стоит добавлять только после появления рабочего игрового ядра.
