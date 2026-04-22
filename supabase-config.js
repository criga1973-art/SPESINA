// Configurazione del client Supabase per Spesina
const SUPABASE_URL = "https://uldpnhmdjbbwwqwjsdoh.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_ZYES3YYmpypE-NGYZ6RC-Q_N3XfcRyJ";

// Inizializzazione del client
const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Nota: Assicurati di caricare lo script di supabase via CDN prima di questo file:
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
