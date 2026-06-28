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
- отдельный helper для user-provided 4x4 surface tileset через `tools/asset_pipeline/process_surface_tileset.py`;
- validator финальных surface tiles через `tools/asset_pipeline/validate_surface_tiles.py`;
- diagnostic export procedural castle preview через `tools/asset_pipeline/export_castle_preview.py`;
- загрузка static PNG tiles/entities через `ResourceManager`;
- runtime idle/walk frames для player/enemy через `AnimationSystem` и `ResourceManager`;
- fallback-placeholder, если ожидаемый PNG отсутствует.

Runtime animation пока не реализована.

Нарезанные walk frames из `assets/images/entities/player/` и `assets/images/entities/enemy/` используются минимальной runtime idle/walk animation.

Нарезанные player attack frames используются visual-only attack animation runtime.

Enemy attack frames могут отсутствовать; при их отсутствии runtime откатывается к static enemy sprite.

---

## Raw source paths

Текущий helper ищет файлы:

- `assets/source/tilesets/crown_reclaim_surface_tileset_raw.png`;
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

Нарезать только user-provided surface tileset v2:

```bash
.venv/bin/python tools/asset_pipeline/process_surface_tileset.py
```

Для текущего 4x4 surface tileset используется proportional grid с явным пропуском черной рамки и separator lines:

```text
margin_x=3
margin_y=3
gutter_x=5
gutter_y=5
background_mode=none
output_tile_size=32
resample=box
```

Surface tiles режутся full-cell способом: ячейка crop-ается целиком и resize-ится в `32x32`.
Обрезка содержимого, chroma-key и удаление фона для этого tileset не применяются.

Проверить финальные surface tiles:

```bash
.venv/bin/python tools/asset_pipeline/validate_surface_tiles.py
```

Экспортировать diagnostic preview замка:

```bash
.venv/bin/python tools/asset_pipeline/export_castle_preview.py --seed 41042 --output assets/tmp/castle_preview_41042.png
```

`assets/tmp/` тоже игнорируется git и подходит для локальных preview-файлов.
Surface tiles preview создается в `assets/tmp/previews/surface_tiles_preview.png`.

---

## Game-ready output

Основные runtime mappings сейчас:

- ordinary tiles: `assets/images/tiles/*.png`;
- castle tiles: `assets/images/castle/*.png`;
- entity icons: `assets/images/entities/player.png`, `enemy.png`, `outpost_enemy.png`, `npc_active.png`, `capture_point_enemy.png`.

Surface tileset v2 создает финальные `32x32` PNG:

- `assets/images/tiles/grass.png`;
- `assets/images/tiles/dirt.png`;
- `assets/images/tiles/road.png`;
- `assets/images/tiles/ruins_floor.png`;
- `assets/images/tiles/forest.png`;
- `assets/images/tiles/water.png`;
- `assets/images/tiles/bridge.png`;
- `assets/images/tiles/wall.png`;
- `assets/images/castle/castle_floor.png`;
- `assets/images/castle/castle_wall.png`;
- `assets/images/castle/cracked_stone_floor.png`;
- `assets/images/castle/dark_corridor_floor.png`;
- `assets/images/tiles/outpost_marker.png`;
- `assets/images/tiles/npc_camp_marker.png`;
- `assets/images/tiles/capture_point_marker.png`;
- `assets/images/tiles/missing_tile.png`.

`ResourceManager` знает default mapping для текущих tile ids и `Sprite.asset_key`.

Static entity PNG подключаются через `Sprite.asset_key` и `ResourceManager.get_entity_surface(...)`.

Текущие entity keys:

- `player`;
- `enemy`;
- `outpost_enemy`;
- `npc_active`;
- `capture_point_enemy`.

Если PNG отсутствует, `ResourceManager` возвращает generated placeholder с fallback-цветом тайла или `Renderable`.

World entities отрисовываются через `RenderSystem` с Y-sort по visual baseline.

Player/enemy idle/walk animation frames ищутся по пути `assets/images/entities/{player|enemy}/walk_*_*.png`.

Visual-only attack animation frames ищутся по пути `assets/images/entities/{player|enemy}/attack_*_*.png`.

Если animation frame отсутствует, `RenderSystem` откатывается к static `Sprite`, а затем к rectangle fallback.

---

## Что не реализовано

Пока не добавлялись:

- `AnimationManager`;
- animation events;
- frame events;
- hitbox timing sync;
- combo system;
- asset manifest;
- sound loading;
- particle effects;
- автоматическая миграция старых assets;
- редактор или UI для assets.

Surface tileset v2 сам по себе не добавляет character spritesheets, `AnimationManager` или новые runtime visual systems.
Текущий runtime использует минимальную idle/walk animation и visual-only attack animation, без `AnimationManager`, animation events и hitbox timing sync.
