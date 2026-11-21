# Sensori Home Assistant

Il **sensore di rete** deve fornire potenza istantanea W/kW, non energia in kWh. Verifica il segno dell’immissione negli strumenti di Home Assistant.

I **prezzi** richiedono un valore numerico con unità di valuta per kWh compatibili (`EUR/kWh`, `ct/kWh`). Potenza FV: W/kW; energia FV: Wh/kWh/MWh. `unknown`, `unavailable` e valori non numerici non sono validi. Per il riavvio automatico serve una nuova misura, non solo un valore HA ripristinato.

---

[Introduzione](index.md) | [Sicurezza](safety.md)
