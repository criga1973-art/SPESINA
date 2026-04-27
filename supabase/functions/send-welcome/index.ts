import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const RESEND_API_KEY = "re_fQUPt4TL_JxoJLoLjtzyD6ZKdezXoeAaM"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const body = await req.json()
    const type = body.type || 'welcome' 
    const name = body.name || body.full_name
    const email = body.email
    const clientId = body.clientId || body.client_id

    let subject, html, from;

    if (type === 'order') {
      from = 'Spesina <ordini@spesina.it>'
      subject = `📦 Conferma Ordine Spesina - ${body.delivery}`
      
      // Costruzione righe prodotti (Supporta sia stringa che array per retrocompatibilità)
      let itemsHtml = "";
      if (Array.isArray(body.items)) {
        itemsHtml = body.items.map(i => `
          <div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee;">
            <img src="${i.image_url || i.img || ''}" alt="${i.name || i.n}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; margin-right: 15px;">
            <div style="flex: 1;">
              <div style="font-weight: bold; font-size: 14px; color: #0f172a;">[${i.quantity || i.q}x] ${i.name || i.n}</div>
              <div style="font-size: 12px; color: #64748b;">EAN: ${i.ean || 'N/A'}</div>
            </div>
            <div style="font-weight: bold; color: #0f172a;">${((i.price || i.p) * (i.quantity || i.q)).toFixed(2)}€</div>
          </div>
        `).join("");
      } else {
        itemsHtml = `<pre style="white-space: pre-wrap; font-family: inherit; font-size: 14px;">${body.orderItems}</pre>`;
      }

      html = `
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 15px;">
          <h1 style="color: #10b981; text-align: center;">Ordine Ricevuto!</h1>
          <p>Ciao <b>${name}</b>, il tuo ordine è stato preso in carico.</p>
          <div style="background: #f9fafb; padding: 20px; border-radius: 10px; border: 1px solid #e5e7eb; margin-bottom: 20px;">
            <p style="margin: 5px 0;">🚚 <b>Consegna prevista:</b> ${body.delivery}</p>
            <p style="margin: 5px 0;">📍 <b>Indirizzo:</b> ${body.address}</p>
            <p style="margin: 5px 0;">📞 <b>Telefono:</b> ${body.phone || 'Non fornito'}</p>
          </div>
          <div style="background: #fff; padding: 15px; border: 1px solid #eee; border-radius: 10px;">
            <h4 style="margin: 0 0 10px 0;">Riepilogo Prodotti:</h4>
            ${itemsHtml}
            <hr style="border: 0; border-top: 1px solid #eee; margin: 15px 0;">
            <p style="text-align: right; font-weight: bold; font-size: 18px; margin: 0;">${body.total}</p>
          </div>
          <p style="margin-top: 20px; font-size: 14px; color: #64748b;">Grazie per aver scelto Spesina, la spesa intelligente a Mestre.</p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="font-size: 12px; color: #6b7280; text-align: center;">Spesina S.r.l. - Mestre (VE)</p>
        </div>
      `
    } else {
      from = 'Spesina <benvenuto@spesina.it>'
      subject = `🎉 Benvenuto in Spesina, ${name}!`
      html = `
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 15px;">
          <h1 style="color: #10b981; text-align: center;">Benvenuto in Spesina!</h1>
          <p>Ciao <b>${name}</b>, la tua registrazione è stata completata con successo.</p>
          <div style="background: #f9fafb; padding: 20px; border-radius: 10px; border: 1px solid #e5e7eb;">
            <p style="margin: 5px 0;">🆔 <b>ID CLIENTE:</b> <span style="font-family: monospace; font-size: 18px; color: #0f172a;">${clientId}</span></p>
            <p style="margin: 5px 0;">📅 <b>Scadenza Abbonamento:</b> ${body.subExpiry || body.sub_expiry}</p>
          </div>
          <p style="margin-top: 20px;">Usa il tuo ID per accedere da qualsiasi dispositivo e iniziare a fare la spesa!</p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
          <p style="font-size: 12px; color: #6b7280; text-align: center;">Spesina S.r.l. - Mestre (VE)</p>
        </div>
      `
    }

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_API_KEY}`,
      },
      body: JSON.stringify({ 
        from, 
        to: [email], 
        bcc: ['criga1973@gmail.com'], 
        subject, 
        html 
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
