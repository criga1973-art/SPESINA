import os
import threading
import asyncio
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import cv2
import zxingcpp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv() # Carica variabili da .env se presente in locale

# --- CONFIGURAZIONE (Legge da Variabili d'Ambiente su Render o .env) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://uldpnhmdjbbwwqwjsdoh.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")

# --- DATI GITHUB ---
GH_OWNER = "criga1973-art"
GH_REPO = "SPESINA"

# --- STRUTTURA CATEGORIE ---
CAT_MAP = {
    "pasta": {"n": "Pasta e Riso", "sub": ["Pasta", "Riso"], "iva": 4},
    "bevande": {"n": "Bevande", "sub": ["Acqua", "Succhi di Frutta", "Birra", "Vino", "Bibite", "Latte 1L", "Latte 500ml", "Alcolici", "Altro"], "iva": 22},
    "freschi": {"n": "Freschi", "sub": ["Salumi", "Latticini", "Yogurt", "Uova", "Piatti Pronti", "Pasta Sfoglia"], "iva": 10},
    "dispensa": {"n": "Dispensa", "sub": ["Tonno e Carne in scatola", "Verdure e Legumi", "Conserve", "Insalatissime", "Sotto olio Sotto aceto"], "iva": 10},
    "snack-salati": {"n": "Snack Salati", "sub": [], "iva": 10},
    "snack-dolci": {"n": "Snack Dolci", "sub": [], "iva": 10},
    "caramelle-dolciumi": {"n": "Caramelle e Dolciumi", "sub": [], "iva": 22},
    "senza-glutine": {"n": "Senza Glutine", "sub": [], "iva": 10},
    "parafarmacia": {"n": "Parafarmacia", "sub": [], "iva": 10},
    "farine": {"n": "Farine e Preparati", "sub": ["Farine", "Preparati", "Lieviti", "Altro"], "iva": 4},
    "condimenti": {"n": "Condimenti e Spezie", "sub": ["Olio", "Aceto", "Sale", "Sughi e Pesti", "Salse", "Spezie", "Altro"], "iva": 10},
    "igiene-p": {"n": "Igiene Persona", "sub": ["Primo Soccorso", "Shampoo e Doccia", "Deodoranti", "Igiene Orale", "Assorbenti e Protezione", "Incontinenza Tena", "Carta e Fazzoletti", "Barba e Rasatura", "Altro"], "iva": 22},
    "igiene-c": {"n": "Igiene Casa e Detersivi", "sub": ["Lavatrice", "Superfici", "Piatti", "Altro"], "iva": 22},
    "surgelati": {"n": "Surgelati", "sub": ["Pizze e Panificati", "Verdure", "Pesce", "Piatti Pronti", "Gelati", "Patatine fritte"], "iva": 10},
    "colazione": {"n": "Colazione", "sub": ["Biscotti", "Merendine", "Cereali", "Caffè, Tè e Tisane", "Confetture e Creme", "Altro"], "iva": 10},
    "panificati": {"n": "Panificati", "sub": ["Panificati", "Altro"], "iva": 4},
    "orto": {"n": "Frutta e Verdura", "sub": ["Frutta e Verdura", "Altro"], "iva": 4},
    "vegano": {"n": "Vegano", "sub": ["Vegano", "Altro"], "iva": 10},
    "animali": {"n": "Amici Domestici", "sub": ["Amici Domestici", "Altro"], "iva": 22},
    "minestre-zuppe": {"n": "Minestre, Risotti e Zuppe", "f": "Minestre Risotti e Zuppe", "sub": [], "iva": 10},
    "prima-infanzia": {"n": "Prima Infanzia", "sub": [], "iva": 5},
    "varie": {"n": "VarIE", "sub": [], "iva": 22}
}

def calculate_prices(super_price, vat_rate, markup_percentage=14):
    """Calcola i prezzi scorporati, ricaricati e l'IVA."""
    super_net = super_price / (1 + vat_rate / 100)
    final_net = super_net * (1 + markup_percentage / 100)
    ricarico_netto = final_net - super_net
    final_price = final_net * (1 + vat_rate / 100)
    final_price_cents = int(round(final_price * 100))
    price_to_save = final_price_cents / 100.0
    return {
        "price_to_save": price_to_save,
        "super_net": round(super_net, 2),
        "ricarico_netto": round(ricarico_netto, 2),
        "vat_rate": vat_rate,
        "final_price_cents": final_price_cents
    }


if not SUPABASE_KEY:
    print("ERRORE: Variabile SUPABASE_KEY non trovata! Controlla il file .env o le variabili d'ambiente.")

if not TELEGRAM_TOKEN:
    print("ERRORE: Variabile TELEGRAM_TOKEN non trovata! Controlla il file .env o le variabili d'ambiente.")

if SUPABASE_KEY and SUPABASE_URL:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

user_states = {}

def upload_to_supabase(image_bytes, ean, folder_name="", sub_name=""):
    """Carica l'immagine direttamente su Supabase Storage nella cartella categoria/sottocategoria."""
    import urllib.parse
    bucket_name = "products"
    
    # Costruiamo il percorso: Categoria / [Sottocategoria] / prod_EAN.webp
    folder_prefix = f"{folder_name}/" if folder_name else ""
    sub_prefix = f"{sub_name}/" if sub_name else ""
    file_name = f"{folder_prefix}{sub_prefix}prod_{ean}.webp"
    
    encoded_file_name = urllib.parse.quote(file_name)
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{encoded_file_name}"
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "image/webp"
    }
    
    try:
        requests.post(url, headers=headers, data=image_bytes)
        # Se il caricamento va a buon fine (200 o 201), restituiamo l'URL pubblico
        return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{encoded_file_name}"
    except Exception as e:
        logging.error(f"Errore Upload Cloud: {e}")
    return None

def avvisa_github_per_foto(ean, categoria, sottocategoria):
    url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/dispatches"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"event_type": "nuovo_prodotto", "client_payload": {"ean": ean, "category": categoria, "subcategory": sottocategoria}}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.info(f"GitHub signaled: {r.status_code}")
    except Exception as e: logging.error(f"GitHub Error: {e}")

def fetch_off_data(ean):
    url = f"https://world.openfoodfacts.org/api/v0/product/{ean}.json"
    headers = {"User-Agent": "SpesinaBot - Telegram - Version 1.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get('status') == 1:
                p = d['product']
                return {
                    'name': p.get('product_name_it') or p.get('product_name') or f"Prodotto {ean}",
                    'image_url': '', # Non prendiamo più la foto dal web
                    'size': p.get('quantity', ''),
                    'info': {'d': p.get('generic_name_it') or "", 'a': p.get('allergens') or "Nessuno"}
                }
    except: pass
    return {'name': f"Prodotto {ean}", 'image_url': "", 'size': "", 'info': {}}

def detect_barcode(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None: return None
        
        def get_valid_ean(res_list):
            for r in res_list:
                if r.text.isdigit() and len(r.text) >= 8:
                    return r.text
            return None

        results = zxingcpp.read_barcodes(img)
        if results: 
            valid = get_valid_ean(results)
            if valid: return valid
            
        h, w = img.shape[:2]
        resized = cv2.resize(img, (int(w*1.5), int(h*1.5)))
        results = zxingcpp.read_barcodes(resized)
        if results:
            return get_valid_ean(results)
        return None
    except: return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    state = user_states.get(chat_id)

    try:
        if state and state.get('step') in ['waiting_price', 'waiting_price_update', 'waiting_price_both']:
            clean_text = text.replace(',', '.')
            if len(text) >= 8 and text.isdigit():
                await update.message.reply_text("⚠️ Sembra un codice a barre. Inserisci il **prezzo** (es: 1.50):")
                return

            try:
                price = float(clean_text)
                if price > 999999:
                    await update.message.reply_text("❌ Prezzo troppo alto.")
                    return

                state['price'] = price
                if state['step'] == 'waiting_price_update':
                    # Recupera la categoria del prodotto per l'IVA
                    prod_res = supabase.table('products').select('category').eq('id', state['existing_id']).single().execute()
                    prod_cat = prod_res.data.get('category') if prod_res.data else 'varie'
                    
                    cat_obj = CAT_MAP.get(prod_cat, {})
                    vat_rate = cat_obj.get('iva', 22)
                    prices = calculate_prices(price, vat_rate)
                    
                    upd_data = {
                        'price': prices["price_to_save"],
                        'prezzo_supermercato_netto': prices["super_net"],
                        'ricarico_netto': prices["ricarico_netto"],
                        'aliquota_iva': prices["vat_rate"],
                        'prezzo_finale_al_cliente_cents': prices["final_price_cents"]
                    }
                    supabase.table('products').update(upd_data).eq('id', state['existing_id']).execute()
                    await update.message.reply_text(f"✅ **PREZZO AGGIORNATO!** ({prices['price_to_save']}€)")
                    del user_states[chat_id]
                elif state['step'] == 'waiting_price_both':
                    state['step'] = 'waiting_image_update'
                    await update.message.reply_text(f"✅ Prezzo memorizzato. Ora inviami la **NUOVA FOTO**:")
                else:
                    state['step'] = 'waiting_image'
                    await update.message.reply_text("📸 **Mi dai l'immagine del prodotto?**")
            except ValueError:
                await update.message.reply_text("❌ Inserisci un prezzo valido (es: 1.50).")
            return

        if text.isdigit() and len(text) >= 8:
            await process_ean(text, update)
            
    except Exception as e:
        logging.error(f"MESSAGE ERROR: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore imprevisto: {e}")
        if chat_id in user_states: del user_states[chat_id]

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    
    await query.answer() 

    state = user_states.get(chat_id)
    if not state:
        await query.message.reply_text("❌ Sessione scaduta o bot riavviato. Riprova da capo.")
        return

    try:
        if data == "upd_price":
            state['step'] = 'waiting_price_update'
            await query.edit_message_text(f"💰 Inserisci il **NUOVO PREZZO** per {state['existing_name']}:")
        elif data == "upd_image":
            state['step'] = 'waiting_image_update'
            await query.edit_message_text(f"📸 Inviami la **NUOVA FOTO** per {state['existing_name']}:")
        elif data == "upd_both":
            state['step'] = 'waiting_price_both'
            await query.edit_message_text(f"💰 Inserisci il **NUOVO PREZZO** per {state['existing_name']}:")
        
        elif data.startswith("cat_"):
            cat_id = data.replace("cat_", "")
            state['category'] = cat_id
            cat_obj = CAT_MAP.get(cat_id, {})
            folder_name = cat_obj.get('f', cat_obj.get('n', ""))
            subfolders = cat_obj.get('sub', [])
            if not subfolders:
                state['subcategory'] = ""
                
                # Se abbiamo una foto in attesa, carichiamola ora nella cartella corretta
                if state.get('photo_bytes'):
                    cloud_url = upload_to_supabase(state['photo_bytes'], state['ean'], folder_name)
                    if cloud_url: state['image_url'] = cloud_url

                # Calcoli prezzi
                vat_rate = cat_obj.get('iva', 22)
                prices = calculate_prices(state['price'], vat_rate)

                new_prod = {
                    "ean": state['ean'], "name": state['name'], "price": prices["price_to_save"],
                    "category": state['category'], "subcategory": state['subcategory'],
                    "image_url": state['image_url'], "size": state.get('size', ''), "info": state.get('info', {}),
                    "prezzo_supermercato_netto": prices["super_net"],
                    "ricarico_netto": prices["ricarico_netto"],
                    "aliquota_iva": prices["vat_rate"],
                    "prezzo_finale_al_cliente_cents": prices["final_price_cents"]
                }
                supabase.table('products').upsert(new_prod).execute()
                asyncio.create_task(asyncio.to_thread(avvisa_github_per_foto, state['ean'], state['category'], state['subcategory']))
                await query.edit_message_text(f"✅ **SALVATO!**\n📦 {state['name']}\n📂 {folder_name}\n💰 {state['price']}€\n\nImmagine salvata in: {folder_name} 🚀")
                if chat_id in user_states: del user_states[chat_id]
            else:
                state['step'] = 'waiting_brand'
                buttons = [[InlineKeyboardButton(s, callback_data=f"sub_{s}")] for s in subfolders]
                await query.edit_message_text(f"📁 **Categoria: {folder_name}**\nScegli la SOTTO-CARTELLA:", reply_markup=InlineKeyboardMarkup(buttons))
        
        elif data.startswith("sub_"):
            sub_name = data.replace("sub_", "")
            state['subcategory'] = sub_name
            cat_id = state['category']
            cat_obj = CAT_MAP.get(cat_id, {})
            folder_name = cat_obj.get('f', cat_obj.get('n', ""))
            
            # Carichiamo la foto nel percorso ANNIDATO: Categoria / Sottocategoria / prod_EAN.webp
            # Puliamo il nome della sotto-cartella per lo storage (rimuoviamo accenti e virgole)
            safe_sub = sub_name.replace("à", "a").replace("è", "e").replace("é", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u").replace(",", "")
            if state.get('photo_bytes'):
                cloud_url = upload_to_supabase(state['photo_bytes'], state['ean'], folder_name, safe_sub)
                if cloud_url: state['image_url'] = cloud_url

            # Calcoli prezzi
            vat_rate = cat_obj.get('iva', 22)
            prices = calculate_prices(state['price'], vat_rate)

            new_prod = {
                "ean": state['ean'], "name": state['name'], "price": prices["price_to_save"],
                "category": state['category'], "subcategory": state['subcategory'],
                "image_url": state['image_url'], "size": state.get('size', ''), "info": state.get('info', {}),
                "prezzo_supermercato_netto": prices["super_net"],
                "ricarico_netto": prices["ricarico_netto"],
                "aliquota_iva": prices["vat_rate"],
                "prezzo_finale_al_cliente_cents": prices["final_price_cents"]
            }
            supabase.table('products').upsert(new_prod).execute()
            asyncio.create_task(asyncio.to_thread(avvisa_github_per_foto, state['ean'], state['category'], state['subcategory']))
            
            await query.edit_message_text(f"✅ **SALVATO!**\n📦 {state['name']}\n📂 {folder_name} > {sub_name}\n💰 {state['price']}€\n\nImmagine salvata in: {folder_name}/{sub_name} 🚀")
            if chat_id in user_states: del user_states[chat_id]

    except Exception as e:
        logging.error(f"CALLBACK ERROR: {e}", exc_info=True)
        await query.message.reply_text(f"❌ Errore: {e}")
        if chat_id in user_states: del user_states[chat_id]

async def process_ean(ean, update):
    chat_id = update.effective_chat.id
    response = supabase.table('products').select('*').eq('ean', ean).execute()
    if response.data:
        p = response.data[0]
        user_states[chat_id] = {
            'existing_id': p['id'], 
            'existing_name': p['name'],
            'existing_cat': p.get('category'),
            'existing_subcategory': p.get('subcategory'),
            'step': 'waiting_choice_update'
        }
        msg = (f"🔄 **PRODOTTO GESTITO**\n🏷️ {p['name']}\n💰 Prezzo: {p['price']}€\n\n"
               "Cosa vuoi aggiornare?")
        buttons = [
            [InlineKeyboardButton("💰 Solo Prezzo", callback_data="upd_price")],
            [InlineKeyboardButton("📸 Solo Foto", callback_data="upd_image")],
            [InlineKeyboardButton("🔄 Entrambi", callback_data="upd_both")]
        ]
        await update.effective_message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        data = fetch_off_data(ean)
        user_states[chat_id] = {
            'ean': ean, 'name': data['name'], 'image_url': data['image_url'], 
            'size': data['size'], 'info': data['info'], 'step': 'waiting_price'
        }
        await update.effective_message.reply_text(f"📦 **NUOVO**: {data['name']} ({data['size']})\n💰 Prezzo di vendita?")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.message.chat_id
        state = user_states.get(chat_id)
        if state and state.get('step') in ['waiting_image', 'waiting_image_update']:
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            
            if state['step'] == 'waiting_image_update':
                # Per aggiornamenti, conosciamo gia' categoria e sotto-categoria (brand)
                cat_id = state.get('existing_cat')
                sub_name = state.get('existing_subcategory', "")
                cat_obj = CAT_MAP.get(cat_id, {})
                folder_name = cat_obj.get('f', cat_obj.get('n', ""))
                
                if not folder_name:
                    # Se la categoria non e' valida, chiediamola di nuovo per sicurezza
                    state['photo_bytes'] = photo_bytes
                    state['step'] = 'waiting_category'
                    buttons = [[InlineKeyboardButton(c['n'], callback_data=f"cat_{cat_id}")] for cat_id, c in CAT_MAP.items()]
                    await update.message.reply_text("⚠️ Categoria non trovata per l'aggiornamento. **Sceglila ora:**", reply_markup=InlineKeyboardMarkup(buttons))
                    return

                ean_or_id = state.get('ean') or state.get('existing_id')
            
                # Puliamo il nome della sotto-cartella per lo storage
                safe_sub = sub_name.replace("à", "a").replace("è", "e").replace("é", "e").replace("ì", "i").replace("ò", "o").replace("ù", "u").replace(",", "")
            
                cloud_url = upload_to_supabase(photo_bytes, ean_or_id, folder_name, safe_sub)
                if cloud_url: state['image_url'] = cloud_url
                
                upd = {"image_url": state['image_url']}
                if state.get('price'): 
                    # Recupera la categoria del prodotto per l'IVA
                    prod_res = supabase.table('products').select('category').eq('id', state['existing_id']).single().execute()
                    prod_cat = prod_res.data.get('category') if prod_res.data else 'varie'
                    
                    cat_obj = CAT_MAP.get(prod_cat, {})
                    vat_rate = cat_obj.get('iva', 22)
                    prices = calculate_prices(state['price'], vat_rate)
                    
                    upd.update({
                        'price': prices["price_to_save"],
                        'prezzo_supermercato_netto': prices["super_net"],
                        'ricarico_netto': prices["ricarico_netto"],
                        'aliquota_iva': prices["vat_rate"],
                        'prezzo_finale_al_cliente_cents': prices["final_price_cents"]
                    })
                
                supabase.table('products').update(upd).eq('id', state['existing_id']).execute()
                await update.message.reply_text(f"✅ **FOTO AGGIORNATA!**\nSalvata in: {folder_name}/{sub_name}")
                if chat_id in user_states: del user_states[chat_id]
            else:
                # Per nuovi prodotti, memorizziamo i bytes e aspettiamo la scelta categoria
                state['photo_bytes'] = photo_bytes
                state['step'] = 'waiting_category'
                buttons = [[InlineKeyboardButton(c['n'], callback_data=f"cat_{cat_id}")] for cat_id, c in CAT_MAP.items()]
                await update.message.reply_text("📂 **Scegli la CATEGORIA:**", reply_markup=InlineKeyboardMarkup(buttons))
            return

        # Scansione Barcode
        photo_file = await update.message.photo[-1].get_file()
        path = f"tmp_{chat_id}.jpg"
        await photo_file.download_to_drive(path)
        ean = detect_barcode(path)
        if ean: await process_ean(ean, update)
        else: await update.message.reply_text("❌ Codice non letto.")
        if os.path.exists(path): os.remove(path)
    except Exception as e:
        logging.error(f"PHOTO ERROR: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Errore durante l'elaborazione foto: {e}")
        if chat_id in user_states: del user_states[chat_id]

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    if not TELEGRAM_TOKEN:
        print("Il bot non può essere avviato senza TELEGRAM_TOKEN. Esce.")
        exit(1)
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Bot attivo con menu pulsanti!")
    app.run_polling()

