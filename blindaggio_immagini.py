import subprocess
import os

def blindatura():
    print("🚀 Avvio procedura di blindaggio immagini...")
    
    # 1. Controlla se la cartella img esiste
    if not os.path.exists("img"):
        print("❌ Cartella img non trovata!")
        return

    # 2. Aggiunge forzatamente tutto il contenuto di img a Git
    print("📦 Aggiunta immagini al tracciamento Git...")
    subprocess.run(["git", "add", "img/*"], capture_output=True)
    
    # 3. Commit
    print("🔒 Creazione lucchetto (Commit)...")
    result = subprocess.run(["git", "commit", "-m", "🔒 Blindaggio immagini: salvataggio forzato del catalogo"], capture_output=True, text=True)
    
    if "nothing to commit" in result.stdout:
        print("✅ Tutto è già al sicuro. Nessuna nuova immagine da blindare.")
    else:
        # 4. Push su GitHub
        print("☁️ Invio in cassaforte (GitHub Push)...")
        subprocess.run(["git", "push", "origin", "main"], capture_output=True)
        print("💎 IMMAGINI BLINDATE CON SUCCESSO!")

if __name__ == "__main__":
    blindatura()
