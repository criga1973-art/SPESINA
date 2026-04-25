import requests
import subprocess
import os
import time

SUPABASE_URL = "https://uldpnhmdjbbwwqwjsdoh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsZHBuaG1kamJid3dxd2pzZG9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4NDE5ODQsImV4cCI6MjA5MjQxNzk4NH0.yXcJBcZtiaDbPl2IyDUBK-Ndoyu0unmEzfY8xZrogzM"
sb_headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}
OFF_HEADERS = {"User-Agent": "SpesinaEnrichment - Windows - Version 1.0"}

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
    # Basic mapping logic
    cats_str = ",".join(off_cats).lower()
    if "shampoo" in cats_str or "shower" in cats_str or "bagno" in cats_str: return "igiene-p", "Shampoo e Doccia"
    if "pasta" in cats_str: return "pasta", "Barilla" # Default brand if unknown
    if "beverage" in cats_str or "bevande" in cats_str: return "bevande", "Bibite"
    if "snack" in cats_str or "biscuits" in cats_str: return "colazione", "Biscotti"
    if "sauce" in cats_str or "condiment" in cats_str: return "condimenti", "Salse"
    if "dairy" in cats_str or "cheese" in cats_str: return "freschi", "Latticini"
    if "canned" in cats_str or "conserves" in cats_str: return "dispensa", "Conserve"
    return None, None

def process_image(img_url, ean):
    out = f"img/prod_{ean}.jpg"
    if os.path.exists(out): return out
    temp = f"temp_{ean}.jpg"
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

if __name__ == "__main__":
    # Get 100 products from 'da-assegnare'
    res = requests.get(f"{SUPABASE_URL}/rest/v1/products?category=eq.da-assegnare&select=id,ean&limit=100&order=id.asc", headers=sb_headers)
    products = res.json()
    print(f"Scanning {len(products)} products for images...\n")
    
    found = 0
    for p in products:
        ean = p["ean"]
        data = get_product_data(ean)
        
        if data and data["img_url"]:
            print(f"[{p['id']}] Found image for: {data['name']}")
            cat, brand = map_category(data["off_cats"])
            
            # If we identified category and have image, process it
            if cat:
                img_path = process_image(data["img_url"], ean)
                if img_path:
                    upd = {
                        "name": data["name"],
                        "category": cat,
                        "brand": brand,
                        "size": data["size"],
                        "image_url": img_path
                    }
                    requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{p['id']}", headers=sb_headers, json=upd)
                    print(f"  --> Updated DB and Image ✅")
                    found += 1
                else:
                    print(f"  --> Image processing failed ❌")
            else:
                print(f"  --> Category mapping failed (cats: {data['off_cats'][:3]}) ❌")
        else:
            # Skip silent if no image found
            pass
        
        time.sleep(0.2)
    
    print(f"\nTotal enriched with images: {found}")
