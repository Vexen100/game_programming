# 🎮 Crown Reclaim

## 📖 О проекте
2D top-down action-adventure с элементами territory control, light strategy и tower-defense

Свергнутый и преданный правитель воскресает и возвращает своё королевство, захватывая регионы и уничтожая влияние противника.


## Вероятные идеи
Tower-defense + quests + metroidvania(??)

Закос под shadow of war в 2D? Совместить мир, сражение, дефенс, открытие нового?

система сохранений. продумать штраф за смерть. продумать возможность процедурной генерации.

## 🛠️ Стек
- **Язык:** Python
- **Фреймворк / Движок:** pygame

## Текущий статус

В проекте сейчас есть играбельный прототип:
- world map;
- expanded Old Ruins `RegionScene`;
- influence;
- outpost/NPC interactions;
- multiple outposts, NPCs and enemy groups in the ordinary region;
- readable tile variety: grass, dirt, road, ruins floor, water, forest and bridge;
- minimal `ResourceManager` with generated placeholder rendering;
- sprite-ready ECS rendering via `Sprite` + `Renderable` fallback;
- castle assault;
- procedural BSP castle layout in `CastleAssaultScene`;
- widened castle corridors tuned for current player/enemy sizes;
- capture points;
- final castle room participates as the final capture point;
- liberation flow;
- single-slot save/continue MVP;
- A*, LOS, BFS validation, UniformGrid.

Assault unlock is harder than before: one outpost, one outpost + one NPC quest, and even all regional objectives without combat are not enough without additional combat contribution.

Ещё не реализовано:
- multi-slot save/load UI;
- settings menu;
- Behavior Tree;
- SpatialHashing;
- full castle runtime save;
- doors/traps/room decorations;
- Lightmap / Perlin;
- production sprites;
- sprite animations;
- sound.

## 📝 Примечание
Репозиторий настроен для итеративной работы. Архитектура, стек и игровые решения будут уточняться в процессе. Ключевые шаги и прогресс фиксируются в истории коммитов и документации.
