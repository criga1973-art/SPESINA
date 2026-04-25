import sys
import os
from PIL import Image
from rembg import remove

def process_with_rembg(input_path, output_path, bg_color_hex="FFFFFF"):
    print(f"Removing background from {input_path} (BG: #{bg_color_hex})...")
    
    # Parse hex color
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    
    # Open image
    input_image = Image.open(input_path)
    
    # Remove background
    output_image = remove(input_image)
    
    # Find bounding box of the non-transparent area
    bbox = output_image.getbbox()
    if not bbox:
        print("Error: Could not identify the product.")
        return
    
    # Crop to content
    img_cropped = output_image.crop(bbox)
    
    # Create canvas 1000x1000 with custom BG
    canvas_size = 1000
    canvas = Image.new("RGBA", (canvas_size, canvas_size), bg_color)
    
    # Resize to fit 850x850
    max_size = 850
    w, h = img_cropped.size
    ratio = min(max_size / w, max_size / h)
    new_size = (int(w * ratio), int(h * ratio))
    img_resized = img_cropped.resize(new_size, Image.Resampling.LANCZOS)
    
    # Paste centered
    px = (canvas_size - new_size[0]) // 2
    py = (canvas_size - new_size[1]) // 2
    canvas.paste(img_resized, (px, py), img_resized)
    
    # Convert to RGB (remove alpha) before saving as JPEG
    final_img = canvas.convert("RGB")
    
    # Save final result - auto detect format from extension
    ext = os.path.splitext(output_path)[1].lower()
    fmt = "WEBP" if ext == ".webp" else "JPEG"
    
    final_img.save(output_path, fmt, quality=95 if fmt == "JPEG" else 85)
    print(f"Success! Product saved to {output_path} with background #{bg_color_hex} (Format: {fmt})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_rembg.py <input> <output> [bg_color_hex]")
    else:
        bg = sys.argv[3] if len(sys.argv) > 3 else "FFFFFF"
        process_with_rembg(sys.argv[1], sys.argv[2], bg)
