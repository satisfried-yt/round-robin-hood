# Dispositivi

Definisci **nome**, **icona**, **entità HA di controllo** e **potenza nominale (W)** per ogni dispositivo. Non usare la stessa entità in più dispositivi RRH. Le schede mostrano stato confermato, partecipazione e motivi di attesa.

Tipi: **interruttore**, **multilivello** o **regolazione continua**. Imposta le potenze per livello e la corretta azione di spegnimento. Verifica che il valore `0` di un’entità `number` spenga davvero il dispositivo. Tempi minimi e blocchi di riavvio limitano le commutazioni rapide.

Rimuovere un dispositivo da RRH non elimina l’entità Home Assistant.

---

[Introduzione](index.md) | [Sicurezza](safety.md)


## Nuovo in 0.9.5: ricerca e orari dei dispositivi

In Dispositivi → Modifica, selezionare entità di comando e livelli mediante il selettore Home Assistant con ricerca per nome o ID. Le associazioni esistenti restano valide.

Attivare la programmazione soltanto se serve. Aggiungere più fasce, scegliere i giorni lun–dom e inserire inizio e fine (HH:MM). Una programmazione disattivata non limita il funzionamento.

Per lunedì 22:00–martedì 02:00 selezionare lunedì come giorno di inizio. L'ora finale è esclusa. Più fasce sono in OR; anche programmazione del profilo e condizioni dei sensori devono essere soddisfatte (AND).

Alla fine della fascia RRH spegne i dispositivi attivi gestiti anche se il tempo minimo rigoroso non è terminato. Non sostituisce le protezioni elettriche o termiche indipendenti. Il prossimo inizio usa il fuso HA.
