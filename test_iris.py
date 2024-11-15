import pytest
from pathlib import Path
import shutil
import tempfile
from PIL import Image
import os

from iris import (
    WatermarkOptions,
    ShadowOptions,
    add_watermark,
    process_images
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_image(temp_dir):
    """Create a sample test image."""
    image_path = Path(temp_dir) / "test.png"
    img = Image.new('RGBA', (400, 300), (255, 255, 255, 255))
    img.save(image_path)
    return str(image_path)

@pytest.fixture
def default_options():
    """Create default watermark options."""
    return WatermarkOptions(
        text="Test Watermark",
        font_size=30,
        opacity=0.5,
        padding=20,
        shadow={
            'offset_x': 3,
            'offset_y': 3,
            'blur': 3,
            'opacity': 0.7
        }
    )

class TestWatermarkOptions:
    def test_default_values(self):
        options = WatermarkOptions()
        assert options.text == '版权所有'
        assert options.font_size == 40
        assert options.opacity == 0.5
        assert options.padding == 20
        assert isinstance(options.shadow, ShadowOptions)

    def test_custom_values(self):
        options = WatermarkOptions(
            text="Custom",
            font_size=50,
            opacity=0.7,
            padding=30,
            shadow={'offset_x': 5}
        )
        assert options.text == "Custom"
        assert options.font_size == 50
        assert options.opacity == 0.7
        assert options.padding == 30
        assert options.shadow.offset_x == 5
        assert options.shadow.offset_y == 3  # Default value

class TestShadowOptions:
    def test_default_values(self):
        shadow = ShadowOptions()
        assert shadow.offset_x == 3
        assert shadow.offset_y == 3
        assert shadow.blur == 3
        assert shadow.opacity == 0.7
        assert shadow.offset == (3, 3)

    def test_custom_values(self):
        shadow = ShadowOptions(offset_x=5, offset_y=5, blur=4, opacity=0.8)
        assert shadow.offset_x == 5
        assert shadow.offset_y == 5
        assert shadow.blur == 4
        assert shadow.opacity == 0.8
        assert shadow.offset == (5, 5)

class TestWatermarkFunctions:
    def test_add_watermark(self, sample_image, temp_dir, default_options):
        output_path = str(Path(temp_dir) / "output.png")

        # Test watermark addition
        add_watermark(sample_image, output_path, default_options)

        # Verify output file exists
        assert os.path.exists(output_path)

        # Verify output is a valid image
        with Image.open(output_path) as img:
            assert img.mode == 'RGBA'
            assert img.size == (400, 300)

    def test_process_images(self, temp_dir, default_options):
        # Create test directory structure
        input_dir = Path(temp_dir) / "input"
        output_dir = Path(temp_dir) / "output"
        subfolder = input_dir / "subfolder"
        os.makedirs(subfolder)

        # Create test images
        test_images = [
            input_dir / "test1.png",
            input_dir / "test2.png",
            subfolder / "test3.png"
        ]

        for img_path in test_images:
            img = Image.new('RGBA', (400, 300), (255, 255, 255, 255))
            img.save(img_path)

        # Process images
        process_images(str(input_dir), str(output_dir), default_options)

        # Verify output structure and files
        assert os.path.exists(output_dir)
        assert os.path.exists(output_dir / "test1.png")
        assert os.path.exists(output_dir / "test2.png")
        assert os.path.exists(output_dir / "subfolder" / "test3.png")
        
        # Verify format preservation
        with Image.open(test_images[0]) as orig:
            with Image.open(output_dir / "test1.png") as out:
                assert out.format == orig.format

    def test_invalid_image(self, temp_dir, default_options):
        # Test with invalid image file
        invalid_image = Path(temp_dir) / "invalid.png"
        with open(invalid_image, 'w') as f:
            f.write("Not an image")

        output_path = str(Path(temp_dir) / "output.png")

        # Should raise an exception for invalid image
        with pytest.raises(Exception):
            add_watermark(str(invalid_image), output_path, default_options)

    def test_unicode_text(self, sample_image, temp_dir):
        # Test with Unicode text
        options = WatermarkOptions(text="测试水印")
        output_path = str(Path(temp_dir) / "unicode_output.png")

        add_watermark(sample_image, output_path, options)
        assert os.path.exists(output_path)

    def test_different_image_sizes(self, temp_dir, default_options):
        # Test with different image sizes
        sizes = [(100, 100), (800, 600), (1920, 1080)]
        
        for size in sizes:
            input_path = Path(temp_dir) / f"test_{size[0]}x{size[1]}.png"
            output_path = Path(temp_dir) / f"output_{size[0]}x{size[1]}.png"

            img = Image.new('RGBA', size, (255, 255, 255, 255))
            img.save(input_path)

            add_watermark(str(input_path), str(output_path), default_options)

            with Image.open(output_path) as result:
                assert result.size == size

    def test_downsize_large_image(self, temp_dir, default_options):
        # Test downsizing of large images
        original_size = (2000, 1500)
        max_size = 1000
        
        # Create large test image
        input_path = Path(temp_dir) / "large_test.png"
        output_path = Path(temp_dir) / "downsized_output.png"
        
        img = Image.new('RGBA', original_size, (255, 255, 255, 255))
        img.save(input_path)
        
        # Set downsizing option
        options = WatermarkOptions(
            text=default_options.text,
            downsize_to=max_size
        )
        
        add_watermark(str(input_path), str(output_path), options)
        
        with Image.open(output_path) as result:
            # Check if image was downsized properly
            assert max(result.size) <= max_size
            # Check if aspect ratio is maintained
            original_ratio = original_size[0] / original_size[1]
            new_ratio = result.size[0] / result.size[1]
            assert abs(original_ratio - new_ratio) < 0.01
