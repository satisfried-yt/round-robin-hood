# Condizioni dei sensori

Le condizioni usano un sensore numerico HA, un confronto (`<`, `<=`, `>`, `>=`), una soglia e **isteresi**. Con **TUTTE** e **ALMENO UNA** puoi combinare condizioni di profilo o dispositivo.

Un sensore `unknown` o `unavailable` non autorizza nuovi avvii. Una condizione di temperatura software non sostituisce un limitatore termico indipendente.

---

[Introduzione](index.md) | [Sicurezza](safety.md)


## Combinare condizioni dei sensori e programmazioni (0.9.5)

Le condizioni numeriche e gli orari settimanali si attivano separatamente. Le regole dei sensori conservano AND/OR; la programmazione è sempre un'ulteriore condizione AND.

Un dispositivo si avvia solo con profilo attivo, programmazione del profilo consentita, programmazione individuale consentita e condizioni numeriche valide.

Un sensore non valido impedisce l'avvio. Alla fine di una fascia, RRH spegne i dispositivi che gestisce senza attendere il tempo minimo. Queste regole non sostituiscono le protezioni indipendenti.

Cercare le entità numeriche nel selettore Home Assistant. Configurare le fasce negli editor di profili e dispositivi.
