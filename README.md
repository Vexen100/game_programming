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
- region scene;
- influence;
- outpost/NPC interactions;
- castle assault;
- procedural BSP castle layout in `CastleAssaultScene`;
- capture points;
- liberation flow;
- single-slot save/continue MVP;
- A*, LOS, BFS validation, UniformGrid.

Ещё не реализовано:
- multi-slot save/load UI;
- settings menu;
- Behavior Tree;
- SpatialHashing;
- full castle runtime save;
- doors/traps/room decorations;
- Lightmap / Perlin;
- sprites/animations/sound.

## 📝 Примечание
Репозиторий настроен для итеративной работы. Архитектура, стек и игровые решения будут уточняться в процессе. Ключевые шаги и прогресс фиксируются в истории коммитов и документации.
