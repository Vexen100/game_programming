# Images

This directory contains the game-ready PNG images used by `ResourceManager`.

Current asset groups:

- `tiles/` - ordinary region tile images;
- `castle/` - castle-specific tile images;
- `entities/` - current static entity icons and sliced animation frames.

Surface tileset v2:

- raw source goes to `assets/source/tilesets/crown_reclaim_surface_tileset_raw.png`;
- final game tiles are exact `32x32` RGBA PNG files;
- ordinary final tiles live in `assets/images/tiles/`;
- castle final tiles live in `assets/images/castle/`;
- local preview is written to `assets/tmp/previews/surface_tiles_preview.png`;
- `assets/source/` and `assets/tmp/` are ignored by git.

Surface tiles are sliced as full cells and resized to `32x32`.
They are not trimmed, chroma-keyed, or background-removed.
The surface tileset uses `background-mode none`.

The current runtime uses static PNG surfaces through `Sprite.asset_key` and
`Renderable` sizes. Sliced walk/attack frames are stored here for later use,
but runtime sprite animation is not implemented yet.

Character spritesheets, runtime animations, and `AnimationManager` are not part
of the surface tileset replacement step.

If an expected PNG is missing, `ResourceManager` still creates a generated
placeholder surface, so gameplay does not depend on perfect asset coverage.

Raw user-provided source art belongs in `assets/source/`, which is ignored by
git. Do not store user saves, settings files, raw PSD/Aseprite files, or other
runtime data in this directory.
