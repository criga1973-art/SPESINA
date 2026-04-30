import requests
import subprocess
import os
import time

SUPABASE_URL = "https://uldpnhmdjbbwwqwjsdoh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsZHBuaG1kamJid3dxd2pzZG9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4NDE5ODQsImV4cCI6MjA5MjQxNzk4NH0.yXcJBcZtiaDbPl2IyDUBK-Ndoyu0unmEzfY8xZrogzM"
sb_headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
OFF_HEADERS = {"User-Agent": "SpesinaEnrichment - Windows - Version 1.0"}

def upload_to_supabase(local_path, ean):
    """Carica il file su Supabase Storage e restituisce l'URL pubblico."""
    bucket_name = "products"
    file_name = f"prod_{ean}.webp"
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{file_name}"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    try:
        with open(local_path, "rb") as f:
            # Sovrascrive se esiste
            res = requests.post(url, headers=headers, data=f)
            if res.status_code in [200, 201]:
                return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_name}"
            else:
                # Se post fallisce, prova a fare l'upload (upsert non è standard via REST semplice, usiamo un trucco o ignoriamo se esiste)
                logging.info(f"Upload status: {res.status_code}")
    except Exception as e:
        print(f"Errore Upload: {e}")
    return None

def get_product_data(ean):
    try:
        r = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{ean}.json", headers=OFF_HEADERS, timeout=5)
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == 1:
                p = d["product"]
                imgs = p.get("selected_images", {}).get("front", {}).get("display", {})
                img_url = imgs.get("it") or imgs.get("en") or p.get("image_front_url")
                if img_url:
                    return {
                        "name": p.get("product_name_it") or p.get("product_name"),
                        "brand": p.get("brands", "").split(",")[0],
                        "size": p.get("quantity"),
                        "img_url": img_url,
                        "off_cats": p.get("categories_tags", [])
                    }
    except: pass
    return None

def map_category(off_cats):
    cats_str = ",".join(off_cats).lower()
    # Igiene Persona
    if any(x in cats_str for x in ["shampoo", "shower", "bagno", "hair", "capelli", "dentifricio", "toothpaste", "deodorant", "sapone", "body-wash", "hygiene", "oral-b", "colgate", "listerine"]): return "igiene-p", "Cura Persona"
    # Igiene Casa
    if any(x in cats_str for x in ["detersivo", "lavatrice", "lavavastoviglie", "detergent", "cleaning", "disinfectant", "igiene-c", "floor", "finish", "dash", "chanteclair"]): return "igiene-c", "Pulizia Casa"
    # Pasta
    if "pasta" in cats_str or "spaghetti" in cats_str or "penne" in cats_str or "fusilli" in cats_str: return "pasta", "Varie"
    # Bevande
    if any(x in cats_str for x in ["beverage", "bevande", "drink", "water", "juice", "beer", "wine", "spirits", "soda", "coca-cola", "aranciata", "the", "acqua"]): return "bevande", "Bibite"
    # Colazione
    if any(x in cats_str for x in ["snack", "biscuit", "biscotti", "colazione", "breakfast", "cereals", "muesli", "coffee", "caffe", "teas", "te", "frollini"]): return "colazione", "Varie"
    # Condimenti
    if any(x in cats_str for x in ["sauce", "condiment", "ketchup", "mayonnaise", "pesto", "vinegar", "oil", "olio", "aceto", "sale", "spice", "spezie", "maionese"]): return "condimenti", "Varie"
    # Freschi
    if any(x in cats_str for x in ["dairy", "cheese", "yogurt", "milk", "latte", "eggs", "uova", "butter", "cream", "fresh", "fresco", "formaggio", "mozzarella"]): return "freschi", "Latticini"
    # Orto (Frutta e Verdura)
    if any(x in cats_str for x in ["fruit", "vegetable", "frutta", "verdura", "orto", "apple", "banana", "salad", "insalata"]): return "orto", "Orto"
    # Vegano
    if "vegan" in cats_str or "vegano" in cats_str or "plant-based" in cats_str: return "vegano", "Vegano"
    # Panificati
    if any(x in cats_str for x in ["bread", "pane", "crackers", "grissini", "piadina", "panificati", "focaccia"]): return "panificati", "Panificati"
    # Animali
    if any(x in cats_str for x in ["pet", "dog", "cat", "cane", "gatto", "animali", "pet-food"]): return "animali", "Amici Domestici"
    # Dispensa (Default per tutto il resto che è cibo)
    if any(x in cats_str for x in ["canned", "conserve", "legume", "beans", "tuna", "fish", "baking", "flour", "farina", "lievito", "raising", "sugar", "rice", "riso", "broth", "brodo", "sauce", "tomato", "pomodoro", "food", "snack"]): return "dispensa", "Varie"
    return "dispensa", "Varie"  # Default sicuro: dispensa

def process_image(img_url, ean):
    out = f"img/prod_{ean}.webp"
    if os.path.exists(out): return out
    temp = f"temp_{ean}.webp"
    try:
        r = requests.get(img_url, headers=OFF_HEADERS, timeout=10)
        if r.status_code == 200 and len(r.content) > 5000:
            with open(temp, "wb") as f: f.write(r.content)
            # Process with rembg
            subprocess.run(["python", "process_rembg.py", temp, out, "E6E6E6"], capture_output=True)
            if os.path.exists(temp): os.remove(temp)
            if os.path.exists(out): return out
    except: pass
    return None

import sys

if __name__ == "__main__":
    # Get products that need AI processing: 
    # 1. image_url is null
    # 2. image_url is an external http link
    # 3. category is 'da-assegnare'
    try:
        # Using Supabase 'or' filter for maximum coverage - Batch of 5 - NEWEST FIRST
        url = f"{SUPABASE_URL}/rest/v1/products?or=(image_url.is.null,image_url.ilike.http*,category.eq.da-assegnare)&select=id,ean,category,brand,name,image_url&limit=50&order=id.asc"
        res = requests.get(url, headers=sb_headers)
        products = res.json()
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)

    if not isinstance(products, list):
        print(f"No products to process or error (Response: {products})")
        sys.exit(0)

    print(f"Found {len(products)} potential products to enrich.\n")
    
    found = 0
    for p in products:
        if not isinstance(p, dict):
            continue
            
        ean = p.get("ean")
        if not ean: continue
        
        # Use existing image_url if it's a link, otherwise try to find one
        img_to_process = p.get('image_url')
        if img_to_process and not img_to_process.startswith('http'):
            # Already a local image, skip
            continue
            
        data = get_product_data(ean)
        if (not img_to_process or img_to_process == '') and data:
            img_to_process = data.get('img_url')
        
        if img_to_process:
            print(f"[{p['id']}] Processing: {p.get('name') or (data['name'] if data else 'Unknown')} ({ean})")
            
            # Category/Brand logic
            cat = p.get('category')
            brand = p.get('brand')
            
            if not cat or cat == 'da-assegnare':
                if data:
                    guessed_cat, guessed_brand = map_category(data["off_cats"])
                    cat = guessed_cat
                    brand = brand or guessed_brand
            
            # If we still don't have a category, we can't save the image in a folder
            if not cat or cat == 'da-assegnare':
                cat = 'altro'
                brand = brand or 'Generico'
            
                # Process image
                img_path = process_image(img_to_process, ean)
                if img_path:
                    # BLINDAGGIO: Upload su Supabase Storage
                    cloud_url = upload_to_supabase(img_path, ean)
                    final_url = cloud_url if cloud_url else img_path

                    # Better name logic: if current name is just "Prodotto EAN", try to get a better one
                    final_name = p.get("name")
                    if not final_name or final_name.startswith("Prodotto"):
                        if data and data.get("name"):
                            final_name = data["name"]
                    
                    if not final_name:
                        final_name = f"Prodotto {ean}"

                    upd = {
                        "name": final_name,
                        "category": cat,
                        "brand": brand or "Altro",
                        "size": (data["size"] if data else ""),
                        "image_url": final_url
                    }
                    requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{p['id']}", headers=sb_headers, json=upd)
                    print(f"  --> Updated DB and Cloud Image OK")
                    found += 1
            else:
                print(f"  --> Image processing failed FAIL")
        else:
            print(f"  --> Category mapping failed FAIL")
        
        time.sleep(0.5)
    
    print(f"\nTotal enriched with images: {found}")
