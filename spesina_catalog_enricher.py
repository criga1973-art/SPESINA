import requests
from bs4 import BeautifulSoup
import json
import time
import re
import sys

SUPABASE_URL = "https://uldpnhmdjbbwwqwjsdoh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsZHBuaG1kamJid3dxd2pzZG9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4NDE5ODQsImV4cCI6MjA5MjQxNzk4NH0.yXcJBcZtiaDbPl2IyDUBK-Ndoyu0unmEzfY8xZrogzM";
h = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}', 'Content-Type': 'application/json'}

def get_catalog():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/products?select=id,ean,name&category=eq.pasta&category=neq.archivio&ean=not.is.null", headers=h)
    return {p['ean']: p for p in res.json()}

def get_all_product_links(query):
    links = set()
    # Correct URL parameter is 'q'
    for page in range(1, 6):
        url = f"https://sugros.com/catalogo-prodotti-alimentari-ingrosso?q={query.replace(' ', '+')}&page={page}"
        print(f"   Scanning page {page} for '{query}'...", flush=True)
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            page_links = []
            for a in soup.find_all('a', href=True):
                if '/prodotto/' in a['href'] and not 'catalogo' in a['href']:
                    page_links.append(a['href'])
            
            if not page_links: break
            links.update(page_links)
            if len(page_links) < 5: break
            time.sleep(0.3)
        except:
            break
    return list(links)

def extract_product_data(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'80\d{11}', text)
        ean = match.group(0) if match else None
        if not ean: return None
        
        data = {}
        def find_val(label):
            tag = soup.find(string=re.compile(label, re.I))
            if tag:
                # Look for the text in the next div or the container that follows the label
                container = tag.find_parent('div')
                if container:
                    # Often the value is in the next sibling div or inside the same div but after the label
                    val_text = container.get_text(strip=True).replace(tag.get_text(strip=True), "").strip()
                    if val_text: return val_text
                    # Fallback to next sibling
                    nxt = container.find_next_sibling('div')
                    if nxt: return nxt.get_text(strip=True)
            return ""

        data['legale'] = find_val("Denominazione legale di vendita")
        data['mkt'] = find_val("Dichiarazione marketing")
        data['a'] = find_val("Allergeni")
        data['s'] = find_val("Conservazione")
        data['c'] = find_val("Istruzioni per l'uso")
        return ean, data
    except:
        return None

# Main
catalog = get_catalog()
print(f"Catalog contains {len(catalog)} active pasta products.", flush=True)

queries = ["Barilla", "Voiello"]
processed_eans = set()
matches_count = 0

for query in queries:
    print(f"\nProcessing {query}...", flush=True)
    links = get_all_product_links(query)
    print(f"Found {len(links)} links.", flush=True)
    
    for link in links:
        if not link.startswith('http'): link = "https://sugros.com" + link
        res_data = extract_product_data(link)
        if not res_data: continue
        ean, data = res_data
        
        if ean in processed_eans: continue
        processed_eans.add(ean)
        
        if ean in catalog:
            p = catalog[ean]
            print(f"   [MATCH] {p['name']} (EAN {ean})", flush=True)
            
            desc = f"{data.get('legale', '')}. {data.get('mkt', '')}".strip(". ")
            if len(desc) < 5: desc = p['name']
            
            info = {
                "d": desc,
                "a": data.get('a', 'N/A'),
                "s": data.get('s', 'N/A'),
                "c": data.get('c', 'N/A')
            }
            info = {k: v for k, v in info.items() if v and v != 'N/A' and len(v) > 2}
            
            requests.patch(f"{SUPABASE_URL}/rest/v1/products?id=eq.{p['id']}", headers=h, json={"info": info})
            matches_count += 1
            print(f"      -> Updated.", flush=True)

print(f"\nFINITO! Aggiornati {matches_count} prodotti.", flush=True)
