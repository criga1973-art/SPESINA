import os
import logging
import requests
import cv2
import numpy as np
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
    "pasta": {"n": "Pasta & Riso", "sub": []},  # PIATTA
    "bevande": {"n": "Bevande", "sub": ["Acqua", "Succhi di Frutta", "Birra", "Vino", "Bibite", "Latte 1L", "Latte 500ml", "Alcolici", "Altro"]},
    "freschi": {"n": "Freschi & Latticini", "sub": ["Salumi", "Latticini", "Yogurt", "Uova", "Altro"]},
    "dispensa": {"n": "Dispensa", "sub": ["Tonno e Carne in scatola", "Verdure e Legumi", "Conserve", "Insalatissime", "Altro"]},
    "farine": {"n": "Farine & Preparati", "sub": ["Farine", "Preparati", "Lieviti", "Altro"]},
    "condimenti": {"n": "Olio & Condimenti", "sub": ["Olio", "Aceto", "Sale", "Sughi e Pesti", "Salse", "Spezie", "Altro"]},
    "igiene-p": {"n": "Igiene Persona", "sub": ["Primo Soccorso", "Shampoo e Doccia", "Deodoranti", "Igiene Orale", "Assorbenti e Protezione", "Incontinenza Tena", "Carta e Fazzoletti", "Barba e Rasatura", "Altro"]},
    "igiene-c": {"n": "Igiene Casa", "sub": ["Lavatrice", "Superfici", "Piatti", "Altro"]},
    "surgelati": {"n": "Surgelati", "sub": ["Pizze e Panificati", "Verdure", "Pesce", "Piatti Pronti", "Gelati", "Altro"]},
    "colazione": {"n": "Colazione & Dolci", "sub": ["Biscotti", "Merendine", "Cereali", "Caffè, Tè e Tisane", "Confetture e Creme", "Altro"]},
    "panificati": {"n": "Panificati", "sub": ["Panificati", "Altro"]},
    "orto": {"n": "Ortofrutta", "sub": ["Frutta e Verdura", "Altro"]},
    "vegano": {"n": "Vegano", "sub": ["Vegano", "Altro"]},
    "animali": {"n": "Amici Animali", "sub": ["Amici Domestici", "Altro"]},
    "varie": {"n": "VarIE", "sub": ["Varie"]}
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

def avvisa_github_per_foto(ean, categoria, brand):
    url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/dispatches"
    headers = {"Authorization": f"token {GH_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"event_type": "nuovo_prodotto", "client_payload": {"ean": ean, "category": categoria, "brand": brand}}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        logging.info(f"GitHub signaled: {r.status_code}")
    except Exception as e: logging.error(f"GitHub Error: {e}")

def fetch_off_data(ean):
    url = f"https://world.openfoodfacts.org/api/v0/product/{ean}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            d = r.json()
            if d.get('status') == 1:
                p = d['product']
                return {
                    'name': p.get('product_name_it') or p.get('product_name') or f"Prodotto {ean}",
                    'image_url': p.get('image_url', ''),
                    'info': {'d': p.get('generic_name_it') or "", 'a': p.get('allergens') or "Nessuno"}
                }
    except: pass
    return {'name': f"Prodotto {ean}", 'image_url': "", 'info': {}}

def detect_barcode(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None: return None
        results = zxingcpp.read_barcodes(img)
        if results: return results[0].text
        h, w = img.shape[:2]
        resized = cv2.resize(img, (int(w*1.5), int(h*1.5)))
        results = zxingcpp.read_barcodes(resized)
        return results[0].text if results else None
    except: return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    state = user_states.get(chat_id)

    if state and state.get('step') in ['waiting_price', 'waiting_price_update']:
        try:
            price = float(text.replace(',', '.'))
            state['price'] = price
            if state['step'] == 'waiting_price_update':
                supabase.table('products').update({'price': price}).eq('id', state['existing_id']).execute()
                await update.message.reply_text(f"✅ **PREZZO AGGIORNATO!** ({price}€)")
                del user_states[chat_id]
            else:
                state['step'] = 'waiting_category'
                buttons = [[InlineKeyboardButton(c['n'], callback_data=f"cat_{id}")] for id, c in CAT_MAP.items()]
                await update.message.reply_text("📂 **Scegli la CATEGORIA:**", reply_markup=InlineKeyboardMarkup(buttons))
        except:
            await update.message.reply_text("❌ Inserisci un prezzo valido.")
        return

    if text.isdigit() and len(text) >= 8:
        await process_ean(text, update)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data
    
    await query.answer() # Ferma il caricamento sul pulsante

    state = user_states.get(chat_id)

    if not state:
        await query.message.reply_text("❌ Sessione scaduta o bot riavviato. Riprova da capo inviando il prodotto.")
        return

    if data.startswith("cat_"):
        cat_id = data.replace("cat_", "")
        state['category'] = cat_id
        subfolders = CAT_MAP[cat_id]['sub']
        
        if not subfolders:
            # Salta il passaggio del brand se la lista è vuota (es. Pasta)
            state['brand'] = ""
            new_prod = {
                "ean": state['ean'], "name": state['name'], "price": state['price'],
                "category": state['category'], "brand": state['brand'],
                "image_url": state['image_url'], "info": state['info']
            }
            supabase.table('products').upsert(new_prod).execute()
            avvisa_github_per_foto(state['ean'], state['category'], state['brand'])
            await query.edit_message_text(f"✅ **SALVATO!**\n📦 {state['name']}\n📂 {CAT_MAP[state['category']]['n']}\n💰 {state['price']}€\n\nL'AI sta preparando la foto... 🚀")
            del user_states[chat_id]
        else:
            state['step'] = 'waiting_brand'
            buttons = [[InlineKeyboardButton(s, callback_data=f"sub_{s}")] for s in subfolders]
            await query.edit_message_text(f"📁 **Categoria: {CAT_MAP[cat_id]['n']}**\nScegli la SOTTO-CARTELLA:", reply_markup=InlineKeyboardMarkup(buttons))
    
    elif data.startswith("sub_"):
        sub_name = data.replace("sub_", "")
        state['brand'] = sub_name
        
        # Salvataggio finale
        new_prod = {
            "ean": state['ean'], "name": state['name'], "price": state['price'],
            "category": state['category'], "brand": state['brand'],
            "image_url": state['image_url'], "info": state['info']
        }
        supabase.table('products').upsert(new_prod).execute()
        avvisa_github_per_foto(state['ean'], state['category'], state['brand'])
        
        await query.edit_message_text(f"✅ **SALVATO!**\n📦 {state['name']}\n📂 {CAT_MAP[state['category']]['n']} > {sub_name}\n💰 {state['price']}€\n\nL'AI sta preparando la foto... 🚀")
        del user_states[chat_id]

async def process_ean(ean, update):
    chat_id = update.effective_chat.id
    response = supabase.table('products').select('*').eq('ean', ean).execute()
    if response.data:
        p = response.data[0]
        user_states[chat_id] = {'existing_id': p['id'], 'step': 'waiting_price_update'}
        await update.effective_message.reply_text(f"🔄 **GIA' IN CATALOGO**\n🏷️ {p['name']}\n💰 Attuale: {p['price']}€\n\nInviami il **NUOVO PREZZO**:")
    else:
        data = fetch_off_data(ean)
        user_states[chat_id] = {
            'ean': ean, 'name': data['name'], 'image_url': data['image_url'], 
            'info': data['info'], 'step': 'waiting_price'
        }
        await update.effective_message.reply_text(f"📦 **NUOVO**: {data['name']}\n💰 Prezzo di vendita?")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    photo_file = await update.message.photo[-1].get_file()
    path = f"tmp_{chat_id}.jpg"
    await photo_file.download_to_drive(path)
    ean = detect_barcode(path)
    if ean: await process_ean(ean, update)
    else: await update.message.reply_text("❌ Codice non letto.")
    if os.path.exists(path): os.remove(path)

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("Il bot non può essere avviato senza TELEGRAM_TOKEN. Esce.")
        exit(1)
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("Bot attivo con menu pulsanti!")
    app.run_polling()

