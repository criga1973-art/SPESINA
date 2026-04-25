import sys
import os
from PIL import Image, ImageFilter
from rembg import remove

def process_with_rembg(input_path, output_path, bg_color_hex="FFFFFF"):
    print(f"Removing background from {input_path} (BG: #{bg_color_hex})...")
    
    # Parse hex color
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    
    # Open image
    img = Image.open(input_path)
    
    # SAFETY CROP: Aggressively remove edges to clear UI icons (Google Lens, etc.)
    w_orig, h_orig = img.size
    if w_orig > 300 and h_orig > 300:
        # Tagliamo di più sotto e a sinistra dove di solito ci sono le icone
        left = int(w_orig * 0.08)
        top = int(h_orig * 0.05)
        right = int(w_orig * 0.95)
        bottom = int(h_orig * 0.88) # Più aggressivo sotto
        img = img.crop((left, top, right, bottom))
    
    # Remove background
    output_image = remove(img)
    
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
    
    # SHARPEN: Enhance details after resizing
    img_resized = img_resized.filter(ImageFilter.SHARPEN)
    
    # Paste centered
    px = (canvas_size - new_size[0]) // 2
    py = (canvas_size - new_size[1]) // 2
    canvas.paste(img_resized, (px, py), img_resized)
    
    # Convert to RGB (remove alpha) before saving
    final_img = canvas.convert("RGB")
    
    # Save final result
    ext = os.path.splitext(output_path)[1].lower()
    fmt = "WEBP" if ext == ".webp" else "JPEG"
    
    final_img.save(output_path, fmt, quality=90 if fmt == "WEBP" else 95)
    print(f"Success! Product saved to {output_path} (Format: {fmt})")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_rembg.py <input> <output> [bg_color_hex]")
    else:
        bg = sys.argv[3] if len(sys.argv) > 3 else "FFFFFF"
        process_with_rembg(sys.argv[1], sys.argv[2], bg)
