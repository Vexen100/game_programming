# Images

This directory contains the game-ready PNG images used by `ResourceManager`.

Current asset groups:

- `tiles/` - ordinary region tile images;
- `castle/` - castle-specific tile images;
- `entities/` - current static entity icons and sliced animation frames.

The current runtime uses static PNG surfaces through `Sprite.asset_key` and
`Renderable` sizes. Sliced walk/attack frames are stored here for later use,
but runtime sprite animation is not implemented yet.

If an expected PNG is missing, `ResourceManager` still creates a generated
placeholder surface, so gameplay does not depend on perfect asset coverage.

Raw user-provided source art belongs in `assets/source/`, which is ignored by
git. Do not store user saves, settings files, raw PSD/Aseprite files, or other
runtime data in this directory.
