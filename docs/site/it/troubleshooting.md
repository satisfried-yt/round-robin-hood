# Risoluzione dei problemi

Se RRH non riparte, controlla il modo di avvio, il sensore di rete (segno, unità, aggiornamento), gli stati dei dispositivi e i **log di Home Assistant**. Un attuatore non disponibile può bloccare il riavvio automatico.

Se nessun carico parte, verifica il surplus disponibile, la riserva, i profili, le condizioni e i timer. Se un sensore tariffario non appare, controlla l’unità. Dopo un errore di aggiornamento non ripetere senza verificare l’output: segui le istruzioni di ripristino.

---

[Introduzione](index.md) | [Sicurezza](safety.md)


## Risoluzione dei problemi: orari e ricerca (0.9.5)

Nessun avvio con surplus: controllare lo stato di profilo e dispositivo. Entrambe le programmazioni e i sensori devono autorizzare. Verificare anche misuratore, riserva, watt e blocco di riavvio.

Ora o giorno inatteso: controllare il fuso di Home Assistant. Le fasce notturne appartengono al giorno iniziale. Il cambio d'ora può saltare o ripetere ore locali.

Entità assente: verificare entità, dominio e unità compatibili. I riferimenti precedenti vengono conservati quando possibile. Se si vede la vecchia interfaccia, aggiornare la cache e riavviare HA.

Se manca la conferma di spegnimento, verificare l'attuatore e i registri HA. RRH non è un interruttore di emergenza.
