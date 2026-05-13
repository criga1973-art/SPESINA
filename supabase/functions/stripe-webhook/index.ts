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

      const metadata = session.metadata
      const clientId = metadata?.client_id
      const name = metadata?.name
      const phone = metadata?.phone
      const delivery = metadata?.delivery
      const address = metadata?.address
      const itemsStr = metadata?.items
      
      let items = []
      if (itemsStr) {
        try {
          items = JSON.parse(itemsStr)
        } catch (e) {
          console.error("Errore parsing items da metadata:", e)
        }
      }

      // Ricostruiamo l'oggetto order_data
      const orderData = {
        order_id: parseInt(orderId),
        name: name,
        phone: phone,
        email: session.customer_email || '',
        items: items,
        total: (session.amount_total / 100).toFixed(2),
        delivery_date: delivery ? delivery.split(' ').slice(1, 4).join(' ') : '',
        delivery_slot: delivery ? delivery.split(' ').pop() : '',
        delivery: delivery,
        address: address,
        status: 'ricevuto',
        payment_method: 'stripe'
      }

      const { error: insertError } = await supabase
        .from('orders')
        .insert([{
          client_id: clientId,
          order_date: new Date().toISOString().split('T')[0],
          order_number: orderId,
          order_data: orderData
        }])

      if (insertError) {
        console.error(`Errore inserimento ordine ${orderId}:`, insertError);
        return new Response("Failed to insert order", { status: 500 })
      }

      console.log(`Ordine ${orderId} inserito con successo`);

      // Invio email via send-welcome
      try {
        await supabase.functions.invoke('send-welcome', {
          body: {
            type: 'order',
            email: session.customer_email || '',
            name: name,
            orderId: parseInt(orderId),
            total: (session.amount_total / 100).toFixed(2),
            address: address,
            delivery: delivery,
            items: items
          }
        })
        console.log("Mail inviata con successo da webhook")
      } catch (e) {
        console.error("Errore chiamata send-welcome da webhook:", e)
      }
    }
  }

  return new Response(JSON.stringify({ received: true }), { 
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  })
})
