# Installazione e aggiornamenti

Prima di un aggiornamento usa **Spegni tutto** e verifica fisicamente che i dispositivi siano spenti. La pausa non interrompe l’alimentazione. Esegui un backup completo di Home Assistant, inclusa la cartella `.storage`.

Per la prima installazione copia `custom_components/round_robin_hood` in `/config/custom_components/`, riavvia Home Assistant Core e aggiungi l’integrazione da **Impostazioni > Dispositivi e servizi**. La configurazione prosegue dal pannello laterale.

Per aggiornare da **0.9.4**, usa le istruzioni in `docs/UPDATE_0.9.5.md`. Per tornare alla versione precedente ripristina **insieme** il codice e il file RRH `.storage` corrispondente, solo con HA Core fermo. I dati creati dopo il backup andranno perduti.

---

[Introduzione](index.md) | [Sicurezza](safety.md)


## Aggiornamento da 0.9.4 a 0.9.5

- Eseguire Spegni tutto in RRH e verificare ogni attuatore. La pausa non spegne i carichi.
- Creare un backup completo di Home Assistant, inclusa /config/.storage. Se necessario, scegliere Sempre spento per evitare l'avvio automatico durante l'aggiornamento.
- Installare v0.9.5 tramite HACS/Marketplace o il pacchetto ufficiale GitHub. Manualmente sostituire solo custom_components/round_robin_hood. Consultare docs/UPDATE_0.9.5.md per i passaggi e il ripristino.
- Riavviare HA Core e verificare dispositivi, profili, condizioni, statistiche, ricerca delle entità e nuovi orari.
- I nuovi orari sono disattivati all'inizio. Per tornare indietro, ripristinare insieme codice e .storage con HA Core arrestato.
