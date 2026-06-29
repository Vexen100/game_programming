import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from PIL import Image

from tools.asset_pipeline.grid_slicing import get_grid_boxes
from tools.asset_pipeline.process_surface_tileset import create_preview
from tools.asset_pipeline.slice_tilesheet import slice_tilesheet
from tools.asset_pipeline.sprite_normalization import (
    clean_sprite_artifacts,
    clean_transparent_rgb,
    get_alpha_bbox,
    get_visible_size,
    is_green_dominant_artifact_pixel,
    normalize_sprite_frame,
    remove_chroma_pixels,
)
from tools.asset_pipeline.validate_entity_animation_frames import (
    validate_entity_animation_frames,
)
from tools.asset_pipeline.validate_surface_tiles import validate_surface_tiles


class TestAssetPipeline(unittest.TestCase):
    """Проверяет узкий pipeline нарезки surface tiles."""

    def create_synthetic_tileset(self, image_path):
        """Создает synthetic 1254x1254 tileset с margin/gutter.

        Args:
            image_path: Путь, куда нужно сохранить synthetic source PNG.

        Returns:
            Список цветов, которыми заполнены 16 ячеек.
        """
        image = Image.new("RGBA", (1254, 1254), (0, 0, 0, 255))
        colors = []
        boxes = get_grid_boxes(
            image.size,
            cols=4,
            rows=4,
            margin_x=3,
            margin_y=3,
            gutter_x=5,
            gutter_y=5,
            grid_mode="proportional",
        )

        for index, box in enumerate(boxes):
            color = ((index * 37) % 255, (index * 67) % 255, (index * 97) % 255, 255)
            colors.append(color)
            tile = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), color)
            image.paste(tile, box)

        image.save(image_path)
        return colors

    def create_alpha_sprite(self, size, bbox, color=(200, 80, 40, 255)):
        """Создает transparent image с заполненной alpha bbox.

        Args:
            size: Размер canvas.
            bbox: Видимая область `(left, top, right, bottom)`.
            color: Цвет видимых пикселей.

        Returns:
            PIL RGBA image.
        """
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        patch = Image.new("RGBA", (bbox[2] - bbox[0], bbox[3] - bbox[1]), color)
        image.alpha_composite(patch, (bbox[0], bbox[1]))
        return image

    def save_alpha_sprite(self, path, bbox, size=(32, 32)):
        """Сохраняет transparent PNG с заданной alpha bbox.

        Args:
            path: Путь записи PNG.
            bbox: Видимая область `(left, top, right, bottom)`.
            size: Размер canvas.

        Returns:
            None.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        self.create_alpha_sprite(size, bbox).save(path)

    def test_proportional_4x4_slicing_handles_1254_image(self):
        """Проверяет proportional slicing для non-divisible 1254x1254 source.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.png"
            output_root = Path(tmp) / "images"
            self.create_synthetic_tileset(source_path)
            names = [f"tile_{index}" for index in range(16)]

            with redirect_stdout(StringIO()):
                output_paths = slice_tilesheet(
                    input_path=source_path,
                    output_root=output_root,
                    cols=4,
                    rows=4,
                    names=names,
                    folders=["tiles"] * 16,
                    output_tile_size=32,
                    margin_x=3,
                    margin_y=3,
                    gutter_x=5,
                    gutter_y=5,
                    grid_mode="proportional",
                    background_mode="none",
                    resample="box",
                )

            self.assertEqual(len(output_paths), 16)
            for output_path in output_paths:
                with Image.open(output_path) as image:
                    self.assertEqual(image.size, (32, 32))
                    self.assertEqual(image.mode, "RGBA")

    def test_slice_tilesheet_rejects_wrong_names_count(self):
        """Проверяет понятную ошибку при неверном числе names.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "source.png"
            Image.new("RGBA", (64, 64), (10, 20, 30, 255)).save(source_path)

            with self.assertRaisesRegex(ValueError, "Expected 16 names"):
                slice_tilesheet(
                    input_path=source_path,
                    output_root=Path(tmp) / "images",
                    cols=4,
                    rows=4,
                    names=["too_few"],
                    folders=["tiles"] * 16,
                    grid_mode="proportional",
                )

    def test_validator_catches_missing_asset(self):
        """Проверяет ошибку validator для отсутствующего PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "Missing surface tile PNG"):
                validate_surface_tiles(tmp, expected_paths=("tiles/missing.png",))

    def test_validator_catches_wrong_size_asset(self):
        """Проверяет ошибку validator для PNG неверного размера.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "tiles" / "bad.png"
            image_path.parent.mkdir(parents=True)
            Image.new("RGBA", (16, 16), (10, 20, 30, 255)).save(image_path)

            with self.assertRaisesRegex(ValueError, "32x32"):
                validate_surface_tiles(tmp, expected_paths=("tiles/bad.png",))

    def test_preview_uses_final_32x32_tiles(self):
        """Проверяет создание preview из финальных 32x32 tile PNG.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tile_paths = []
            for index in range(16):
                tile_path = Path(tmp) / f"tile_{index}.png"
                Image.new("RGBA", (32, 32), (index, 20, 30, 255)).save(tile_path)
                tile_paths.append(tile_path)

            preview_path = create_preview(tile_paths, Path(tmp) / "preview.png")

            with Image.open(preview_path) as preview:
                self.assertEqual(preview.size, (128, 128))
                self.assertEqual(preview.mode, "RGBA")

    def test_normalize_sprite_frame_keeps_32x32_canvas(self):
        """Проверяет, что normalization сохраняет 32x32 canvas.

        Returns:
            None.
        """
        image = self.create_alpha_sprite((48, 48), (20, 20, 28, 28))

        normalized = normalize_sprite_frame(image, output_size=(32, 32))

        self.assertEqual(normalized.size, (32, 32))
        self.assertEqual(normalized.mode, "RGBA")

    def test_normalize_sprite_frame_scales_small_visible_bbox_to_target_height(self):
        """Проверяет scale маленького bbox до target height.

        Returns:
            None.
        """
        image = self.create_alpha_sprite((48, 48), (20, 20, 28, 28))

        normalized = normalize_sprite_frame(
            image,
            output_size=(32, 32),
            target_visible_height=24,
        )

        self.assertEqual(get_visible_size(normalized)[1], 24)

    def test_normalize_sprite_frame_bottom_centers_to_baseline(self):
        """Проверяет bottom-center alignment по baseline.

        Returns:
            None.
        """
        image = self.create_alpha_sprite((48, 48), (20, 20, 28, 28))

        normalized = normalize_sprite_frame(
            image,
            output_size=(32, 32),
            target_visible_height=16,
            target_visible_width=16,
            baseline_y=29,
        )
        bbox = get_alpha_bbox(normalized)

        self.assertEqual(bbox[3] - 1, 29)
        self.assertEqual((bbox[0] + bbox[2]) // 2, 16)

    def test_clean_transparent_rgb_zeroes_hidden_rgb(self):
        """Проверяет очистку RGB у fully transparent pixels.

        Returns:
            None.
        """
        image = Image.new("RGBA", (1, 1), (255, 0, 255, 0))

        cleaned = clean_transparent_rgb(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))

    def test_remove_chroma_pixels_makes_green_transparent(self):
        """Проверяет удаление chroma-green пикселя.

        Returns:
            None.
        """
        image = Image.new("RGBA", (1, 1), (12, 204, 8, 255))

        cleaned = remove_chroma_pixels(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))

    def test_clean_sprite_artifacts_preserves_visible_non_chroma_sprite_pixel(self):
        """Проверяет, что обычный видимый цвет спрайта сохраняется.

        Returns:
            None.
        """
        image = Image.new("RGBA", (1, 1), (160, 80, 64, 255))

        cleaned = clean_sprite_artifacts(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (160, 80, 64, 255))

    def test_clean_sprite_artifacts_removes_low_alpha_colored_noise(self):
        """Проверяет удаление low-alpha colored noise.

        Returns:
            None.
        """
        image = Image.new("RGBA", (1, 1), (255, 0, 255, 8))

        cleaned = clean_sprite_artifacts(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))

    def test_is_green_dominant_artifact_detects_dark_chroma_remnant(self):
        """Проверяет detection тёмных green-dominant remnants.

        Returns:
            None.
        """
        artifact_colors = [
            (10, 120, 0, 255),
            (23, 100, 14, 255),
            (12, 113, 3, 255),
        ]

        for color in artifact_colors:
            with self.subTest(color=color):
                self.assertTrue(is_green_dominant_artifact_pixel(*color))

    def test_clean_sprite_artifacts_removes_dark_green_opaque_noise(self):
        """Проверяет удаление opaque dark-green chroma remnant.

        Returns:
            None.
        """
        image = Image.new("RGBA", (1, 1), (10, 120, 0, 255))

        cleaned = clean_sprite_artifacts(image)

        self.assertEqual(cleaned.getpixel((0, 0)), (0, 0, 0, 0))

    def test_green_dominant_cleanup_preserves_blue_red_gold_gray_pixels(self):
        """Проверяет, что cleanup не удаляет обычные цвета спрайта.

        Returns:
            None.
        """
        safe_colors = [
            (45, 80, 170, 255),
            (130, 55, 35, 255),
            (135, 135, 135, 255),
            (210, 170, 45, 255),
            (12, 12, 12, 255),
        ]
        image = Image.new("RGBA", (len(safe_colors), 1), (0, 0, 0, 0))
        for x, color in enumerate(safe_colors):
            image.putpixel((x, 0), color)

        cleaned = clean_sprite_artifacts(image)

        for x, color in enumerate(safe_colors):
            with self.subTest(color=color):
                self.assertEqual(cleaned.getpixel((x, 0)), color)

    def test_validate_entity_animation_frames_allows_missing_enemy_attack_frames(self):
        """Проверяет, что validator не требует enemy attack frames.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "enemy.png",
                (5, 2, 26, 30),
            )
            self.save_alpha_sprite(
                image_root / "entities" / "enemy" / "walk_down_0.png",
                (5, 2, 26, 30),
            )

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertTrue(result.passed)

    def test_validate_entity_animation_frames_fails_tiny_walk_frame(self):
        """Проверяет fail validator для слишком маленького walk frame.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "enemy.png",
                (5, 2, 26, 30),
            )
            self.save_alpha_sprite(
                image_root / "entities" / "enemy" / "walk_down_0.png",
                (14, 14, 18, 18),
            )

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("visible height ratio" in error for error in result.errors)
            )

    def test_validator_fails_green_dominant_opaque_artifact(self):
        """Проверяет fail validator для dark green opaque artifact.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "player.png",
                (4, 2, 28, 30),
            )
            frame_path = image_root / "entities" / "player" / "walk_down_0.png"
            self.save_alpha_sprite(frame_path, (4, 2, 28, 30))

            with Image.open(frame_path) as frame:
                frame = frame.convert("RGBA")
                frame.putpixel((10, 10), (10, 120, 0, 255))
                frame.save(frame_path)

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("green-dominant artifact pixels" in error for error in result.errors)
            )

    def test_validator_passes_after_green_dominant_cleanup(self):
        """Проверяет pass validator после cleanup green-dominant artifact.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "player.png",
                (4, 2, 28, 30),
            )
            frame_path = image_root / "entities" / "player" / "walk_down_0.png"
            self.save_alpha_sprite(frame_path, (4, 2, 28, 30))

            with Image.open(frame_path) as frame:
                frame = frame.convert("RGBA")
                frame.putpixel((10, 10), (10, 120, 0, 255))
                clean_sprite_artifacts(frame).save(frame_path)

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertTrue(result.passed)

    def test_validator_fails_visible_chroma_artifact(self):
        """Проверяет fail validator для видимого chroma-green artifact.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "player.png",
                (4, 2, 28, 30),
            )
            frame_path = image_root / "entities" / "player" / "walk_down_0.png"
            self.save_alpha_sprite(frame_path, (4, 2, 28, 30))

            with Image.open(frame_path) as frame:
                frame = frame.convert("RGBA")
                frame.putpixel((10, 10), (12, 204, 8, 255))
                frame.save(frame_path)

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertFalse(result.passed)
            self.assertTrue(
                any("visible chroma pixels" in error for error in result.errors)
            )

    def test_validator_fails_transparent_nonzero_rgb(self):
        """Проверяет fail validator для transparent pixel с ненулевым RGB.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as tmp:
            image_root = Path(tmp)
            self.save_alpha_sprite(
                image_root / "entities" / "player.png",
                (4, 2, 28, 30),
            )
            frame_path = image_root / "entities" / "player" / "walk_down_0.png"
            self.save_alpha_sprite(frame_path, (4, 2, 28, 30))

            with Image.open(frame_path) as frame:
                frame = frame.convert("RGBA")
                frame.putpixel((0, 0), (255, 0, 255, 0))
                frame.save(frame_path)

            result = validate_entity_animation_frames(image_root=image_root)

            self.assertFalse(result.passed)
            self.assertTrue(
                any(
                    "transparent pixels with non-zero RGB" in error
                    for error in result.errors
                )
            )
