# Round Robin Hood - Introduzione

**Version 0.9.5** | [Deutsch](../) | [English](../en/)

Round Robin Hood (RRH) distribuisce il surplus fotovoltaico misurato tra i dispositivi idonei secondo potenze nominali, profili e strategie. Il valore di controllo è la potenza istantanea di rete (W o kW), non il contatore cumulativo in kWh.

**Sicurezza:** RRH può comandare dispositivi reali. Non sostituisce protezioni elettriche o termiche indipendenti né un interruttore fisico di emergenza. Errori possono causare costi, surriscaldamento o incendi.

## Introduzione

- [Installazione e aggiornamenti](installation.md)
- [Configurazione](setup.md)
- [Dashboard](dashboard.md)
- [Dispositivi](consumers.md)
- [Profili e strategie](profiles.md)
- [Condizioni dei sensori](conditions.md)
- [Energia e costi](energy.md)
- [Impostazioni](settings.md)
- [Sensori Home Assistant](sensors.md)
- [Comportamento al riavvio](startup.md)
- [Risoluzione dei problemi](troubleshooting.md)
- [Sicurezza](safety.md)
- [Domande frequenti](faq.md)
- [Glossario](glossary.md)
- [Informazioni](about.md)


## Novità della versione 0.9.5

- Selezione delle entità Home Assistant con ricerca nelle impostazioni, nella procedura guidata, nei dispositivi, nelle condizioni e nelle fonti energetiche, anche da smartphone.
- Programmazioni settimanali facoltative per profili e dispositivi, con giorni selezionabili, più fasce e intervalli oltre la mezzanotte.
- Devono essere valide le condizioni dei sensori ed entrambe le programmazioni. Alla fine della fascia, RRH spegne i dispositivi che controlla, anche prima del termine del tempo minimo.
- La configurazione resta invariata e gli orari sono inizialmente disattivati. Effettuare il backup completo di HA, inclusa .storage, prima di aggiornare.
