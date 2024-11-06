#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import argparse
import platform

def get_system_font():
    """
    Return the appropriate system font path based on the operating system.
    For macOS, use the system Chinese font.
    """
    system = platform.system()
    if system == 'Darwin':  # macOS
        # PingFang is a system font in macOS that supports Chinese characters
        return '/System/Library/Fonts/STHeiti Medium.ttc'
    elif system == 'Linux':
        # Common paths for fonts with Chinese support in Linux
        possible_fonts = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/wqy-microhei/wqy-microhei.ttc'
        ]
        for font_path in possible_fonts:
            if os.path.exists(font_path):
                return font_path
    elif system == 'Windows':
        # Microsoft YaHei is a common Chinese font in Windows
        return 'C:\\Windows\\Fonts\\msyh.ttc'

    # If no system-specific font is found, return a common fallback
    return '/System/Library/Fonts/PingFang.ttc'

def add_watermark(image_path, output_path, watermark_text="© Your Name", font_size=40):
    """
    Add a watermark to an image and save it to the output path.

    Args:
        image_path (str): Path to the source image
        output_path (str): Path where the watermarked image will be saved
        watermark_text (str): Text to use as watermark
        font_size (int): Size of the watermark font
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Create a transparent overlay for the watermark
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Try to use system font that supports Chinese characters
            try:
                font_path = get_system_font()
                font = ImageFont.truetype(font_path, font_size)
            except OSError as e:
                print(f"Warning: Could not load system font ({str(e)}). Using default font.")
                font = ImageFont.load_default()

            # Calculate text size
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate position (bottom-right corner with padding)
            padding = 20
            position = (
                img.width - text_width - padding,
                img.height - text_height - padding
            )

            # Draw the watermark text with a slight shadow
            shadow_position = (position[0] + 2, position[1] + 2)
            draw.text(shadow_position, watermark_text, font=font, fill=(0, 0, 0, 50))
            draw.text(position, watermark_text, font=font, fill=(255, 255, 255, 80))

            # Combine the original image with the watermark overlay
            watermarked = Image.alpha_composite(img, overlay)

            # Convert back to RGB if the output format doesn't support alpha
            if Path(output_path).suffix.lower() in ['.jpg', '.jpeg']:
                watermarked = watermarked.convert('RGB')

            # Save the watermarked image
            watermarked.save(output_path)
            print(f"Processed: {image_path}")

    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")

def process_folder(input_folder, output_folder, watermark_text="© Your Name"):
    """
    Process all images in the input folder and save watermarked versions to the output folder.

    Args:
        input_folder (str): Path to the folder containing source images
        output_folder (str): Path to the folder where watermarked images will be saved
        watermark_text (str): Text to use as watermark
    """
    # Expand user home directory if present
    input_folder = os.path.expanduser(input_folder)
    output_folder = os.path.expanduser(output_folder)

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Supported image formats
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    # Count total and processed images
    total_images = sum(1 for f in Path(input_folder).glob('*')
                      if f.suffix.lower() in supported_formats)
    processed_images = 0

    # Process each image in the input folder
    for file_path in Path(input_folder).glob('*'):
        if file_path.suffix.lower() in supported_formats:
            output_path = Path(output_folder) / file_path.name
            add_watermark(str(file_path), str(output_path), watermark_text)
            processed_images += 1
            print(f"Progress: {processed_images}/{total_images} images")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Add watermarks to images in a folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i ~/Pictures/originals -o ~/Pictures/watermarked -w "© 张伟 2024"
  %(prog)s --input-folder ./photos --output-folder ./watermarked --watermark "私人文件"
  %(prog)s -i ./input -o ./output -w "机密文件" -s 60
        """
    )

    parser.add_argument('-i', '--input-folder', required=True,
                        help='Path to the folder containing original images')
    parser.add_argument('-o', '--output-folder', required=True,
                        help='Path to the folder where watermarked images will be saved')
    parser.add_argument('-w', '--watermark', default='© Your Name',
                        help='Text to use as watermark (default: "© Your Name")')
    parser.add_argument('-s', '--font-size', type=int, default=40,
                        help='Font size for the watermark (default: 40)')

    # Parse arguments
    args = parser.parse_args()

    # Process the images
    print("\nStarting watermark process...")
    process_folder(args.input_folder, args.output_folder, args.watermark)
    print("\nWatermarking complete!")
    print(f"Processed images saved to: {os.path.abspath(args.output_folder)}")

if __name__ == "__main__":
    main()
