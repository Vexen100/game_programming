# Asset pipeline

## Назначение

Этот документ описывает текущий минимальный pipeline для пользовательских 32x32 PNG assets.

Pipeline нужен только для подготовки game-ready PNG в `assets/images/`.

Raw source art хранится отдельно в `assets/source/` и не должен попадать в git.

---

## Текущее состояние

Сейчас подключены:

- нарезка tile sheet через `tools/asset_pipeline/slice_tilesheet.py`;
- нарезка sprite sheet через `tools/asset_pipeline/slice_spritesheet.py`;
- общий helper для текущего набора raw-файлов через `tools/asset_pipeline/process_current_assets.py`;
- diagnostic export procedural castle preview через `tools/asset_pipeline/export_castle_preview.py`;
- загрузка static PNG tiles/entities через `ResourceManager`;
- fallback-placeholder, если ожидаемый PNG отсутствует.

Runtime animation пока не реализована.

Нарезанные walk/attack frames уже лежат в `assets/images/entities/player/` и `assets/images/entities/enemy/`, но сейчас они являются подготовленными asset-файлами на будущее, а не active animation runtime.

---

## Raw source paths

Текущий helper ищет файлы:

- `assets/source/tilesets/crown_reclaim_tileset_raw.png`;
- `assets/source/spritesheets/crown_reclaim_entity_icons_raw.png`;
- `assets/source/spritesheets/player_knight_walk_raw.png`;
- `assets/source/spritesheets/player_knight_attack_raw.png`;
- `assets/source/spritesheets/enemy_soldier_walk_raw.png`.

`assets/source/` добавлен в `.gitignore`, потому что это raw/user-provided source art.

---

## Команды

Нарезать текущие raw-файлы:

```bash
.venv/bin/python tools/asset_pipeline/process_current_assets.py
```

Экспортировать diagnostic preview замка:

```bash
.venv/bin/python tools/asset_pipeline/export_castle_preview.py --seed 41042 --output assets/tmp/castle_preview_41042.png
```

`assets/tmp/` тоже игнорируется git и подходит для локальных preview-файлов.

---

## Game-ready output

Основные runtime mappings сейчас:

- ordinary tiles: `assets/images/tiles/*.png`;
- castle tiles: `assets/images/castle/*.png`;
- entity icons: `assets/images/entities/player.png`, `enemy.png`, `outpost_enemy.png`, `npc_active.png`, `capture_point_enemy.png`.

`ResourceManager` знает default mapping для текущих tile ids и `Sprite.asset_key`.

Если PNG отсутствует, `ResourceManager` возвращает generated placeholder с fallback-цветом тайла или `Renderable`.

---

## Что не реализовано

Пока не добавлялись:

- `AnimationManager`;
- runtime sprite animation;
- asset manifest;
- sound loading;
- particle effects;
- автоматическая миграция старых assets;
- редактор или UI для assets.

Этот шаг добавляет только подготовку PNG и их безопасное подключение к текущему rendering path.
