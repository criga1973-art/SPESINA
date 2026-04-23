import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const RESEND_API_KEY = "re_fQUPt4TL_JxoJLoLjtzyD6ZKdezXoeAaM"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Gestione CORS per chiamate dal browser
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { name, email, clientId, address, phone, subExpiry } = await req.json()

    console.log(`Invio email a ${email} per il cliente ${clientId}`)

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({
        from: 'Spesina <benvenuto@spesina.it>',
        to: [email],
        subject: `🎉 Benvenuto in Spesina, ${name}!`,
        html: `
          <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 15px;">
            <h1 style="color: #10b981; text-align: center;">Benvenuto in Spesina!</h1>
            <p>Ciao <b>${name}</b>, la tua registrazione è stata completata con successo.</p>
            <div style="background: #f9fafb; padding: 20px; border-radius: 10px; border: 1px solid #e5e7eb;">
              <p style="margin: 5px 0;">🆔 <b>ID CLIENTE:</b> <span style="font-family: monospace; font-size: 18px; color: #0f172a;">${clientId}</span></p>
              <p style="margin: 5px 0;">📍 <b>Indirizzo:</b> ${address}</p>
              <p style="margin: 5px 0;">📞 <b>Telefono:</b> ${phone}</p>
              <p style="margin: 5px 0;">📅 <b>Scadenza Abbonamento:</b> ${subExpiry}</p>
            </div>
            <p style="margin-top: 20px;">Usa il tuo ID per accedere da qualsiasi dispositivo e iniziare a fare la spesa!</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #6b7280; text-align: center;">Spesina S.r.l. - Mestre (VE)</p>
          </div>
        `,
      }),
    })

    const data = await res.json()
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
