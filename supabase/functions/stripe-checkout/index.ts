import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Gestione preflight CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const body = await req.json()
    const { orderId, total, email, successUrl, cancelUrl, orderData } = body

    // Recupera la chiave segreta di Stripe dalle variabili d'ambiente di Supabase
    const stripeSecretKey = Deno.env.get('STRIPE_SECRET_KEY')
    if (!stripeSecretKey) {
      throw new Error("La variabile d'ambiente STRIPE_SECRET_KEY non è impostata su Supabase!")
    }

    if (!orderId || !total) {
      throw new Error("Mancano i dati obbligatori: orderId e total.")
    }

    // Calcoliamo il totale in centesimi per Stripe
    const amountInCents = Math.round(parseFloat(total) * 100)

    // Prepariamo i parametri per l'API di Stripe
    const params = new URLSearchParams()
    params.append('mode', 'payment')
    
    // Usiamo gli URL passati dal frontend, oppure quelli di default se mancano
    params.append('success_url', successUrl || `https://spesina.it/?success=true&order_id=${orderId}`)
    params.append('cancel_url', cancelUrl || `https://spesina.it/?canceled=true`)
    
    params.append('client_reference_id', orderId)
    
    if (email) {
      params.append('customer_email', email)
    }

    // Aggiungiamo i dati dell'ordine nei metadati se presenti
    if (orderData) {
      params.append('metadata[client_id]', orderData.client_id || '')
      params.append('metadata[name]', orderData.name || '')
      params.append('metadata[phone]', orderData.phone || '')
      params.append('metadata[delivery]', orderData.delivery || '')
      params.append('metadata[address]', orderData.address || '')
      
      const simplifiedItems = orderData.items.map((i: any) => ({
        ean: i.ean,
        n: i.n,
        q: i.q,
        p: i.p
      }))
      params.append('metadata[items]', JSON.stringify(simplifiedItems))
    }

    // Creiamo un singolo elemento che rappresenta l'intera spesa
    params.append('line_items[0][price_data][currency]', 'eur')
    params.append('line_items[0][price_data][product_data][name]', `Ordine #${orderId} su Spesina`)
    params.append('line_items[0][price_data][unit_amount]', amountInCents.toString())
    params.append('line_items[0][quantity]', '1')

    console.log(`Creazione sessione Stripe per ordine ${orderId}. Success URL: ${successUrl}`);

    // Chiamata diretta all'API di Stripe
    const res = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${stripeSecretKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString()
    })

    const stripeSession = await res.json()

    if (!res.ok) {
      console.error("Errore Stripe API:", stripeSession);
      throw new Error(stripeSession.error?.message || "Errore nella creazione della sessione Stripe")
    }

    // Restituiamo l'URL della pagina di pagamento creata da Stripe
    return new Response(JSON.stringify({ url: stripeSession.url }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error("Errore Edge Function:", error.message);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
