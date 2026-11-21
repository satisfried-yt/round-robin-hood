# Installazione e aggiornamenti

Prima di un aggiornamento usa **Spegni tutto** e verifica fisicamente che i dispositivi siano spenti. La pausa non interrompe l’alimentazione. Esegui un backup completo di Home Assistant, inclusa la cartella `.storage`.

Per la prima installazione copia `custom_components/round_robin_hood` in `/config/custom_components/`, riavvia Home Assistant Core e aggiungi l’integrazione da **Impostazioni > Dispositivi e servizi**. La configurazione prosegue dal pannello laterale.

Per aggiornare da **0.9.2**, usa le istruzioni in `docs/UPDATE_0.9.3.md`. Per tornare alla versione precedente ripristina **insieme** il codice e il file RRH `.storage` corrispondente, solo con HA Core fermo. I dati creati dopo il backup andranno perduti.

---

[Introduzione](index.md) | [Sicurezza](safety.md)
