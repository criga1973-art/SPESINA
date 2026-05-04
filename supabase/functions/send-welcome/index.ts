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
    console.log("📦 Body ricevuto:", JSON.stringify(body));

    const type = body.type || 'welcome'
    const email = (body.email || body.e || "").trim()
    const name = body.name || body.n || body.full_name || 'Cliente'
    const orderId = body.orderId || 'N/A'
    const total = body.total || '0.00'
    const address = body.address || 'N/A'
    const delivery = body.delivery || 'N/A'

    if (!email || !email.includes('@')) {
      throw new Error(`Email non valida: ${email}`);
    }

    let subject = "";
    let html = "";
    const from = 'Spesina <ordini@spesina.it>';

    // Funzione helper per generare la lista prodotti in formato tabella (più compatibile)
    const generateItemsTable = (items) => {
      if (!Array.isArray(items)) return "<tr><td>Nessun prodotto in elenco</td></tr>";
      return items.map(i => `
        <tr>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; width: 60px;">
            <img src="${i.img || i.image || 'https://uldpnhmdjbbwwqwjsdoh.supabase.co/storage/v1/object/public/products/placeholder.png'}" 
                 width="50" height="50" 
                 style="border-radius:8px; object-fit:contain; background:#f8fafc; border:1px solid #eee;">
          </td>
          <td style="padding: 10px 10px; border-bottom: 1px solid #f1f5f9;">
            <div style="font-size: 14px; font-weight: 700; color: #1e293b;">${i.q || 1}x ${i.n || i.name}</div>
            <div style="font-size: 12px; color: #64748b;">${i.l || i.size || ''}</div>
          </td>
          <td style="padding: 10px 0; border-bottom: 1px solid #f1f5f9; text-align: right; font-weight: 800; color: #1e293b; width: 80px;">
            ${((i.p || 0) * (i.q || 1)).toFixed(2)}€
          </td>
        </tr>
      `).join("");
    };

    if (type === 'RECEIPT') {
      subject = `🧾 Ricevuta Ordine #${orderId} - Grazie ${name}!`
      html = `
        <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; border-radius:15px; padding:25px; color:#1e293b;">
          <h2 style="color:#10b981; margin-top:0;">Grazie per il tuo ordine, ${name}!</h2>
          <p>L'ordine <b>#${orderId}</b> è stato consegnato correttamente.</p>
          <div style="background:#f8fafc; padding:20px; border-radius:12px; margin:20px 0;">
            <p style="margin:0 0 10px 0;">📍 <b>Consegna:</b> ${address}</p>
            <p style="margin:0;">💰 <b>Totale:</b> <span style="font-size:18px; font-weight:800; color:#10b981;">${total}${total.includes('€') ? '' : '€'}</span></p>
          </div>
          <table width="100%" style="border-collapse:collapse; margin-top:20px;">
            ${generateItemsTable(body.items)}
          </table>
          <p style="text-align:center; color:#94a3b8; font-size:12px; margin-top:30px;">Spesina - La tua spesa intelligente a Mestre</p>
        </div>`;
    } else if (type === 'order') {
      subject = `📦 Conferma Ordine #${orderId} - Spesina`
      html = `
        <div style="font-family:sans-serif; max-width:600px; margin:auto; border:1px solid #eee; border-radius:15px; padding:25px; color:#1e293b;">
          <div style="text-align:center; margin-bottom:20px;">
            <h2 style="color:#10b981; margin:10px 0;">Ordine #${orderId} Ricevuto!</h2>
            <p style="color:#64748b;">Ciao ${name}, abbiamo preso in carico la tua spesa.</p>
          </div>
          <div style="background:#f8fafc; padding:20px; border-radius:12px; border:1px solid #f1f5f9; margin-bottom:25px;">
            <p style="margin:0 0 8px 0;">🚚 <b>Consegna:</b> ${delivery}</p>
            <p style="margin:0;">📍 <b>Indirizzo:</b> ${address}</p>
          </div>
          <table width="100%" style="border-collapse:collapse;">
            ${generateItemsTable(body.items)}
          </table>
          <div style="text-align:right; margin-top:20px; padding-top:15px; border-top:2px solid #10b981;">
            <span style="color:#64748b; font-size:14px;">Totale Ordine:</span><br>
            <span style="font-size:24px; font-weight:900; color:#1e293b;">${total}${total.includes('€') ? '' : '€'}</span>
          </div>
          <p style="text-align:center; color:#94a3b8; font-size:12px; margin-top:40px;">Spesina - Mestre</p>
        </div>`;
    } else {
      subject = body.subject || `Benvenuto su Spesina! Il tuo Account è attivo`
      const cId = body.clientId || 'N/A';
      html = body.html || `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 12px; padding: 25px; color: #1e293b;">
          <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #10b981; margin: 0;">Benvenuto in Spesina! 🛒</h2>
            <p style="color: #64748b; font-size: 16px;">Il tuo account è attivo e pronto.</p>
          </div>
          
          <p style="font-size: 15px; line-height: 1.5;">Ciao <b>${name}</b>, grazie per esserti registrato. Abbiamo creato il tuo <b>Codice Cliente</b> univoco, da usare per le tue spese:</p>
          
          <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; margin: 25px 0; border: 1px dashed #cbd5e1;">
            <span style="font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Il tuo ID Cliente</span><br>
            <strong style="font-size: 32px; color: #10b981; letter-spacing: 2px;">${cId}</strong>
          </div>
          
          <p style="font-size: 15px; text-align: center; margin-bottom: 25px;">Puoi subito iniziare a esplorare i nostri prodotti!</p>
          
          <div style="text-align: center;">
            <a href="https://spesina.it" style="display: inline-block; background-color: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
              Fai la tua prima spesa
            </a>
          </div>
          
          <p style="margin-top: 40px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 20px;">
            Spesina - La tua spesa intelligente a Mestre
          </p>
        </div>
      `;
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
        bcc: ['ordini@spesina.it'], 
        subject, 
        html 
      }),
    });

    return new Response(JSON.stringify(await res.json()), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
})
