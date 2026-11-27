# Profili e strategie

Tutti i profili condividono un budget di potenza; la **priorità** determina l’ordine di assegnazione. Ogni profilo ha partecipanti, strategia e opzioni proprie. Le condizioni dei sensori possono impedire l’attivazione dell’intero profilo.

Le otto strategie sono descritte qui sotto. A seconda della scelta, puoi impostare salti dei dispositivi che non entrano nel budget, finestre temporali, rotazioni, miglioramento minimo e intervallo di ottimizzazione.

## Profili e strategie

- Round Robin classico: turnazione dei dispositivi idonei.
- Tempo equo: meno tempo confermato, maggiore priorità.
- Energia equa: meno Wh stimati ricevuti, maggiore priorità.
- Priorità fissa: prevale l’ordine configurato.
- Massima efficienza: cerca una combinazione che sfrutta più surplus.
- Potenza crescente: dispositivi più piccoli prima.
- Potenza decrescente: dispositivi più grandi prima.
- Funzionamento stabile: evita commutazioni non necessarie.

---

[Introduzione](index.md) | [Sicurezza](safety.md)


## Programmazione settimanale dei profili (dalla 0.9.5)

In Profili → Modifica è possibile attivare una programmazione indipendente per ogni profilo. Ogni fascia include giorni selezionabili, inizio, fine e più intervalli nello stesso giorno.

Le programmazioni di profilo e dispositivo sono indipendenti. Per avviare servono profilo attivo, entrambe le fasce consentite e condizioni dei sensori valide. La strategia seleziona poi il carico idoneo.

Quando la fascia del profilo termina, RRH richiede lo spegnimento confermato dei dispositivi attivi che gestisce; più dispositivi possono essere spenti con il comando di gruppo. Non assume il controllo di dispositivi accesi esternamente.

Le fasce oltre mezzanotte appartengono al giorno iniziale. Si utilizza il fuso di Home Assistant, inclusi i cambi d'ora. Il pannello mostra la prossima apertura.
