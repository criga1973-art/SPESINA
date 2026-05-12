import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import Stripe from 'https://esm.sh/stripe@12.0.0?target=deno'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  // Gestione preflight CORS (se necessaria, ma i webhook di solito sono solo POST)
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: { 'Access-Control-Allow-Origin': '*' } })
  }

  const stripeSecretKey = Deno.env.get('STRIPE_SECRET_KEY')
  const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET')
  
  if (!stripeSecretKey || !webhookSecret) {
    console.error("Variabili d'ambiente mancanti: STRIPE_SECRET_KEY o STRIPE_WEBHOOK_SECRET");
    return new Response("Missing env vars", { status: 500 })
  }

  const stripe = new Stripe(stripeSecretKey, {
    apiVersion: '2022-11-15',
    httpClient: Stripe.createFetchHttpClient(),
  })

  const signature = req.headers.get('stripe-signature')
  if (!signature) {
    console.error("Firma Stripe mancante nell'header");
    return new Response("Missing signature", { status: 400 })
  }

  const body = await req.text()
  let event

  try {
    // Verifica che il messaggio arrivi davvero da Stripe
    event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret)
    console.log(`Evento ricevuto: ${event.type}`);
  } catch (err) {
    console.error(`Verifica firma fallita: ${err.message}`);
    return new Response(`Webhook Error: ${err.message}`, { status: 400 })
  }

  // Gestiamo solo l'evento di pagamento completato
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object
    const orderId = session.client_reference_id

    console.log(`Pagamento completato per sessione Stripe. OrderId: ${orderId}`);

    if (orderId) {
      const supabaseUrl = Deno.env.get('SUPABASE_URL')
      const supabaseServiceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
      
      const supabase = createClient(supabaseUrl, supabaseServiceRoleKey)

      // 1. Recupera l'ordine corrente
      const { data: order, error: fetchError } = await supabase
        .from('orders')
        .select('order_data')
        .eq('order_number', orderId)
        .single()

      if (fetchError || !order) {
        console.error(`Ordine non trovato su Supabase: ${orderId}`, fetchError);
        return new Response("Order not found", { status: 404 })
      }

      // 2. Aggiorna lo stato nel JSONB
      const updatedData = {
        ...order.order_data,
        status: 'ricevuto'
      }

      const { error: updateError } = await supabase
        .from('orders')
        .update({ order_data: updatedData })
        .eq('order_number', orderId)

      if (updateError) {
        console.error(`Errore aggiornamento ordine ${orderId}:`, updateError);
        return new Response("Failed to update order", { status: 500 })
      }

      console.log(`Ordine ${orderId} aggiornato con successo a 'ricevuto'`);
    }
  }

  return new Response(JSON.stringify({ received: true }), { 
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
})
