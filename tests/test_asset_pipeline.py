import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from PIL import Image

from tools.asset_pipeline.grid_slicing import get_grid_boxes
from tools.asset_pipeline.process_surface_tileset import create_preview
from tools.asset_pipeline.slice_tilesheet import slice_tilesheet
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
