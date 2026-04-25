import os
import sys
import requests
from rembg import remove
from PIL import Image
import io
from supabase import create_client

# Prende le chiavi dalle impostazioni segrete di GitHub
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_product(ean, category, brand):
    print(f"🚀 Cerco immagine per EAN: {ean}")
    
    # 1. Cerca su Google Images
    search_url = f"https://serpapi.com{ean}+prodotto+pacco&tbm=isch&api_key={SERPAPI_KEY}"
    res = requests.get(search_url).json()
    img_url = res['images_results'][0]['original'] 

    # 2. Rimuove lo sfondo
    img_data = requests.get(img_url).content
    output = remove(img_data)
    img = Image.open(io.BytesIO(output)).convert("RGBA")

    # 3. Mette il fondo grigio #e6e6e6
    canvas = Image.new("RGBA", img.size, "#e6e6e6")
    canvas.paste(img, (0, 0), img)
    final_img = canvas.convert("RGB")

    # 4. Crea il percorso cartella
    path = f"public/products/{category}/{brand}".lower().replace(" ", "-")
    os.makedirs(path, exist_ok=True)

    # 5. Salva il file
    filename = f"{ean}.jpg"
    final_path = os.path.join(path, filename)
    final_img.save(final_path, "JPEG", quality=90)

    # 6. Aggiorna Supabase
    web_url = f"/{final_path}"
    supabase.table('products').update({"image_url": web_url}).eq('ean', ean).execute()
    print(f"✅ Successo! Immagine salvata in {web_url}")

if __name__ == "__main__":
    # Legge i dati inviati dal bot [EAN, Categoria, Marca]
    if len(sys.argv) > 3:
        process_product(sys.argv[1], sys.argv[2], sys.argv[3])
