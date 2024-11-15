from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from pathlib import Path
import argparse
from typing import Dict, Any, Tuple

class WatermarkOptions:
    def __init__(self, **kwargs):
        self.text = kwargs.get('text', '版权所有')
        self.font_path = kwargs.get('font_path')
        self.font_size = kwargs.get('font_size', 40)
        self.opacity = kwargs.get('opacity', 0.5)
        self.padding = kwargs.get('padding', 20)
        self.shadow = ShadowOptions(**kwargs.get('shadow', {}))
        self.downsize_to = kwargs.get('downsize_to', None)

class ShadowOptions:
    def __init__(self, **kwargs):
        self.offset_x = kwargs.get('offset_x', 3)
        self.offset_y = kwargs.get('offset_y', 3)
        self.blur = kwargs.get('blur', 3)
        self.opacity = kwargs.get('opacity', 0.7)

    @property
    def offset(self) -> Tuple[int, int]:
        return (self.offset_x, self.offset_y)

def add_watermark(image_path: str, output_path: str, options: WatermarkOptions) -> None:
    """Add watermark to an image with shadow effect."""
    with Image.open(image_path) as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Downsize image if needed
        if options.downsize_to:
            max_size = options.downsize_to
            if img.width > max_size or img.height > max_size:
                ratio = min(max_size / img.width, max_size / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Create layers
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shadow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))

        # Create drawing objects
        draw_watermark = ImageDraw.Draw(watermark)
        draw_shadow = ImageDraw.Draw(shadow_layer)

        # Set up font
        try:
            font = (ImageFont.truetype(options.font_path, options.font_size)
                   if options.font_path
                   else ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', options.font_size))
        except:
            font = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', options.font_size)

        # Calculate position
        bbox = draw_watermark.textbbox((0, 0), options.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = img.width - text_width - options.padding
        y = img.height - text_height - options.padding

        # Draw shadow
        shadow_color = (0, 0, 0, int(255 * options.shadow.opacity))
        draw_shadow.text(
            (x + options.shadow.offset_x, y + options.shadow.offset_y),
            options.text,
            font=font,
            fill=shadow_color
        )

        # Apply shadow blur
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(options.shadow.blur))

        # Draw main watermark
        draw_watermark.text(
            (x, y),
            options.text,
            font=font,
            fill=(255, 255, 255, int(255 * options.opacity))
        )

        # Combine layers
        result = Image.alpha_composite(img, shadow_layer)
        result = Image.alpha_composite(result, watermark)

        # Save result in original format
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        original_format = Image.open(image_path).format or 'PNG'
        result.save(output_path, original_format)

def process_images(input_folder: str, output_folder: str, options: WatermarkOptions) -> None:
    """Process all images in the input folder and its subfolders."""
    input_path = Path(input_folder)
    output_path = Path(output_folder)

    for img_path in input_path.rglob('*'):
        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            relative_path = img_path.relative_to(input_path)
            output_file = output_path / relative_path

            print(f"Processing: {img_path}")
            add_watermark(str(img_path), str(output_file), options)

def parse_args() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description='Add watermark with shadow to images')
    parser.add_argument('-i', '--input', required=True, help='Input folder containing images')
    parser.add_argument('-o', '--output', required=True, help='Output folder for watermarked images')
    parser.add_argument('-w', '--watermark', default='版权所有', help='Watermark text')
    parser.add_argument('-f', '--font', help='Path to custom font file')
    parser.add_argument('--font-size', type=int, default=40, help='Font size')
    parser.add_argument('--opacity', type=float, default=0.5, help='Watermark opacity (0-1)')
    parser.add_argument('--padding', type=int, default=20, help='Padding from edges')
    parser.add_argument('--shadow-offset-x', type=int, default=3, help='Shadow offset X')
    parser.add_argument('--shadow-offset-y', type=int, default=3, help='Shadow offset Y')
    parser.add_argument('--shadow-blur', type=int, default=3, help='Shadow blur radius')
    parser.add_argument('--shadow-opacity', type=float, default=0.7, help='Shadow opacity (0-1)')
    parser.add_argument('--downsize-to', type=int, help='Maximum size in pixels for any dimension')

    return vars(parser.parse_args())

def validate_options(args: Dict[str, Any]) -> bool:
    """Validate command line arguments."""
    if not os.path.exists(args['input']):
        print(f"Error: Input folder '{args['input']}' does not exist")
        return False

    if not 0 <= args['opacity'] <= 1 or not 0 <= args['shadow_opacity'] <= 1:
        print("Error: Opacity values must be between 0 and 1")
        return False

    if args['font'] and not os.path.exists(args['font']):
        print(f"Error: Font file '{args['font']}' does not exist")
        return False

    return True

def main():
    args = parse_args()

    if not validate_options(args):
        return

    # Create watermark options
    options = WatermarkOptions(
        text=args['watermark'],
        font_path=args['font'],
        font_size=args['font_size'],
        opacity=args['opacity'],
        padding=args['padding'],
        shadow={
            'offset_x': args['shadow_offset_x'],
            'offset_y': args['shadow_offset_y'],
            'blur': args['shadow_blur'],
            'opacity': args['shadow_opacity']
        },
        downsize_to=args['downsize_to']
    )

    # Create output folder
    os.makedirs(args['output'], exist_ok=True)

    # Process images
    process_images(args['input'], args['output'], options)

if __name__ == '__main__':
    main()
