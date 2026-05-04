-- 1. Creiamo la sequenza che parte da 1
CREATE SEQUENCE IF NOT EXISTS customer_id_seq START 1;

-- 2. Creiamo una funzione che possiamo chiamare dalla Edge Function per ottenere il prossimo ID
CREATE OR REPLACE FUNCTION generate_customer_id()
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER -- Permette di eseguirla anche da ruoli con meno permessi
AS $$
DECLARE
  next_num integer;
  formatted_id text;
BEGIN
  -- Ottiene il prossimo numero (es: 1, 2, 3...)
  next_num := nextval('customer_id_seq');
  
  -- Formatta il numero aggiungendo gli zeri (es: SP-0001)
  -- LPAD(testo, lunghezza_totale, carattere_riempimento)
  formatted_id := 'SP-' || LPAD(next_num::text, 4, '0');
  
  RETURN formatted_id;
END;
$$;
