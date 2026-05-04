import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const RESEND_API_KEY = "re_fQUPt4TL_JxoJLoLjtzyD6ZKdezXoeAaM"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Gestione CORS preflight request
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const payload = await req.json()
    console.log("📦 Webhook Payload Ricevuto:", JSON.stringify(payload));
    
    const { user, email_data } = payload

    // 1. Controlliamo se è un evento di Signup (Registrazione)
    if (!email_data || email_data.email_action_type !== 'signup') {
      console.log("⚠️ Ignorato: Non è una mail di registrazione.");
      return new Response(JSON.stringify({ message: "Ignorato: non è signup" }), { 
        status: 200, headers: corsHeaders 
      })
    }

    // 2. Inizializziamo Supabase con privilegi di Amministratore (Service Role)
    // Questo ci permette di generare l'ID e aggiornare l'utente
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 3. Generiamo il Customer ID usando la funzione SQL che hai appena eseguito
    const { data: customerId, error: rpcError } = await supabaseAdmin.rpc('generate_customer_id')
    
    if (rpcError) {
      console.error("❌ Errore nella generazione ID Cliente:", rpcError);
      throw new Error("Impossibile generare l'ID Cliente");
    }

    console.log(`✅ ID Cliente generato: ${customerId}`);

    // 4. Aggiorniamo i metadati dell'utente con l'ID appena generato
    const { error: updateError } = await supabaseAdmin.auth.admin.updateUserById(user.id, {
      user_metadata: { customer_id: customerId }
    })

    if (updateError) {
      console.error("❌ Errore nell'aggiornamento utente:", updateError);
    }

    // 5. Costruiamo il Link di Conferma nativo di Supabase
    // Format: site_url/auth/v1/verify?token=...&type=signup&redirect_to=...
    const siteUrl = email_data.site_url || "https://spesina.it"
    const confirmationLink = `${siteUrl}/auth/v1/verify?token=${email_data.token_hash}&type=${email_data.email_action_type}&redirect_to=${encodeURIComponent(email_data.redirect_to || siteUrl)}`

    // 6. Prepariamo la mail HTML da inviare
    const html = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 12px; padding: 25px; color: #1e293b;">
        <div style="text-align: center; margin-bottom: 20px;">
          <h2 style="color: #10b981; margin: 0;">Benvenuto in Spesina! 🛒</h2>
          <p style="color: #64748b; font-size: 16px;">Il tuo account è quasi pronto.</p>
        </div>
        
        <p style="font-size: 15px; line-height: 1.5;">Grazie per esserti registrato. Abbiamo creato il tuo <b>Codice Cliente</b>, che potrai usare per tutte le tue operazioni:</p>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; margin: 25px 0; border: 1px dashed #cbd5e1;">
          <span style="font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Il tuo ID Cliente</span><br>
          <strong style="font-size: 32px; color: #10b981; letter-spacing: 2px;">${customerId}</strong>
        </div>
        
        <p style="font-size: 15px; text-align: center; margin-bottom: 25px;">Per attivare definitivamente il tuo account e fare la tua prima spesa, clicca sul pulsante qui sotto:</p>
        
        <div style="text-align: center;">
          <a href="${confirmationLink}" style="display: inline-block; background-color: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2);">
            Conferma il tuo Account
          </a>
        </div>
        
        <p style="margin-top: 40px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 20px;">
          Se non hai richiesto tu questa registrazione, ignora questa email.<br>
          Spesina - La tua spesa intelligente a Mestre
        </p>
      </div>
    `

    // 7. Invio tramite Resend
    console.log("✉️ Invio mail di conferma a:", user.email);
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({ 
        from: 'Spesina <ordini@spesina.it>', 
        to: [user.email], 
        subject: 'Benvenuto su Spesina! Conferma la tua registrazione', 
        html 
      }),
    });

    const resendData = await res.json()
    
    if (!res.ok) {
      throw new Error(`Errore Resend: ${JSON.stringify(resendData)}`)
    }

    console.log("✅ Mail inviata con successo!");
    return new Response(JSON.stringify({ message: "Email sent successfully", data: resendData }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error) {
    console.error("❌ Errore generale Edge Function:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 500,
    })
  }
})
