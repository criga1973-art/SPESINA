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

    console.log(`📨 [MAIL ENGINE] Tipo: ${type} | Destinatario: ${email} | Nome: ${name}`);

    let subject, html, from;

    if (type === 'RECEIPT') {
      from = 'Spesina <ricevute@spesina.it>'
      subject = `🧾 La tua ricevuta Spesina - Grazie ${name}!`
      
      let itemsHtml = "";
      if (Array.isArray(body.items)) {
        itemsHtml = body.items.map(i => `
          <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
              <div style="display: flex; align-items: center;">
                <img src="${i.img || 'https://spesina.it/img/placeholder.png'}" alt="${i.n}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 10px; margin-right: 12px; border: 1px solid #f1f5f9;">
                <div>
                  <div style="font-weight: 700; font-size: 14px; color: #1e293b;">${i.q}x ${i.n}</div>
                  <div style="font-size: 12px; color: #64748b;">${i.l || i.size || ''}</div>
                </div>
              </div>
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; text-align: right; font-weight: 700; color: #1e293b;">
              ${(i.p * i.q).toFixed(2)}€
            </td>
          </tr>
        `).join("");
      }

      html = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;800&display=swap');
          </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
          <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 40px 20px;">
            <tr>
              <td align="center">
                <!-- Main Card -->
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
                  
                  <!-- Header with Logo -->
                  <tr>
                    <td style="padding: 40px 40px 20px 40px; text-align: center;">
                      <div style="color: #2d1b4d; font-size: 32px; font-weight: 800; letter-spacing: -1px; margin-bottom: 10px;">
                        Spes<span style="color: #42d3a5;">i</span>na
                      </div>
                      <div style="width: 40px; height: 4px; background: #42d3a5; margin: 0 auto; border-radius: 2px;"></div>
                    </td>
                  </tr>

                  <!-- Hero Message -->
                  <tr>
                    <td style="padding: 20px 40px 30px 40px; text-align: center;">
                      <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: #1e293b; line-height: 1.2;">Grazie ${name}! <br><span style="color: #42d3a5;">La tua spesa è a casa.</span></h1>
                      <p style="margin: 15px 0 0 0; font-size: 16px; color: #64748b; line-height: 1.5;">Speriamo che i prodotti selezionati oggi ti piacciano. Ecco il riepilogo della tua consegna.</p>
                    </td>
                  </tr>

                  <!-- Payment Box -->
                  <tr>
                    <td style="padding: 0 40px 30px 40px;">
                      <div style="background: linear-gradient(135deg, #42d3a5, #10b981); padding: 25px; border-radius: 20px; text-align: center; color: #ffffff;">
                        <div style="font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Pagamento Ricevuto</div>
                        <div style="font-size: 36px; font-weight: 800; margin-top: 5px;">${body.total}€</div>
                      </div>
                    </td>
                  </tr>

                  <!-- Order Details -->
                  <tr>
                    <td style="padding: 0 40px 20px 40px;">
                      <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background: #f8fafc; border-radius: 16px; padding: 20px;">
                        <tr>
                          <td style="padding-bottom: 10px;">
                            <div style="font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Indirizzo Consegna</div>
                            <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-top: 4px;">${body.address}</div>
                          </td>
                        </tr>
                        <tr>
                          <td>
                            <div style="font-size: 11px; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Data e Ora</div>
                            <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-top: 4px;">${body.delivery}</div>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>

                  <!-- Items Table -->
                  <tr>
                    <td style="padding: 20px 40px 40px 40px;">
                      <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 800; color: #1e293b;">Riepilogo Prodotti</h4>
                      <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        ${itemsHtml}
                      </table>
                    </td>
                  </tr>

                  <!-- Footer -->
                  <tr>
                    <td style="padding: 30px 40px; background-color: #f1f5f9; text-align: center;">
                      <p style="margin: 0; font-size: 14px; font-weight: 700; color: #1e293b;">Hai domande sul tuo ordine?</p>
                      <p style="margin: 5px 0 0 0; font-size: 13px; color: #64748b;">Rispondi a questa email o chiamaci al +39 041 XXX XXXX</p>
                      <div style="margin-top: 20px; font-size: 12px; color: #94a3b8; font-weight: 500;">
                        Spesina S.r.l. - Mestre (VE)<br>
                        La spesa intelligente, veloce e sostenibile.
                      </div>
                    </td>
                  </tr>

                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
      `
    } else if (type === 'order') {
      from = 'Spesina <ordini@spesina.it>'
      subject = `📦 Conferma Ordine Spesina - ${body.delivery}`
      
      // Costruzione righe prodotti (Supporta sia stringa che array per retrocompatibilità)
      let itemsHtml = "";
      if (Array.isArray(body.items)) {
        itemsHtml = body.items.map(i => `
          <div style="display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #eee;">
            <img src="${i.image_url || i.img || ''}" alt="${i.name || i.n}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; margin-right: 15px;">
            <div style="flex: 1;">
              <div style="font-weight: bold; font-size: 14px; color: #0f172a;">${i.name || i.n}</div>
              <div style="font-weight: bold; font-size: 14px; color: #0f172a;">Quantità: ${i.quantity || i.q} ${i.size || i.l ? '(' + (i.size || i.l) + ')' : ''}</div>
              <div style="font-size: 11px; color: #64748b;">EAN: ${i.ean || 'N/A'}</div>
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
