/* rrh-origin:20b099583abcb710ccdad5c7b3900433 */
/* Round Robin Hood. Native browser component with no external runtime dependencies. */
const DOMAIN = "round_robin_hood";
const STRATEGY_LABELS = {
  classic: "Klassischer Round Robin", fair_runtime: "Faire Laufzeitverteilung", fair_energy: "Faire Energieverteilung", fixed_priority: "Feste Priorität",
  maximum_efficiency: "Maximale Effizienz", power_asc: "Leistung aufsteigend",
  power_desc: "Leistung absteigend", stable_operation: "Stabiler Betrieb"
};
const STRATEGY_LABELS_EN = {
  classic: "Classic Round Robin", fair_runtime: "Fair Runtime", fair_energy: "Fair Energy Distribution", fixed_priority: "Fixed Priority",
  maximum_efficiency: "Maximum Efficiency", power_asc: "Power Ascending",
  power_desc: "Power Descending", stable_operation: "Stable Operation"
};
const STRATEGY_HELP_EN = {
  classic:"Round Robin: each eligible consumer takes a turn in sequence; insufficient power can stop the next turn (depending on skip policy).",
  fair_runtime:"Shortest confirmed runtime receives priority. Uses a configured time window, minimum difference and cooldown between rotations.",
  fair_energy:"Least estimated received PV energy has priority (nameplate watts × confirmed runtime). Rotations use an energy gap.",
  fixed_priority:"Always prefer consumers higher in the list; optionally skip those not fitting current available watts.",
  maximum_efficiency:"Select a combination that uses more available solar power; apply minimum gain, optimization interval and start margin.",
  power_asc:"Allocate smaller eligible consumers first; optional skip if they cannot fit.",
  power_desc:"Allocate larger eligible consumers first; optional skip if they cannot fit.",
  stable_operation:"Prefer stable running states and avoid unnecessary changes when supply fluctuates."
};
const ORDER_CHOICE_STRATEGIES = new Set(["classic", "fair_runtime", "fair_energy", "stable_operation"]);
const POWER_SKIP_STRATEGIES = new Set(["classic", "fair_runtime", "fair_energy", "fixed_priority", "power_asc", "power_desc"]);
const STRATEGY_HELP = {
  classic: "Zyklisch, mit wählbarem Überspringen bei Leistungsmangel.",
  fair_runtime: "Weniger Fair-Runtime-Betriebszeit zuerst; optional strikt oder mit Überspringen.",
  fair_energy: "Weniger zugeteilte PV-Energie zuerst; geschätzte kWh aus Nennleistung × bestätigter Laufzeit.",
  fixed_priority: "Feste Rangfolge; optional strikt oder mit Überspringen.",
  maximum_efficiency: "Beste Kombination; mit Mindestgewinn und Abstand zu Leistungsschwankungen.",
  power_asc: "Kleine Geräte zuerst; Strikt oder Überspringen wählbar.",
  power_desc: "Große Geräte zuerst; Strikt oder Überspringen wählbar.",
  stable_operation: "Bevorzugt laufende Geräte und vermeidet unnötige Wechsel."
};
const VERSION = "0.9.4";
const UI_EN = {
  dashboard:"Dashboard", consumers:"Consumers", profiles:"Profiles", energy:"Energy & costs", settings:"Settings", howto:"How-to", about:"About",
  page:"Page", on:"RRH ON", off:"All OFF", pause:"Pause",
  mode:"Operation", grid:"Grid power", budget:"Additional power available", candidate:"Next candidate",
  managed:"Estimated managed power", managedHelp:"Nominal power of running RRH-controlled loads, not a meter.",
  pipeline:"Current allocation order", pipelineNote:"Profiles appear in configured priority order.",
  add:"Add consumer", consumerHeader:"Consumers & order", consumerNote:"Assign and order consumers in Profiles. Edit while paused.",
  source:"Grid source", control:"Power & switching", fresh:"Data quality", save:"Save settings", reset:"Reload / discard",
  profileInfo:"Profiles & priority", profileBody:"Each profile has its own allocation strategy; higher-priority groups allocate first.",
  energyInfo:"Energy and cost reporting", energyBody:"Energy and cost estimates from confirmed RRH-controlled power.",
  note:"Explicit control authorization required",
  offNotice:"OFF sends one direct switch-off request for every configured RRH consumer, even if it was turned on manually. A missing confirmation is reported as an error. This is not a certified electrical emergency stop.",
  footer:"Classic groups · Priority · No overtaking · OFF switches off all configured RRH consumers",
  active:"Running", paused:"Paused", error:"Error pause", stopped:"Stopped",
  disabled:"No consumer", noSource:"No grid source selected", kw:"Nominal power", availability:"Participation",
  notReady:"Not yet available", powerLabel:"Power / draw", nextHeader:"Next candidate",
};
const UI_DE = {
  dashboard:"Dashboard", consumers:"Verbraucher", profiles:"Profile", energy:"Energie & Kosten", settings:"Einstellungen", howto:"Anleitung", about:"Über",
  page:"Seite", on:"RRH EIN", off:"Alle AUS", pause:"Pause",
  mode:"Betrieb", grid:"Netzleistung / Bezug", budget:"Zusätzlich verfügbar", candidate:"Nächster Kandidat",
  managed:"Geschätzte verwaltete Leistung", managedHelp:"Nennleistung der laufenden, RRH-gesteuerten Verbraucher; kein Messwert.",
  pipeline:"Aktuelle Vergabereihenfolge", pipelineNote:"Profile nach Priorität; jede Gruppe nutzt ihre gewählte Strategie.",
  add:"Verbraucher hinzufügen", consumerHeader:"Verbraucher & Reihenfolge", consumerNote:"Gruppenzuordnung unter Profile. Pfeile sortieren hier die Liste (im selben Profil auch die Vergabereihenfolge). Bearbeiten im pausierten Betrieb.",
  source:"Netzquelle", control:"Leistung & Schaltverhalten", fresh:"Datenqualität", save:"Einstellungen speichern", reset:"Neu laden / verwerfen",
  profileInfo:"Profile & Priorität", profileBody:"Gemeinsames Leistungsbudget; pro Profil eine eigene Strategie.",
  energyInfo:"Energie- und Kostenstatistik", energyBody:"Geschätzte Energie- und Kostenwerte aus bestätigter RRH-Leistung.",
  note:"Aktoren nur nach ausdrücklicher Freigabe",
  offNotice:"AUS sendet direkt einen Ausschaltauftrag an alle konfigurierten RRH-Verbraucher – auch an manuell eingeschaltete. Fehlende Bestätigungen werden als Fehler angezeigt. Kein zertifizierter elektrischer Not-Aus.",
  footer:"Profilprioritäten · Individuelle Strategien · AUS schaltet alle RRH-Verbraucher ab",
  active:"Aktiv", paused:"Pausiert", error:"Fehlerpause", stopped:"Gestoppt",
  disabled:"Kein Kandidat", noSource:"Keine Netzquelle ausgewählt", kw:"Nennleistung", availability:"Teilnahme",
  notReady:"Noch nicht verfügbar", powerLabel:"Netzfluss", nextHeader:"Nächster Kandidat",
};
const HELP = {
  de: {
    start: "Schaltet die Automatik ein.",
    pause: "Pausiert die Automatik. Laufende Verbraucher bleiben eingeschaltet; Fair-Laufzeit und Fair-Energie werden nicht weitergezählt.",
    off: "Fordert für alle konfigurierten RRH-Verbraucher sofort AUS an – unabhängig von Mindestlaufzeiten und Verzögerungen. Nicht erreichbar bedeutet: keine bestätigte Abschaltung. Kein zertifizierter Not-Aus.",
    grid: "Gemessene Netzeinspeisung bzw. Netzbezug. Laufende Geräte sind im Netzfluss bereits berücksichtigt.",
    budget: "Netzeinspeisung abzüglich Reserve: so viel Leistung ist zusätzlich verfügbar.",
    total: "Geschätztes Gesamtbudget: zusätzliche Leistung plus Nennleistung bereits laufender RRH-Verbraucher.",
    candidate: "Nächster auswählbarer Verbraucher gemäß der Strategie seines Profils.",
    managed: "Summe der Nennleistungen laufender RRH-Verbraucher, kein Messwert.",
    pipeline: "Profile nach Priorität. Reihenfolge und Abschaltungen hängen von der gewählten Strategie ab.",
    consumers: "Zuweisung unter Profile. Pfeile sortieren die Liste und innerhalb eines Profils die Vergabereihenfolge. Bearbeiten bei pausierter Automatik.",
    profiles: "Profile teilen sich ein Leistungsbudget. Höhere Priorität schaltet zuerst ein, niedrigere zuerst ab.",
    energy: "Energie- und Kostenwerte sind Schätzungen aus Netzfluss und bestätigter RRH-Leistung.",
    settings: "Einstellungen bei pausierter Automatik ändern und gemeinsam speichern.",
    gridSource: "Leistungssensor mit W oder kW verwenden, keinen Energiezähler mit kWh.",
    control: "Die globale Unterlastverzögerung gilt für Geräte ohne eigene Verzögerung. Sofort-AUS und Sensorbedingungen haben Vorrang. Bestätigungen sind standardmäßig aktiv.",
    freshness: "Nur neue Sensormeldungen zählen. Bei zu alten Netzdaten geht RRH in Fehlerpause; laufende Verbraucher bleiben unverändert.",
  },
  en: {
    start: "Start automatic allocation.",
    pause: "Pause allocation without switching running consumers off. Fair runtime and fair energy accounting also pause.",
    off: "Request immediate OFF for all configured RRH consumers, overriding runtime protection and delays. Unreachable devices cannot be confirmed off. Not a certified electrical emergency stop.",
    grid: "Measured grid export or import; running loads are already included in this value.",
    budget: "Grid export minus the reserve: additional power available for allocation.",
    total: "Estimated total budget: additional power plus nominal ratings of running RRH loads.",
    candidate: "Next available consumer based on its profile's scheduling strategy.",
    managed: "Sum of nominal ratings for RRH-controlled running loads, not a measured value.",
    pipeline: "Profiles appear in priority order with individual scheduling strategies.",
    consumers: "Assign consumers under Profiles. Arrows change list order and the sequence within a profile. Edit while paused.",
    profiles: "Profiles share a single power budget. High-priority profiles allocate first and shed last.",
    energy: "Energy/cost statistics are estimates derived from valid grid readings.",
    settings: "Pause before changing settings; save them together.",
    gridSource: "Use an instantaneous power sensor in W or kW, not an energy counter in kWh.",
    control: "Deficit delays apply to insufficient reserve; explicit OFF and conditions take precedence.",
    freshness: "Stale grid data pauses RRH with an error. Already-running loads are not automatically switched off.",
  },
};

const LOCALIZED_STATS = {
  de:{ energyInfo:"Energie & Kosten", energyBody:"Geschätzte Bilanz ausschließlich aus gültiger Netzmessung und bestätigten RRH-Verbrauchern.",
    overview:"Übersicht · seit Statistikbeginn", dayStats:"Tageswerte · zuletzt 45 Tage", deviceStats:"Verbraucher · Energie und Laufzeit", chartStats:"24-Stunden-Verlauf · Überschussnutzung (%)", dataCaveat:"Schätzwerte. Akku-Flüsse werden nicht separat bilanziert; Netzfluss kann durch einen Akku beeinflusst sein. Keine Rückrechnung vor Aktivierung der Statistik.",
    rate:"Netto-Vorteil jetzt", total_net:"Bisheriger Netto-Vorteil", total_energy:"Von RRH genutzter Überschuss", capture:"Überschuss-Nutzungsquote", live_chart:"Live-Effizienz", pv_power:"PV-Leistung", gross:"Wert der Eigennutzung", lost:"Entgangene Einspeisevergütung", captured:"Genutzte Energie", potential:"Erfasster Überschuss", exported:"Verbleibende Einspeisung", captureAvg:"Nutzungsquote gesamt", timeRunning:"Geräte-Betriebsstunden", moneyCoverage:"Mit gültigem Tarif bewertet", starts:"Starts", consumption:"Verbrauch (kWh)", durationLabel:"Laufzeit (h)",
    resetStats:"Gesamtstatistik zurücksetzen", resetStatsConfirm:"Gesamte RRH-Energie- und Kostenstatistik endgültig zurücksetzen? Fairness-Statistiken bleiben erhalten.", priceMissing:"Strompreis und Einspeisevergütung auf der Seite Energie & Kosten konfigurieren.",
    energySettings:"Energie & Kosten", dashboardSettings:"Dashboard-Anzeigen & Sprache", sourceMode:"Datenquelle", fixed:"Fester Wert", entity:"HA-Entität", pvSize:"PV-Anlagengröße (W)", importPrice:"Strompreis (€/kWh)", feedPrice:"Einspeisevergütung (€/kWh)", solarPower:"PV-Leistungssensor (W oder kW, optional)", solarEnergy:"PV-Energiezähler (kWh, optional)", gridExportEnergy:"Netzeinspeisezähler (kWh, optional)", chartType:"Live-Diagramm", language:"Sprache", automatic:"Automatisch (Home Assistant)", energyHelp:"Tarife wie im HA-Energie-Dashboard als Entität oder feste Zahl wählen. Geldwerte sind Netto-Vorteile gegenüber Einspeisung; keine Stromrechnung.", showCards:"Karten ein-/ausblenden", sensorWarning:"Quellen-Hinweise", unitsNotice:"PV-Anlagengröße in W, Tarife je kWh in ausgewählter Währung. Einheit und Wechselkurs nicht automatisch umrechnen.",
    chartGauge:"Effizienzbalken", chartLine:"Linie", chartBar:"Balken", chartArea:"Fläche", chartDonut:"Ring", chartStacked:"Gestapelt", chartSpark:"Sparkline", demo:"Demo-Modus", exitDemo:"Demo verlassen"},
  en:{energyInfo:"Energy & costs", energyBody:"Estimated totals from valid grid readings and confirmed RRH loads only.",overview:"Overview · since statistics started",dayStats:"Daily totals · last 45 days",deviceStats:"Consumers · energy and runtime",chartStats:"24-hour history · surplus utilization (%)",dataCaveat:"Estimates only. Batteries are not accounted for separately; their flow can affect the grid reading. No backfilling before tracking starts.",rate:"Net benefit now",total_net:"Accumulated net benefit",total_energy:"Surplus used by RRH",capture:"Surplus capture rate",live_chart:"Live efficiency",pv_power:"PV output",gross:"Self-consumption value",lost:"Foregone feed-in payment",captured:"Energy used",potential:"Tracked surplus",exported:"Remaining grid export",captureAvg:"Average capture",timeRunning:"Device running hours",moneyCoverage:"Energy with valid pricing",starts:"Starts",consumption:"Energy (kWh)",durationLabel:"Runtime (h)",resetStats:"Reset overall statistics",resetStatsConfirm:"Permanently reset RRH energy and cost statistics? Fairness statistics will be preserved.",priceMissing:"Configure import and feed-in prices on Energy & costs.",energySettings:"Energy & costs",dashboardSettings:"Dashboard cards & language",sourceMode:"Source",fixed:"Fixed value",entity:"HA entity",pvSize:"PV system size (W)",importPrice:"Grid import price (€/kWh)",feedPrice:"Feed-in compensation (€/kWh)",solarPower:"PV power sensor (W or kW, optional)",solarEnergy:"PV energy sensor (kWh, optional)",gridExportEnergy:"Grid export energy sensor (kWh, optional)",chartType:"Live chart",language:"Language",automatic:"Automatic (Home Assistant)",energyHelp:"Reuse HA Energy Dashboard price sources or set fixed rates. Net benefit is measured against export compensation; not your bill.",showCards:"Show or hide cards",sensorWarning:"Data source notices",unitsNotice:"PV capacity in W; rates per kWh in selected currency. No currency conversion.",chartGauge:"Efficiency bar",chartLine:"Line",chartBar:"Bars",chartArea:"Area",chartDonut:"Donut",chartStacked:"Stacked",chartSpark:"Sparkline",demo:"Demo mode",exitDemo:"Leave demo"},
  fr:{energyInfo:"Énergie et coûts", energyBody:"Estimations basées sur le réseau et les charges RRH confirmées.",overview:"Vue d’ensemble · depuis le début",dayStats:"Données quotidiennes · 45 jours",deviceStats:"Appareils · énergie et durée",chartStats:"Historique 24 heures · surplus utilisé (%)",dataCaveat:"Estimations. La batterie n’est pas comptabilisée séparément et peut influencer le réseau.",rate:"Gain net actuel",total_net:"Gain net cumulé",total_energy:"Surplus utilisé par RRH",capture:"Part du surplus utilisée",live_chart:"Efficacité en direct",pv_power:"Puissance PV",gross:"Valeur de l’autoconsommation",lost:"Rémunération d’injection perdue",captured:"Énergie utilisée",potential:"Surplus suivi",exported:"Injection restante",captureAvg:"Part utilisée globale",timeRunning:"Heures de fonctionnement",moneyCoverage:"Énergie tarifée",starts:"Démarrages",consumption:"Énergie (kWh)",durationLabel:"Durée (h)",resetStats:"Réinitialiser les statistiques",resetStatsConfirm:"Réinitialiser définitivement les statistiques énergie/coûts ? Les statistiques d’équité seront conservées.",priceMissing:"Configurez les prix d’achat et d’injection dans Énergie et coûts.",energySettings:"Énergie et coûts",dashboardSettings:"Cartes et langue",sourceMode:"Source",fixed:"Valeur fixe",entity:"Entité HA",pvSize:"Puissance installée PV (W)",importPrice:"Tarif d’achat (€/kWh)",feedPrice:"Tarif d’injection (€/kWh)",solarPower:"Capteur de puissance PV (optionnel)",solarEnergy:"Capteur d’énergie PV (optionnel)",gridExportEnergy:"Compteur d’injection (optionnel)",chartType:"Graphique direct",language:"Langue",automatic:"Automatique (Home Assistant)",energyHelp:"Choisissez des capteurs existants ou des valeurs fixes. Gain net après déduction de l’injection.",showCards:"Afficher/masquer les cartes",sensorWarning:"Remarques sur les sources",unitsNotice:"Capacité PV en W ; tarifs par kWh dans la monnaie choisie.",chartGauge:"Barre d’efficacité",chartLine:"Ligne",chartBar:"Barres",chartArea:"Zone",chartDonut:"Anneau",chartStacked:"Empilé",chartSpark:"Mini-courbe",demo:"Mode démo",exitDemo:"Quitter la démo"},
  es:{energyInfo:"Energía y costes", energyBody:"Estimaciones basadas en la red y las cargas RRH confirmadas.",overview:"Resumen · desde el inicio",dayStats:"Datos diarios · 45 días",deviceStats:"Dispositivos · energía y tiempo",chartStats:"Historial 24 horas · uso de excedentes (%)",dataCaveat:"Estimaciones. La batería no se contabiliza por separado y puede afectar a la lectura de red.",rate:"Beneficio neto actual",total_net:"Beneficio neto acumulado",total_energy:"Excedente aprovechado",capture:"Uso del excedente",live_chart:"Eficiencia en vivo",pv_power:"Potencia solar",gross:"Valor del autoconsumo",lost:"Compensación de exportación perdida",captured:"Energía aprovechada",potential:"Excedente registrado",exported:"Exportación restante",captureAvg:"Aprovechamiento total",timeRunning:"Horas de funcionamiento",moneyCoverage:"Energía con tarifa",starts:"Arranques",consumption:"Energía (kWh)",durationLabel:"Tiempo (h)",resetStats:"Reiniciar estadísticas",resetStatsConfirm:"¿Borrar las estadísticas de energía y costes? Se conservan las de equidad.",priceMissing:"Configura los precios de compra y vertido en Energía y costes.",energySettings:"Energía y costes",dashboardSettings:"Tarjetas e idioma",sourceMode:"Fuente",fixed:"Valor fijo",entity:"Entidad HA",pvSize:"Tamaño de instalación PV (W)",importPrice:"Precio de compra (€/kWh)",feedPrice:"Compensación de vertido (€/kWh)",solarPower:"Sensor de potencia solar (opcional)",solarEnergy:"Sensor de energía solar (opcional)",gridExportEnergy:"Contador de energía vertida (opcional)",chartType:"Gráfico en vivo",language:"Idioma",automatic:"Automático (Home Assistant)",energyHelp:"Usa sensores existentes o importes fijos. El beneficio neto descuenta el vertido perdido.",showCards:"Mostrar u ocultar tarjetas",sensorWarning:"Avisos de sensores",unitsNotice:"Potencia nominal PV en W, tarifas por kWh en moneda seleccionada.",chartGauge:"Barra de eficiencia",chartLine:"Línea",chartBar:"Barras",chartArea:"Área",chartDonut:"Anillo",chartStacked:"Apilado",chartSpark:"Minigráfico",demo:"Modo demo",exitDemo:"Salir de demo"},
  pt:{energyInfo:"Energia e custos", energyBody:"Estimativas a partir da rede e de cargas RRH confirmadas.",overview:"Resumo · desde o início",dayStats:"Valores diários · 45 dias",deviceStats:"Dispositivos · energia e tempo",chartStats:"Histórico 24 horas · utilização de excedente (%)",dataCaveat:"Estimativas. A bateria não é contabilizada em separado e pode afetar a leitura da rede.",rate:"Benefício líquido atual",total_net:"Benefício líquido acumulado",total_energy:"Excedente utilizado",capture:"Taxa de aproveitamento",live_chart:"Eficiência em direto",pv_power:"Potência solar",gross:"Valor do autoconsumo",lost:"Receita de injeção não recebida",captured:"Energia utilizada",potential:"Excedente registado",exported:"Injeção restante",captureAvg:"Aproveitamento médio",timeRunning:"Horas de funcionamento",moneyCoverage:"Energia com tarifa",starts:"Arranques",consumption:"Energia (kWh)",durationLabel:"Tempo (h)",resetStats:"Repor estatísticas",resetStatsConfirm:"Repor definitivamente as estatísticas de energia e custos? As estatísticas de justiça permanecem.",priceMissing:"Configure os preços de compra e injeção em Energia e custos.",energySettings:"Energia e custos",dashboardSettings:"Cartões e idioma",sourceMode:"Fonte",fixed:"Valor fixo",entity:"Entidade HA",pvSize:"Dimensão PV (W)",importPrice:"Preço de compra (€/kWh)",feedPrice:"Tarifa de injeção (€/kWh)",solarPower:"Sensor de potência PV (opcional)",solarEnergy:"Sensor de energia PV (opcional)",gridExportEnergy:"Contador de energia exportada (opcional)",chartType:"Gráfico em direto",language:"Idioma",automatic:"Automático (Home Assistant)",energyHelp:"Utilize sensores existentes ou valores fixos. Benefício líquido após deduzir a injeção.",showCards:"Mostrar ou ocultar cartões",sensorWarning:"Avisos de sensores",unitsNotice:"Capacidade PV em W, tarifas por kWh na moeda selecionada.",chartGauge:"Barra de eficiência",chartLine:"Linha",chartBar:"Barras",chartArea:"Área",chartDonut:"Anel",chartStacked:"Empilhado",chartSpark:"Minigráfico",demo:"Modo demo",exitDemo:"Sair da demo"},
  it:{energyInfo:"Energia e costi", energyBody:"Stime basate sulla rete e sui carichi RRH confermati.",overview:"Riepilogo · dall’inizio",dayStats:"Dati giornalieri · 45 giorni",deviceStats:"Dispositivi · energia e durata",chartStats:"Storico 24 ore · uso del surplus (%)",dataCaveat:"Stime. La batteria non è contabilizzata separatamente e può influenzare la lettura di rete.",rate:"Beneficio netto attuale",total_net:"Beneficio netto totale",total_energy:"Surplus usato da RRH",capture:"Quota di surplus utilizzata",live_chart:"Efficienza in tempo reale",pv_power:"Potenza FV",gross:"Valore dell’autoconsumo",lost:"Ricavo da immissione rinunciato",captured:"Energia utilizzata",potential:"Surplus rilevato",exported:"Immissione residua",captureAvg:"Utilizzo medio",timeRunning:"Ore di funzionamento",moneyCoverage:"Energia valorizzata",starts:"Avvii",consumption:"Energia (kWh)",durationLabel:"Durata (h)",resetStats:"Azzera statistiche",resetStatsConfirm:"Azzerare definitivamente le statistiche di energia e costi? Le statistiche di equità rimangono.",priceMissing:"Configura i prezzi di acquisto e immissione in Energia e costi.",energySettings:"Energia e costi",dashboardSettings:"Schede e lingua",sourceMode:"Fonte",fixed:"Valore fisso",entity:"Entità HA",pvSize:"Dimensione impianto FV (W)",importPrice:"Prezzo di acquisto (€/kWh)",feedPrice:"Tariffa di immissione (€/kWh)",solarPower:"Sensore potenza FV (opzionale)",solarEnergy:"Sensore energia FV (opzionale)",gridExportEnergy:"Contatore immissione (opzionale)",chartType:"Grafico in tempo reale",language:"Lingua",automatic:"Automatico (Home Assistant)",energyHelp:"Usa sensori HA o valori fissi. Il beneficio netto sottrae il ricavo da immissione.",showCards:"Mostra o nascondi schede",sensorWarning:"Avvisi delle fonti",unitsNotice:"Capacità PV in W, tariffe per kWh nella valuta scelta.",chartGauge:"Barra di efficienza",chartLine:"Linea",chartBar:"Barre",chartArea:"Area",chartDonut:"Anello",chartStacked:"Impilato",chartSpark:"Mini-grafico",demo:"Modalità demo",exitDemo:"Esci dalla demo"}
};

Object.assign(LOCALIZED_STATS.fr,{dashboard:"Tableau de bord",consumers:"Appareils",profiles:"Profils",energy:"Énergie et coûts",settings:"Paramètres",page:"Page",on:"RRH MARCHE",off:"Tout ARRÊTER",pause:"Pause",mode:"État",grid:"Réseau",budget:"Puissance disponible",managed:"Puissance gérée",pipeline:"Ordre d'attribution",active:"En marche",paused:"En pause",error:"Erreur",stopped:"Arrêté",source:"Source réseau",control:"Commande",fresh:"Qualité des données",save:"Enregistrer",reset:"Recharger",consumerHeader:"Appareils",profileInfo:"Profils et priorité",add:"Ajouter un appareil"});
Object.assign(LOCALIZED_STATS.es,{dashboard:"Panel",consumers:"Dispositivos",profiles:"Perfiles",energy:"Energía y costes",settings:"Ajustes",page:"Página",on:"RRH ACTIVAR",off:"APAGAR todo",pause:"Pausa",mode:"Estado",grid:"Red",budget:"Potencia disponible",managed:"Potencia gestionada",pipeline:"Orden de asignación",active:"Activo",paused:"Pausado",error:"Error",stopped:"Detenido",source:"Fuente de red",control:"Control",fresh:"Calidad de datos",save:"Guardar",reset:"Recargar",consumerHeader:"Dispositivos",profileInfo:"Perfiles y prioridad",add:"Añadir dispositivo"});
Object.assign(LOCALIZED_STATS.pt,{dashboard:"Painel",consumers:"Dispositivos",profiles:"Perfis",energy:"Energia e custos",settings:"Definições",page:"Página",on:"RRH LIGAR",off:"DESLIGAR todos",pause:"Pausa",mode:"Estado",grid:"Rede",budget:"Potência disponível",managed:"Potência gerida",pipeline:"Ordem de atribuição",active:"Ativo",paused:"Pausado",error:"Erro",stopped:"Parado",source:"Fonte de rede",control:"Controlo",fresh:"Qualidade dos dados",save:"Guardar",reset:"Recarregar",consumerHeader:"Dispositivos",profileInfo:"Perfis e prioridade",add:"Adicionar dispositivo"});
Object.assign(LOCALIZED_STATS.it,{dashboard:"Dashboard",consumers:"Dispositivi",profiles:"Profili",energy:"Energia e costi",settings:"Impostazioni",page:"Pagina",on:"RRH ACCENDI",off:"SPEGNI tutto",pause:"Pausa",mode:"Stato",grid:"Rete",budget:"Potenza disponibile",managed:"Potenza gestita",pipeline:"Ordine di assegnazione",active:"Attivo",paused:"In pausa",error:"Errore",stopped:"Fermo",source:"Fonte rete",control:"Controllo",fresh:"Qualità dati",save:"Salva",reset:"Ricarica",consumerHeader:"Dispositivi",profileInfo:"Profili e priorità",add:"Aggiungi dispositivo"});

const LOCALE_KEYS = {de:"de-DE",en:"en-GB",fr:"fr-FR",es:"es-ES",pt:"pt-PT",it:"it-IT"};
// All new 0.9.1 interactive strings are supplied in all supported UI languages.
const RELEASE_COPY = {
 de:{startupPending:"Autostart wartet",howtoIntro:"Anleitungsartikel direkt lesen: Kapitel links auswählen oder suchen.",startupTitle:"Startverhalten bei HA-Neustart",startupHelp:"Neustart: erst nach frischer Netzleistungsmeldung und geprüften Verbrauchern regeln. Kein blindes Wiederherstellen von Schalterstellungen.",startupLast:"Letzten RRH-Zustand wiederherstellen",startupOn:"Immer EIN (nach Sicherheitsprüfung)",startupOff:"Immer AUS (empfohlen)",sensorChoose:"Nur kompatible HA-Sensoren werden angezeigt.",donation:"Gib einen Drink aus",donationSetting:"Spendenhinweis im Dashboard anzeigen",profileMembers:"Teilnehmer des Profils",energyConfig:"Tarife & PV-Daten",resetTitle:"RRH vollständig zurücksetzen",resetAction:"Alle RRH-Daten löschen",resetWarning:"Unwiderruflich: Verbraucher, Profile, Einstellungen, Laufzeiten, Statistiken und die gespeicherte Bestätigung des Sicherheitshinweises werden gelöscht. HA-Geräte und HA-Verlauf bleiben unverändert. Erst nach bestätigtem Alle AUS möglich.",resetType:"Zur Bestätigung RESET ROUND ROBIN HOOD eingeben",resetCancel:"Abbrechen",resetExecute:"Alle AUS & unwiderruflich löschen",resetFailure:"Reset fehlgeschlagen: Keine Daten erneut löschen. HA-Protokoll prüfen.",aboutImprint:"Impressum",aboutMaker:"Erstellt von",aboutLinks:"Kanäle von Satisfried",aboutVersions:"Versionsinformationen",aboutHa:"Home Assistant Core",aboutUnknown:"Nicht verfügbar",aboutSafety:"Privates, KI-unterstützt entstandenes Projekt. Keine zertifizierte Sicherheitssteuerung; unabhängige Schutzmaßnahmen sind erforderlich.",aboutCopyright:"Copyright (c) 2026 Satisfried. Apache-2.0-Lizenz; keine Markenrechte eingeräumt.",iconHint:"Symbol auswählen",donationTooltip:"Große Mengen Rum-Cola waren Treibstoff für dieses Projekt. Das kostet.",welcomeTitle:"Willkommen bei Round Robin Hood",welcomeLead:"Wie möchtest du beginnen? Keine der Optionen schaltet ungefragt echte Verbraucher ein.",welcomeWizard:"Einrichtungsassistent starten",welcomeWizardHelp:"Sensoren, Verbraucher, Profile und Tarife Schritt für Schritt einrichten.",welcomeDemo:"Demo-Modus ausprobieren",welcomeDemoHelp:"Sechs virtuelle Verbraucher ausprobieren. Keine Steuerung echter Geräte.",welcomeSkip:"Einrichtung überspringen",welcomeSkipHelp:"RRH bleibt AUS. Du kannst später alles manuell einrichten oder den Assistenten erneut starten.",welcomeError:"Auswahl konnte nicht gespeichert werden. Bitte erneut versuchen."},
 en:{startupPending:"Waiting to auto-start",howtoIntro:"Read the guide here: choose or search chapters in the sidebar.",startupTitle:"Behavior on Home Assistant restart",startupHelp:"After restart, wait for a fresh grid report and verified consumer states. Never blindly restore switch states.",startupLast:"Restore last RRH state",startupOn:"Always ON (after safety checks)",startupOff:"Always OFF (recommended)",sensorChoose:"Only compatible Home Assistant sensors are shown.",donation:"Buy me a drink",donationSetting:"Show donation link on the dashboard",profileMembers:"Profile participants",energyConfig:"Tariffs & PV details",resetTitle:"Factory reset Round Robin Hood",resetAction:"Delete all RRH data",resetWarning:"Irreversible: consumers, profiles, settings, runtime, statistics and the saved safety acknowledgment will be deleted. HA devices and HA history remain untouched. Reset requires confirmed All OFF.",resetType:"Type RESET ROUND ROBIN HOOD to confirm",resetCancel:"Cancel",resetExecute:"All OFF & permanently reset",resetFailure:"Reset failed. Do not retry blindly; check HA logs.",aboutImprint:"Legal notice",aboutMaker:"Created by",aboutLinks:"Satisfried channels",aboutVersions:"Version information",aboutHa:"Home Assistant Core",aboutUnknown:"Unavailable",aboutSafety:"Independent project created with AI assistance. Not a certified safety controller; independent protections are required.",aboutCopyright:"Copyright (c) 2026 Satisfried. Apache-2.0 license; no trademark rights granted.",iconHint:"Choose an icon",donationTooltip:"Large amounts of rum and cola fueled this project. That adds up.",welcomeTitle:"Welcome to Round Robin Hood",welcomeLead:"How would you like to begin? None of these options switches on real devices automatically.",welcomeWizard:"Start setup wizard",welcomeWizardHelp:"Configure sensors, consumers, profiles and prices step by step.",welcomeDemo:"Try demo mode",welcomeDemoHelp:"Explore six simulated consumers without controlling real devices.",welcomeSkip:"Skip setup",welcomeSkipHelp:"RRH remains OFF. Set it up manually or restart the wizard later.",welcomeError:"Could not save your choice. Please try again."},
 fr:{startupPending:"Démarrage en attente",howtoIntro:"Lisez le guide ici : choisissez ou recherchez un chapitre dans la navigation.",startupTitle:"Comportement au redémarrage HA",startupHelp:"Attendre une nouvelle mesure réseau et les états vérifiés des appareils avant toute commande.",startupLast:"Rétablir le dernier état RRH",startupOn:"Toujours ACTIVÉ (après contrôle)",startupOff:"Toujours ARRÊT (recommandé)",sensorChoose:"Seuls les capteurs compatibles sont affichés.",donation:"Offrir un verre",donationSetting:"Afficher le lien de don sur le tableau de bord",profileMembers:"Participants du profil",energyConfig:"Tarifs et données PV",resetTitle:"Réinitialiser complètement RRH",resetAction:"Supprimer toutes les données RRH",resetWarning:"Irréversible : appareils, profils, réglages, durées, statistiques et confirmation de sécurité seront supprimés. Les appareils et l’historique HA restent intacts. Tous les appareils doivent être confirmés éteints.",resetType:"Saisir RESET ROUND ROBIN HOOD pour confirmer",resetCancel:"Annuler",resetExecute:"Tout éteindre et réinitialiser",resetFailure:"Échec de la réinitialisation. Vérifier les journaux HA.",aboutImprint:"Mentions légales",aboutMaker:"Créé par",aboutLinks:"Chaînes de Satisfried",aboutVersions:"Versions",aboutHa:"Home Assistant Core",aboutUnknown:"Indisponible",aboutSafety:"Projet indépendant créé avec l’aide de l’IA. Ce logiciel ne remplace pas un dispositif de sécurité certifié.",aboutCopyright:"Copyright (c) 2026 Satisfried. Licence Apache 2.0 ; aucun droit de marque accordé.",iconHint:"Choisir une icône",donationTooltip:"De grandes quantités de rhum-cola ont alimenté ce projet. Cela a un coût.",welcomeTitle:"Bienvenue dans Round Robin Hood",welcomeLead:"Comment voulez-vous commencer ? Aucune option n’active automatiquement des appareils réels.",welcomeWizard:"Lancer l’assistant",welcomeWizardHelp:"Configurer pas à pas les capteurs, appareils, profils et tarifs.",welcomeDemo:"Essayer le mode démo",welcomeDemoHelp:"Six appareils simulés, sans contrôle d’appareils réels.",welcomeSkip:"Ignorer la configuration",welcomeSkipHelp:"RRH reste ARRÊT. Configuration manuelle ou assistant disponible plus tard.",welcomeError:"Impossible d’enregistrer ce choix. Réessayez."},
 es:{startupPending:"Inicio pendiente",howtoIntro:"Lee la guía aquí: elige o busca un capítulo en la navegación.",startupTitle:"Inicio tras reiniciar Home Assistant",startupHelp:"Esperar una nueva medición de red y estados verificados antes de activar dispositivos.",startupLast:"Restaurar último estado de RRH",startupOn:"Siempre ENCENDIDO (tras comprobar)",startupOff:"Siempre APAGADO (recomendado)",sensorChoose:"Solo se muestran sensores compatibles.",donation:"Invítame a una copa",donationSetting:"Mostrar enlace de donación en el panel",profileMembers:"Participantes del perfil",energyConfig:"Tarifas y datos FV",resetTitle:"Restablecer RRH completamente",resetAction:"Borrar todos los datos de RRH",resetWarning:"Irreversible: se borrarán dispositivos, perfiles, ajustes, tiempos, estadísticas y la confirmación de seguridad. Los dispositivos y el historial de HA no se modifican. Se requiere apagado confirmado.",resetType:"Escribe RESET ROUND ROBIN HOOD para confirmar",resetCancel:"Cancelar",resetExecute:"Apagar todo y restablecer",resetFailure:"Error al restablecer. Revisar registros de HA.",aboutImprint:"Aviso legal",aboutMaker:"Creado por",aboutLinks:"Canales de Satisfried",aboutVersions:"Versiones",aboutHa:"Home Assistant Core",aboutUnknown:"No disponible",aboutSafety:"Proyecto independiente creado con ayuda de IA. No sustituye un sistema de seguridad certificado.",aboutCopyright:"Copyright (c) 2026 Satisfried. Licencia Apache 2.0; no se conceden derechos de marca.",iconHint:"Elegir icono",donationTooltip:"Grandes cantidades de ron con cola impulsaron este proyecto. Y eso cuesta.",welcomeTitle:"Bienvenido a Round Robin Hood",welcomeLead:"¿Cómo quieres comenzar? Ninguna opción activa automáticamente dispositivos reales.",welcomeWizard:"Iniciar asistente",welcomeWizardHelp:"Configura sensores, consumidores, perfiles y tarifas paso a paso.",welcomeDemo:"Probar modo de demostración",welcomeDemoHelp:"Seis consumidores simulados; no se controlan dispositivos reales.",welcomeSkip:"Omitir configuración",welcomeSkipHelp:"RRH permanece APAGADO. Puedes configurarlo manualmente después.",welcomeError:"No se pudo guardar la selección. Inténtalo de nuevo."},
 pt:{startupPending:"Início em espera",howtoIntro:"Leia o guia aqui: escolha ou pesquise um capítulo na navegação.",startupTitle:"Início após reiniciar o Home Assistant",startupHelp:"Aguardar nova medição da rede e confirmar os estados dos dispositivos antes de atuar.",startupLast:"Restaurar último estado do RRH",startupOn:"Sempre LIGADO (após verificação)",startupOff:"Sempre DESLIGADO (recomendado)",sensorChoose:"Apenas sensores compatíveis são apresentados.",donation:"Paga-me uma bebida",donationSetting:"Mostrar ligação para donativos no painel",profileMembers:"Participantes do perfil",energyConfig:"Tarifas e dados solares",resetTitle:"Repor completamente o RRH",resetAction:"Apagar todos os dados do RRH",resetWarning:"Irreversível: dispositivos, perfis, definições, tempos, estatísticas e confirmação de segurança serão apagados. Os dispositivos e histórico do HA ficam intactos. Requer desligamento confirmado.",resetType:"Escreva RESET ROUND ROBIN HOOD para confirmar",resetCancel:"Cancelar",resetExecute:"Desligar tudo e repor",resetFailure:"Falha na reposição. Consulte os registos do HA.",aboutImprint:"Aviso legal",aboutMaker:"Criado por",aboutLinks:"Canais de Satisfried",aboutVersions:"Versões",aboutHa:"Home Assistant Core",aboutUnknown:"Indisponível",aboutSafety:"Projeto independente criado com apoio de IA. Não substitui um controlador de segurança certificado.",aboutCopyright:"Copyright (c) 2026 Satisfried. Licença Apache 2.0; sem concessão de direitos de marca.",iconHint:"Escolher ícone",donationTooltip:"Muito rum e cola alimentaram este projeto. E isso custa dinheiro.",welcomeTitle:"Bem-vindo ao Round Robin Hood",welcomeLead:"Como quer começar? Nenhuma opção liga automaticamente dispositivos reais.",welcomeWizard:"Iniciar assistente",welcomeWizardHelp:"Configure sensores, consumidores, perfis e tarifas passo a passo.",welcomeDemo:"Experimentar modo de demonstração",welcomeDemoHelp:"Explore seis consumidores simulados sem comandar dispositivos reais.",welcomeSkip:"Ignorar configuração",welcomeSkipHelp:"RRH continua DESLIGADO. Pode configurá-lo manualmente mais tarde.",welcomeError:"Não foi possível guardar a opção. Tente novamente."},
 it:{startupPending:"Avvio in attesa",howtoIntro:"Leggi qui la guida: scegli o cerca un capitolo nel menu.",startupTitle:"Avvio dopo il riavvio di Home Assistant",startupHelp:"Attendere una nuova misura di rete e stati verificati dei dispositivi prima di azionarli.",startupLast:"Ripristina l’ultimo stato RRH",startupOn:"Sempre ACCESO (dopo i controlli)",startupOff:"Sempre SPENTO (consigliato)",sensorChoose:"Vengono mostrati solo i sensori compatibili.",donation:"Offrimi un drink",donationSetting:"Mostra il link per le donazioni nella dashboard",profileMembers:"Partecipanti al profilo",energyConfig:"Tariffe e dati FV",resetTitle:"Ripristina completamente RRH",resetAction:"Elimina tutti i dati RRH",resetWarning:"Irreversibile: dispositivi, profili, impostazioni, tempi, statistiche e conferma di sicurezza verranno eliminati. Dispositivi e cronologia HA restano invariati. Occorre lo spegnimento confermato.",resetType:"Digita RESET ROUND ROBIN HOOD per confermare",resetCancel:"Annulla",resetExecute:"Spegni tutto e ripristina",resetFailure:"Ripristino non riuscito. Controlla i log di HA.",aboutImprint:"Note legali",aboutMaker:"Creato da",aboutLinks:"Canali di Satisfried",aboutVersions:"Versioni",aboutHa:"Home Assistant Core",aboutUnknown:"Non disponibile",aboutSafety:"Progetto indipendente creato con il supporto dell’IA. Non sostituisce un sistema di sicurezza certificato.",aboutCopyright:"Copyright (c) 2026 Satisfried. Licenza Apache 2.0; nessun diritto sui marchi concesso.",iconHint:"Scegli un'icona",donationTooltip:"Tanto rum e cola hanno alimentato questo progetto. E costa.",welcomeTitle:"Benvenuto in Round Robin Hood",welcomeLead:"Come vuoi iniziare? Nessuna opzione attiva automaticamente dispositivi reali.",welcomeWizard:"Avvia configurazione guidata",welcomeWizardHelp:"Configura sensori, dispositivi, profili e tariffe passo dopo passo.",welcomeDemo:"Prova la modalità demo",welcomeDemoHelp:"Esplora sei dispositivi simulati senza comandare quelli reali.",welcomeSkip:"Salta la configurazione",welcomeSkipHelp:"RRH resta SPENTO. Potrai configurarlo manualmente in seguito.",welcomeError:"Impossibile salvare la scelta. Riprova."}
};
const CHART_LABELS = {gauge:"chartGauge",line:"chartLine",bar:"chartBar",area:"chartArea",donut:"chartDonut",stacked:"chartStacked",sparkline:"chartSpark"};
const CARD_NAMES = {grid:"grid",budget:"budget",managed:"managed",live_chart:"live_chart",rate:"rate",total_net:"total_net",total_energy:"total_energy",capture:"capture",pipeline:"pipeline",pv_power:"pv_power"};


// Small, explicit legacy UI translations. The new statistics UI uses keyed
// translations above. Preserve the original German text per DOM node so a
// language change is reversible without replacing or losing input elements.
const LEGACY_WORDS = new Map([
  ["Profil erstellen",["Create profile","Créer un profil","Crear perfil","Criar perfil","Crea profilo"]],
  ["Verbraucher",["Consumer","Appareil","Dispositivo","Dispositivo","Dispositivo"]],
  ["Profil bearbeiten",["Edit profile","Modifier le profil","Editar perfil","Editar perfil","Modifica profilo"]],
  ["Verbraucher bearbeiten",["Edit consumer","Modifier l’appareil","Editar dispositivo","Editar dispositivo","Modifica dispositivo"]],
  ["Name",["Name","Nom","Nombre","Nome","Nome"]],
  ["Verbrauchertyp",["Consumer type","Type d’appareil","Tipo de dispositivo","Tipo de dispositivo","Tipo di dispositivo"]],
  ["Nenn- oder Mindestleistung (W)",["Rated or minimum power (W)","Puissance nominale ou minimale (W)","Potencia nominal o mínima (W)","Potência nominal ou mínima (W)","Potenza nominale o minima (W)"]],
  ["HA-Steuerentität",["HA control entity","Entité de contrôle HA","Entidad de control HA","Entidade de controlo HA","Entità di controllo HA"]],
  ["Ein / Aus (Schalter)",["On / Off (switch)","Marche / arrêt (interrupteur)","Encender / apagar", "Ligar / desligar", "Acceso / spento"]],
  ["Mehrstufig",["Multiple stages","Plusieurs niveaux","Varios niveles","Vários níveis","Più livelli"]],
  ["Stufenlos regelbar (Watt-Sollwert)",["Stepless (Watt setpoint)","Réglage continu (watts)","Regulación continua (vatios)","Regulação contínua (watts)","Regolazione continua (watt)"]],
  ["Teilnahme",["Participation","Participation","Participación","Participação","Partecipazione"]],
  ["Profil speichern",["Save profile","Enregistrer le profil","Guardar perfil","Guardar perfil","Salva profilo"]],
  ["Speichern",["Save","Enregistrer","Guardar","Guardar","Salva"]],
  ["Abbrechen",["Cancel","Annuler","Cancelar","Cancelar","Annulla"]],
  ["Löschen",["Delete","Supprimer","Eliminar","Eliminar","Elimina"]],
  ["Entfernen",["Remove","Supprimer","Quitar","Remover","Rimuovi"]],
  ["Profilname",["Profile name","Nom du profil","Nombre del perfil","Nome do perfil","Nome profilo"]],
  ["Verteilstrategie",["Allocation strategy","Stratégie de répartition","Estrategia de reparto","Estratégia de distribuição","Strategia di distribuzione"]],
  ["Profil aktiv (nimmt am Betrieb teil)",["Active profile (participates)","Profil actif (participe)","Perfil activo (participa)","Perfil ativo (participa)","Profilo attivo (partecipa)"]],
  ["Netzleistung aus Home Assistant",["Grid power from Home Assistant","Puissance réseau Home Assistant","Potencia de red Home Assistant","Potência da rede Home Assistant","Potenza rete Home Assistant"]],
  ["Vorzeichen der Quelle",["Source sign","Signe de la source","Signo de la fuente","Sinal da fonte","Segno della fonte"]],
  ["Leistungsreserve (W)",["Power reserve (W)","Réserve de puissance (W)","Reserva de potencia (W)","Reserva de potência (W)","Riserva di potenza (W)"]],
  ["Globale Unterlastverzögerung aktivieren",["Enable global deficit delay","Activer le délai de déficit global","Activar retraso global por déficit","Ativar atraso de défice global","Abilita ritardo per deficit globale"]],
  ["Globale Unterlastverzögerung (Sekunden)",["Global deficit delay (seconds)","Délai de déficit global (secondes)","Retraso global por déficit (segundos)","Atraso global de défice (segundos)","Ritardo deficit globale (secondi)"]],
  ["Timer-Überspringen bestätigen",["Confirm timer skips","Confirmer le saut des minuteries","Confirmar omisión de temporizadores","Confirmar salto dos temporizadores","Conferma salto timer"]],
  ["Profil-Deaktivierung bestätigen",["Confirm profile deactivation","Confirmer la désactivation du profil","Confirmar desactivación del perfil","Confirmar desativação do perfil","Conferma disattivazione profilo"]],
  ["Keinen verwenden",["None","Aucun","Ninguno","Nenhum","Nessuno"]],
  ["Maximales Meldungsalter (Sekunden)",["Maximum meter update age (seconds)","Âge maximal des mesures (secondes)","Edad máxima del dato (segundos)","Idade máxima da medição (segundos)","Età massima misura (secondi)"]],
  ["Einstellungen",["Settings","Paramètres","Ajustes","Definições","Impostazioni"]],
  ["Restüberschussverbraucher",["Residual surplus consumer","Consommateur du surplus résiduel","Consumidor del excedente residual","Consumidor do excedente residual","Consumatore del surplus residuo"]],
  ["Verbraucher auswählen",["Select consumers","Sélectionner les appareils","Seleccionar dispositivos","Selecionar dispositivos","Seleziona dispositivi"]],
  ["Reihenfolge der Karten im Dashboard",["Dashboard card order","Ordre des cartes du tableau de bord","Orden de tarjetas en el panel","Ordem dos cartões no painel","Ordine schede dashboard"]],
  ["Feste Profilreihenfolge",["Fixed profile order","Ordre fixe des profils","Orden fijo de perfiles","Ordem fixa de perfis","Ordine fisso dei profili"]],
  ["Nächster Kandidat",["Next candidate","Prochain candidat","Siguiente candidato","Próximo candidato","Prossimo candidato"]],
  ["Pausiert",["Paused","En pause","Pausado","Pausado","In pausa"]],
  ["Betrieb pausiert",["Operation paused","Fonctionnement en pause","Funcionamiento pausado","Operação em pausa","Funzionamento in pausa"]],
  ["Betrieb gestoppt",["Operation stopped","Fonctionnement arrêté","Funcionamiento detenido","Operação parada","Funzionamento arrestato"]],
]);
const LEGACY_LANGUAGE_INDEX={en:0,fr:1,es:2,pt:3,it:4};

const PAGES = ["dashboard", "consumers", "profiles", "energy", "settings", "howto", "about"];
const fmt = new Intl.NumberFormat("de-DE", {maximumFractionDigits: 1});
const watts = value => value == null ? "—" : `${fmt.format(value)} W`;
const duration = seconds => {
  const total = Math.max(0, Math.ceil(Number(seconds) || 0));
  return [Math.floor(total / 3600), Math.floor(total % 3600 / 60), total % 60].map(n => String(n).padStart(2,"0")).join(":");
};
const text = (node, value) => { node.textContent = value ?? ""; };
const copy = value => JSON.parse(JSON.stringify(value));
function node(tag, label, cls) {
  const el = document.createElement(tag);
  if (label != null) el.textContent = label;
  if (cls) el.className = cls;
  return el;
}
function consumerIcon(c) {
  const wrapper = node("span", null, "consumer-icon");
  wrapper.setAttribute("aria-hidden", "true");
  if (c.icon_image) {
    const img = node("img");
    img.src = c.icon_image; img.alt = ""; img.loading = "lazy";
    wrapper.append(img);
  } else {
    const mdi = node("ha-icon");
    mdi.setAttribute("icon", c.icon || "mdi:power-plug");
    wrapper.append(mdi, node("span", "⚡", "icon-fallback"));
  }
  return wrapper;
}
function identifier() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes); // Works on local HTTP too, unlike randomUUID().
  return Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
}

class RrhHoodPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: "open"});
    this._hass = null;
    this._data = null;
    this._timer = null;
    this._polling = false;
    this._writing = false;
    this._writeCount = 0;
    this._settingsDirty = false;
    this._settingsRevision = null;
    this._rowsFingerprint = "";
    this._page = "dashboard";
    this._profileDraftIds = [];
    this._editorImage = null;
    this._language = "de";
    this._emergencyOrdinal = 0;
    this._offRequested = false;
    this._requestOrdinal = 0;
    this._helpCounter = 0;
    this._originalText = new WeakMap();
    this._noticeShownThisVisit = false;
    this._wizardOfferedThisVisit = false;
    this._wizardStep = 0;
    this._wizardManual = false;
    this._tariffFieldsEdited = new Set();
    this._wizardRateEdited = new Set();
  }
  set hass(value) {
    this._hass = value;
    const language = String(value?.locale?.language || value?.language || "de").toLowerCase();
    const configured=this._data?.config?.dashboard?.language || "auto";
    const detected=["de","en","fr","es","pt","it"].find(code=>language.startsWith(code)) || "en";
    const nextLanguage = configured === "auto" ? detected : configured;
    if (this._language !== nextLanguage) { this._language = nextLanguage; if (this._built) this._translateStatic(); }
    if (this.isConnected && this._built && !this._timer && !this._polling) this._poll();
  }
  get hass() { return this._hass; }
  connectedCallback() {
    // HA may assign properties before this module is registered (including on F5).
    for (const key of ["hass", "narrow", "panel", "route"]) {
      if (Object.prototype.hasOwnProperty.call(this, key)) {
        const value = this[key]; delete this[key]; this[key] = value;
      }
    }
    if (!this._built) this._build();
    this._noticeShownThisVisit = false;
    this._wizardOfferedThisVisit = false;
    this._poll();
  }
  disconnectedCallback() { clearTimeout(this._timer); this._timer = null; }
  $(selector) { return this.shadowRoot.querySelector(selector); }
  _tr(key) { return RELEASE_COPY[this._language]?.[key] || LOCALIZED_STATS[this._language]?.[key] || (this._language === "en" ? UI_EN : UI_DE)[key] || UI_EN[key] || UI_DE[key] || key; }
  _translateStatic() {
    for (const el of this.shadowRoot.querySelectorAll("[data-release-i18n]")) text(el, this._tr(el.dataset.releaseI18n));
    for (const el of this.shadowRoot.querySelectorAll("[data-i18n]")) {
      const helpNodes = Array.from(el.children).filter(child => child.classList.contains("info-wrap"));
      text(el, this._tr(el.dataset.i18n));
      if (helpNodes.length) el.append(...helpNodes);
    }
    for (const el of this.shadowRoot.querySelectorAll("[data-nav]")) text(el, this._tr(el.dataset.nav));
    for (const option of this.$("#page-choice").options) text(option, this._tr(option.value));
    for (const option of this.$("#profile-strategy").options) text(option, this._strategyLabel(option.value));
    this.$("#page-choice-label").firstChild.textContent = `${this._tr("page")}: `;
    for (const el of this.shadowRoot.querySelectorAll(".info-wrap[data-help-key]")) {
      text(el.querySelector(".info-popover"), this._help(el.dataset.helpKey));
    }
    for (const button of this.shadowRoot.querySelectorAll("[data-action-help]")) button.title = this._help(button.dataset.actionHelp);
    if(this.$("#donation-link"))this.$("#donation-link").title=this._tr("donationTooltip");
    // The English slogan is intentionally the same international brand line in every language.
    if(this.$("#howto-intro"))text(this.$("#howto-intro"),this._tr("howtoIntro"));
    const guide=this.$("#guide-frame");if(guide){const lang=["de","en","fr","es","pt","it"].includes(this._language)?this._language:"en";if(guide.dataset.language!==lang){guide.dataset.language=lang;guide.src=`/${DOMAIN}/guide/${lang}/index.html`;}}
    this._localizeLegacy();
    if(this.$("#stat-currency")) this._currencyLabels();
    if (this._data) this._render();
  }
  _localizeLegacy() {
    if (!this._built) return;
    const walker=document.createTreeWalker(this.shadowRoot, NodeFilter.SHOW_TEXT);
    let current;
    while((current=walker.nextNode())) {
      if(current.parentElement?.closest?.('[data-i18n],.info-wrap,script,style,svg')) continue;
      const original=this._originalText.get(current) || current.nodeValue.trim();
      const options=LEGACY_WORDS.get(original);
      if(!options) continue;
      this._originalText.set(current,original);
      const target=LEGACY_LANGUAGE_INDEX[this._language]===undefined?original:options[LEGACY_LANGUAGE_INDEX[this._language]];
      const textValue=current.nodeValue;
      const leading=textValue.match(/^\s*/)?.[0]||"";
      const trailing=textValue.match(/\s*$/)?.[0]||"";
      current.nodeValue=leading+target+trailing;
    }
  }
  _help(key) { return key === "donationTooltip" ? this._tr(key) : ((HELP[this._language] || HELP.de)[key] || HELP.de[key] || key); }
  _strategyLabel(key) { return (this._language === "en" ? STRATEGY_LABELS_EN : STRATEGY_LABELS)[key] || key; }
  _info(key) {
    const wrapper = node("span", null, "info-wrap");
    wrapper.dataset.helpKey = key;
    const button = node("button", "i", "info-button");
    button.type = "button";
    button.setAttribute("aria-label", this._language === "en" ? "Show information" : "Information anzeigen");
    button.setAttribute("aria-expanded", "false");
    const popover = node("span", this._help(key), "info-popover");
    popover.id = `rrh-info-${++this._helpCounter}`;
    popover.setAttribute("role", "tooltip");
    button.setAttribute("aria-describedby", popover.id);
    button.onclick = event => {
      event.preventDefault(); event.stopPropagation();
      const opening = !wrapper.classList.contains("open");
      this._closeInfo();
      wrapper.classList.toggle("open", opening);
      button.setAttribute("aria-expanded", String(opening));
    };
    wrapper.append(button, popover);
    return wrapper;
  }
  _closeInfo() {
    for (const el of this.shadowRoot.querySelectorAll(".info-wrap.open")) {
      el.classList.remove("open");
      el.querySelector(".info-button")?.setAttribute("aria-expanded", "false");
    }
  }
  _setupInfo() {
    const attach = (selector, key) => {
      const target = this.$(selector);
      if (target) target.append(this._info(key));
    };
    for (const [id, key] of [["activate", "start"], ["pause", "pause"], ["main-off", "off"]]) {
      const button = this.$(`#${id}`), holder = node("span", null, "operation-action");
      button.dataset.actionHelp = key;
      button.title = this._help(key);
      button.replaceWith(holder);
      holder.append(button, this._info(key));
    }
    this.$("#donation-info").append(this._info("donationTooltip"));
    this.$("#donation-link").title = this._tr("donationTooltip");
    for (const [selector, key] of [
      ["#grid-title", "grid"],
      ["#budget-title", "budget"], ["#allocation-title", "candidate"],
      ["#managed-title", "managed"], ["#total-usable-label", "total"],
      ["#pipeline-title", "pipeline"], ["#consumers-heading", "consumers"],
      ["#profiles-heading", "profiles"], ["#settings-heading", "settings"],
      ["#energy-heading", "energy"],
      ["#source-settings .settings-summary strong", "gridSource"],
      ["#control-settings .settings-summary strong", "control"],
      ["#freshness-settings .settings-summary strong", "freshness"],
    ]) attach(selector, key);
    this.shadowRoot.addEventListener("click", event => {
      if (!event.target.closest(".info-wrap")) this._closeInfo();
    });
    this.shadowRoot.addEventListener("keydown", event => {
      if (event.key === "Escape") this._closeInfo();
    });
  }
  _compactFormHelp() {
    for (const help of Array.from(this.shadowRoot.querySelectorAll("#editor .help, #profile-editor .help, #settings-form .help"))) {
      const description = help.textContent.trim();
      const controlLabel = help.closest("label");
      const section = help.closest(".condition-edit, .time-group");
      if (controlLabel) {
        const wrapper = node("div", null, "field-help");
        wrapper.hidden = controlLabel.hidden;
        controlLabel.hidden = false;
        controlLabel.replaceWith(wrapper);
        wrapper.append(controlLabel, this._info(description));
      } else if (section) {
        section.classList.add("has-help");
        section.append(this._info(description));
      } else if (help.closest("#profile-editor")) {
        this.$("#profile-editor-title").append(this._info(description));
      }
      help.remove();
    }
  }
  _setPage(page) {
    if (!PAGES.includes(page)) return;
    this._page = page;
    for (const key of PAGES) {
      this.$(`#page-${key}`).hidden = key !== page;
      const tab = this.$(`[data-nav="${key}"]`);
      if (key === page) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    }
    this.$("#page-choice").value = page;
    // No backend call: switching pages never stops or restarts the controller.
  }

  _build() {
    // Static templates and trusted local onboarding labels use innerHTML. Entity names and server text use textContent.
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block; height: 100%; overflow: auto;
          background: var(--primary-background-color, #f4f6f8);
          color: var(--primary-text-color, #182830);
          font: 15px/1.5 var(--paper-font-body1_-_font-family, system-ui, sans-serif);
          --accent: var(--primary-color, #16786d);
          --rrh-sage: #A9D8B8;
          --rrh-sky: #C1D7F5;
          --rrh-gold: #F6D98D;
          --line: var(--divider-color, #dce4e6);
          --surface: var(--card-background-color, #fff);
          --subtle: var(--secondary-background-color, #eef3f4);
          --muted: var(--secondary-text-color, #60717b);
        }
        *, *::before, *::after { box-sizing: border-box; }
        main { max-width: 1240px; padding: 24px 24px 36px; margin: auto; }
        h1, h2, h3, p, dl, dd { margin: 0; }
        h1 { font-size: 25px; line-height: 1.2; letter-spacing: -.5px; }
        h2 { font-size: 17px; line-height: 1.4; }
        h3 { font-size: 17px; line-height: 1.4; overflow-wrap: anywhere; }
        small, .muted { color: var(--muted); }
        .card {
          min-width: 0; background: var(--surface); border: 1px solid var(--line);
          border-radius: 16px; padding: 20px;
          box-shadow: var(--ha-card-box-shadow, 0 2px 5px rgba(15, 35, 45, .025));
        }
        .app-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
        .brand { flex: 0 0 54px; width: 54px; height: 54px; object-fit: cover;
          display: block; border-radius: 13px; background: transparent; }
        .heading { flex: 1; min-width: 0; }
        .eyebrow { font-size: 10px; font-weight: 750; letter-spacing: 1.4px;
          text-transform: uppercase; margin-bottom: 5px; }
        .brand-tagline { font-weight:700; font-size:clamp(13px,1.6vw,18px); color:var(--primary-text-color, #182830); margin-top:3px; }
        .brand-subline { font-size:12px; color:var(--muted); margin-top:2px; }
        .demo-toggle { min-width:150px; font-size:12px; }
        .demo-active { border-left:4px solid #b88718; }
        .demo-slider { width:100%; accent-color:var(--accent); }
        .version { white-space: nowrap; font-size: 12px; border: 1px solid var(--line);
          border-radius: 20px; padding: 4px 10px; }
        button, input, select, textarea { font: inherit; }
        button { min-height: 44px; min-width: 44px; border: 1px solid var(--line);
          background: var(--surface); color: inherit; border-radius: 10px;
          padding: 9px 14px; cursor: pointer; font-weight: 600; }
        button:hover:not(:disabled) { border-color: var(--rrh-sage); }
        button.primary:hover:not(:disabled) { box-shadow:0 0 0 2px var(--rrh-gold); }
        button:disabled { opacity: .45; cursor: not-allowed; }
        button.primary { background: var(--accent); color: var(--text-primary-color, #fff); border-color: var(--accent); }
        button.pause { border: 2px solid var(--accent); }
        button.danger { color: var(--error-color, #b64040); }
        button:focus-visible, input:focus-visible, select:focus-visible, summary:focus-visible {
          outline: 3px solid var(--accent); outline-offset: 3px;
        }
        .page-nav { margin-bottom: 14px; padding: 8px; }
        .nav-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
        .nav-tabs button { border: 0; background: transparent; min-width: 0; padding: 9px 14px; }
        .nav-tabs button[aria-current="page"] { color: var(--accent); background: var(--subtle); }
        .nav-mobile { display: none; align-items: center; gap: 10px; font-weight: 650; }
        .nav-mobile select { flex: 1; min-width: 0; padding: 10px 12px; border: 1px solid var(--line); border-radius: 9px; background: var(--surface); color: inherit; }
        .page > .section:first-child { margin-top: 0; }
        .pipeline { display: grid; grid-template-columns: repeat(auto-fit,minmax(min(100%,210px),1fr)); gap: 12px; margin-top: 12px; align-items: start; }
        .pipe-card { display: flex; align-items: flex-start; gap: 10px; padding: 13px; }
        .pipe-card .consumer-icon { flex-shrink: 0; }
        .pipe-card .pipe-detail { min-width: 0; flex: 1; overflow-wrap: anywhere; }
        .pipe-card .pipe-detail strong { display: block; font-size: 13px; }
        .pipe-card .pipe-detail small { display: block; font-size: 11px; }
        .pipe-card.pipe-on { border-color: var(--success-color, #1b9c6a); }
        .pipe-card.pipe-next { outline: 2px solid var(--accent); }
        .emergency-button { border: 2px solid var(--error-color, #b64040); background: var(--error-color, #b64040); color: #fff; }
        .emergency-button:disabled { opacity: .7; }
        .operation-action { display:flex; align-items:center; gap:4px; flex:1 1 200px; min-width:0; }
        .operation-action > button:not(.info-button) { flex:1; min-width:0; overflow-wrap:anywhere; }
        .info-wrap { display:inline-flex; position:relative; vertical-align:middle; margin-left:6px; flex:none; }
        .info-button { display:inline-grid; place-items:center; border:1px solid var(--muted); border-radius:50%;
          width:24px; height:24px; min-width:24px; min-height:24px; padding:0; font-size:10px;
          line-height:1; font-weight:750; font-style:normal; color:var(--muted); background:transparent; border:0; position:relative; }
        .info-button::before { content:""; border:1px solid currentColor; width:16px; height:16px;
          border-radius:50%; position:absolute; inset:4px; pointer-events:none; }
        .info-button:focus-visible { outline:3px solid var(--accent); outline-offset:2px; }
        .info-popover { display:none; position:absolute; left:0; top:calc(100% + 6px); z-index:50;
          width:max-content; max-width:min(270px, calc(100vw - 48px)); padding:9px 11px;
          border:1px solid var(--line); border-radius:9px; background:var(--surface);
          box-shadow:0 5px 15px rgba(0,0,0,.15); color:var(--primary-text-color, #182830);
          font-size:12px; font-weight:400; text-align:left; white-space:normal; overflow-wrap:anywhere; }
        .info-wrap:hover > .info-popover,
        .info-wrap:focus-within > .info-popover,
        .info-wrap.open > .info-popover { display:block; }
        .operation-action .info-wrap { margin-left:0; }
        .operation-action .info-popover { left:auto; right:0; }
        .metric-title .info-wrap, h2 .info-wrap { margin-left:8px; }
        .notice .info-wrap { margin-left:10px; }
        .settings-summary strong .info-wrap { margin-left:8px; }
        .operation-card .buttons { flex:1; justify-content:flex-end; }
        .operation-card .buttons .info-button { padding:0; }
        .notice { font-size: 12px; padding: 12px 16px; border-left: 4px solid var(--accent); margin-bottom: 16px; }
        .overview-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .operation-card { grid-column: 1 / -1; }
        .toolbar, .section-title, .operation-title { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .toolbar, .section-title { justify-content: space-between; }
        .buttons { display: flex; gap: 8px; flex-wrap: wrap; }
        .badge { font-weight: 650; font-size: 13px; display: inline-flex; align-items: center;
          gap: 8px; background: var(--subtle); border-radius: 20px; padding: 5px 10px; }
        .dot { height: 8px; width: 8px; background: #7c8b92; border-radius: 50%; }
        .running .dot { background: var(--success-color, #1b9c6a); }
        .error .dot { background: var(--error-color, #c54d44); }
        .reason { font-size: 14px; margin-top: 14px; overflow-wrap: anywhere; }
        .last-action { font-size: 12px; margin-top: 8px; }
        .last-action:empty, .form-error:empty { display: none; }
        .metric-card { display: flex; flex-direction: column; gap: 8px; }
        .metric-title { font-size: 12px; font-weight: 600; color: var(--muted); }
        .metric-number { font-size: 31px; line-height: 1.2; font-weight: 700;
          font-variant-numeric: tabular-nums; letter-spacing: -.6px; overflow-wrap: anywhere; }
        .candidate { font-size: 23px; line-height: 1.3; }
        .metric-sub { font-size: 12px; overflow-wrap: anywhere; }
        .card-foot { border-top: 1px solid var(--line); padding-top: 10px; margin-top: auto; }
        .source-line { font-size: 11px; overflow-wrap: anywhere; }
        .alert { color: var(--error-color, #b64040); border-left: 4px solid currentColor;
          margin-bottom: 14px; white-space: pre-wrap; overflow-wrap: anywhere; }
        .hidden, [hidden] { display: none !important; }
        .section { margin-top: 20px; }
        .section-bar { margin-bottom: 12px; padding: 16px 20px; }
        .section-copy { min-width: 0; flex: 1; }
        .note { font-size: 12px; margin-top: 4px; }
        .consumers { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
        .consumer { display: flex; flex-direction: column; gap: 10px; }
        .consumer.is-next { border-color: var(--accent); }
        .consumer-head { display: flex; gap: 10px; align-items: flex-start; }
        .consumer-title { flex: 1; min-width: 0; }
        .consumer-icon { flex: 0 0 38px; height: 38px; width: 38px; display: grid; place-items: center;
          border-radius: 10px; background: var(--subtle); color: var(--accent); font-size: 22px; overflow: hidden; }
        .consumer-icon img { display: block; width: 30px; height: 30px; object-fit: contain; }
        .consumer-icon ha-icon { --mdc-icon-size: 25px; }
        .consumer-icon ha-icon:not(:defined) { display: none; }
        .consumer-icon ha-icon:defined + .icon-fallback { display: none; }
        #dashboard-pipeline, #profiles-list { display: grid; gap: 16px; }
        .profile-card { display: grid; gap: 13px; background:var(--subtle); }
        .pipeline-shell { padding:18px; }
        .pipeline-shell > h2 { font-size:17px; margin-bottom:14px; }
        .pipeline-shell > #dashboard-pipeline { display:grid; gap:12px; }
        .pipeline-shell .profile-card { background:var(--surface); border-color:var(--line); }
        .profile-card .pipe-card { background:var(--surface); border:1px solid var(--line); }
        .pipeline-shell .profile-card .pipe-card { background:var(--subtle); }
        /* More-specific nested-card backgrounds must not erase state borders. */
        .profile-card .pipe-card.pipe-on, .pipeline-shell .profile-card .pipe-card.pipe-on {
          border-color:var(--success-color, #1b9c6a); border-width:2px;
        }
        .strategy-fields { display:grid; gap:10px; padding:10px; border-radius:9px; background:var(--subtle); }
        .strategy-help { font-size:12px; color:var(--muted); }

        .profile-card.is-inactive { border-style: dashed; }
        .profile-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
        .profile-heading > div:first-child { min-width: 0; }
        .profile-heading h3 { display: inline; margin-right: 10px; }
        .profile-meta { color: var(--muted); font-size: 12px; }
        .profile-controls { display: flex; gap: 6px; flex-wrap: wrap; }
        .profile-controls button { font-size: 12px; }
        .profile-members { display: grid; gap: 6px; max-height: 48vh; overflow-y: auto; }
        .member-row { display: flex; align-items: center; gap: 8px; border: 1px solid var(--line); border-radius: 10px; padding: 7px 10px; }
        .member-row label { flex: 1; min-width: 0; }
        .member-row small { display: block; font-weight: 400; }
        .member-row button { min-width: 36px; min-height: 36px; padding: 4px; }
        .icon-preview { display: flex; align-items: center; gap: 10px; padding: 6px 0; }
        .chip { border-radius: 6px; background: var(--subtle); font-size: 11px; padding: 3px 7px; }
        .next-chip { display: inline-block; margin-top: 6px; color: var(--accent); font-weight: 650; }
        .consumer-state { font-size: 12px; font-weight: 600; overflow-wrap: anywhere; }
        .consumer-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .consumer-facts > div { min-width: 0; }
        dt { font-size: 11px; color: var(--muted); }
        dd { margin-top: 3px; font-size: 18px; font-weight: 650; overflow-wrap: anywhere; }
        dd.participation-value { font-size: 14px; padding-top: 3px; }
        .consumer-entity { font-size: 11px; overflow-wrap: anywhere; }
        .consumer-warning { font-size: 12px; overflow-wrap: anywhere; color: var(--error-color, #b64040); }
        .timer-line { display: flex; flex-wrap: nowrap; gap: 6px; align-items: center; }
        .timer-skip { padding: 3px 7px; min-width: 36px; min-height: 36px; font-size: 12px; flex-shrink: 0; }
        .timer-line { width: fit-content; max-width: 100%; }
        .timer-chip { min-width: 0; max-width: 100%; }
        .condition-alert { font-size:12px; overflow-wrap:anywhere; color:var(--error-color, #b64040); }
        .condition-status { display:block; min-width:0; font-size:12px; }
        .condition-status summary { display:flex; align-items:center; justify-content:flex-start; gap:6px;
          cursor:pointer; min-height:28px; font-weight:650; color:var(--success-color, #238453); }
        .condition-status.is-blocked summary { color:var(--error-color, #b64040); }
        .condition-status summary::after { content:none; }
        .condition-status .info-bubble { display:inline-grid; place-items:center; width:18px; height:18px;
          min-width:18px; border:1px solid currentColor; border-radius:50%; font-size:11px;
          font-weight:700; line-height:1; }
        .condition-details { margin:4px 0 6px; padding:10px; font-weight:400; font-size:11px;
          color:var(--primary-text-color, #182830); border:1px solid var(--line);
          border-radius:8px; background:var(--subtle); overflow-wrap:anywhere; }
        .condition-details .condition-check { margin-top:4px; }
        .condition-details .condition-check:first-child { margin-top:0; }
        .condition-check.failed { color:var(--error-color, #b64040); }
        .condition-summary-extra { font-weight:600; }
        .condition-edit { display: grid; gap: 10px; border: 1px solid var(--line); border-radius: 12px; padding: 12px; }
        .condition-list { display: grid; gap: 10px; }
        .condition-row { border: 1px solid var(--line); border-radius: 10px; padding: 10px; display: grid; gap: 8px; }
        .condition-grid { display: grid; grid-template-columns: minmax(0,1.5fr) repeat(3,minmax(0,1fr)); gap: 8px; }
        .condition-grid label { font-size: 12px; min-width: 0; }
        .condition-grid input,.condition-grid select { min-width: 0; }
        .condition-row > button { justify-self: start; min-height: 36px; }
        @media (max-width: 540px) { .condition-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }

        .profile-active-label { color: var(--success-color, #2eaf63); font-weight: 700; }
        .profile-inactive-label { color: var(--error-color, #e15757); font-weight: 700; }
        .timer-chip { font-size: 12px; padding: 6px 9px; background: var(--card-background-color, var(--subtle)); color: var(--primary-text-color, inherit); border: 1px solid var(--divider-color, var(--line)); border-radius: 8px; overflow-wrap: anywhere; }
        .time-controls { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 8px; }
        .time-group { display: grid; gap: 10px; padding: 12px; border: 1px solid var(--line); border-radius: 10px; }
        .time-group[hidden] { display:none; }
        .time-group label { font-size: 12px; }
        .consumer-controls { margin-top: auto; border-top: 1px solid var(--line); padding-top: 10px;
          display: grid; gap: 8px; }
        .participation-controls { display: flex; gap: 6px; }
        .participation-controls > button:first-child { flex: 1; }
        .consumer-controls button { font-size: 12px; padding: 8px 10px; }
        .edit-controls { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .empty { grid-column: 1 / -1; text-align: center; padding: 28px; border-style: dashed; }
        .settings-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; align-items: stretch; }
        .settings-grid > .settings-card { height:100%; min-width:0; }
        details summary { list-style: none; cursor: pointer; min-height: 50px;
          display: flex; align-items: center; gap: 12px; }
        details summary::-webkit-details-marker { display: none; }
        details summary::after { content: '+'; font-size: 22px; flex: 0 0 24px; text-align: center; color: var(--muted); margin-left: auto; }
        details[open] summary::after { content: '−'; }
        .settings-summary { min-width: 0; flex: 1; }
        .settings-summary strong { display: block; font-size: 14px; }
        .settings-summary small { display: block; font-size: 11px; margin-top: 3px; overflow-wrap: anywhere; }
        .settings-fields { display: grid; gap: 16px; padding-top: 18px; border-top: 1px solid var(--line); margin-top: 16px; }
        label { display: block; min-width: 0; font-size: 13px; font-weight: 600; }
        input, select, textarea { display: block; width: 100%; max-width: 100%; margin-top: 6px;
          border: 1px solid var(--line); border-radius: 8px; min-height: 45px;
          padding: 10px; color: inherit; background: var(--surface); }
        input:disabled, select:disabled { opacity: .6; }
        .help { font-size: 12px; margin-top: 5px; font-weight: 400; color: var(--muted); }
        .field-help { position:relative; min-width:0; }
        .field-help > label { padding-right:28px; display:block; }
        .field-help > label > input, .field-help > label > select {
          width:calc(100% + 28px); max-width:calc(100% + 28px);
        }
        .field-help > .info-wrap { position:absolute; right:0; top:0; }
        .has-help { position:relative; }
        .has-help > .info-wrap { position:absolute; right:10px; top:10px; }
        .condition-edit.has-help > .check { padding-right:30px; }
        .time-group.has-help { padding-top:26px; }
        .form-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .settings-actions { margin-top: 12px; padding: 16px 20px; }
        #settings-hint { font-size: 12px; }
        .check { display: flex; align-items: flex-start; gap: 10px; font-weight: 400; }
        .check input { width: 20px; min-height: 20px; margin: 1px 0 0; flex-shrink: 0; }
        .check span { flex: 1; min-width: 0; }
        .form-error { font-size: 13px; color: var(--error-color, #b64040); margin-top: 10px; white-space: pre-wrap; overflow-wrap: anywhere; }
        footer.card { margin-top: 16px; font-size: 11px; text-align: center; padding: 12px 16px; }
        dialog { border: 1px solid var(--line); border-radius: 16px; padding: 24px;
          width: min(580px, calc(100vw - 24px)); max-height: 90vh; overflow: auto;
          background: var(--surface); color: var(--primary-text-color, #182830); }
        dialog::backdrop { background: rgba(0, 0, 0, .4); }
        dialog .section-title { margin-bottom: 22px; }
        dialog form { display: grid; gap: 16px; }
        dialog .form-actions { margin-top: 4px; }
        /* Fixed three-column slots: the final row keeps its empty positions. */
        .consumers { grid-template-columns: repeat(3,minmax(0,1fr)); align-items: stretch; }
        .consumers > .consumer { height:100%; }
        .page { container-type: inline-size; }
        @container (max-width: 900px) { .consumers { grid-template-columns: repeat(2,minmax(0,1fr)); } }
        @container (max-width: 610px) { .consumers { grid-template-columns: minmax(0,1fr); } }
        @media (max-width: 900px) { .consumers { grid-template-columns: repeat(2,minmax(0,1fr)); } }
        @media (max-width: 610px) { .consumers { grid-template-columns: minmax(0,1fr); } }
        .overview-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 245px), 1fr)); }
        .settings-grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }
        @media (max-width: 760px) {
          .nav-tabs { display: none; }
          .nav-mobile { display: flex; }
        }
        @media (max-width: 700px) {
          main { padding: 12px 12px 28px; }
          .app-header { gap: 8px; padding: 14px 12px; }
          h1 { font-size: 21px; }
          .eyebrow { font-size: 9px; letter-spacing: .7px; }
          .brand { display: block; flex-basis: 42px; width: 42px; height: 42px; border-radius: 10px; }
          .version { font-size: 10px; padding: 4px 7px; }
          .card { padding: 16px; }
          .notice { padding: 12px 14px; }
          .overview-grid, .consumers, .settings-grid { gap: 12px; }
          .toolbar { align-items: flex-start; }
          .operation-card .toolbar { display:grid; gap:12px; }
          .operation-card .buttons { width:100%; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:6px; }
          .operation-card .operation-action { min-width:0; gap:4px; }
          .operation-card .operation-action > button:not(.info-button) { min-height:45px; padding:8px 4px; font-size:12px; }
          .operation-card .operation-action .info-button { width:24px; height:24px; min-width:24px; min-height:24px; }
          .metric-number { font-size: 28px; }
          .candidate { font-size: 23px; }
          .section-title { gap: 10px; }
          .section-bar #add { width: 100%; font-size: 13px; }
          .settings-actions .form-actions > button { flex: 1 1 180px; }
          .settings-actions #settings-hint { width: 100%; }
          dialog { padding: 18px; }
          footer.card { padding: 12px; }
        }
        @media (max-width: 370px) {
          .app-header { flex-wrap: wrap; }
          .version { margin-left: auto; }
          h1 { font-size: 19px; }
          .eyebrow { letter-spacing: 0; }
        }
        .rrh-stat-card .metric-number { font-size: clamp(1.35rem,2.2vw,2rem); overflow-wrap: anywhere; }
        .chart-card { grid-column: 1 / -1; min-height:0; }
        .chart-card svg { overflow:visible; }
        .chart-card #rrh-live-chart { overflow:hidden; padding:4px 0; min-height:0; }
        .strategy-panel { border:1px solid var(--line); border-radius:12px; padding:16px; display:grid; gap:12px; min-width:0; }
        .strategy-panel legend { font-size:13px; padding:0 8px; font-weight:700; }
        .icon-gallery { display:grid;grid-template-columns:repeat(auto-fill,minmax(51px,1fr));gap:8px;margin:6px 0 12px; }
        .icon-choice { display:grid; place-items:center; min-width:44px; min-height:51px; padding:8px; }
        .icon-choice[aria-pressed="true"] { border:2px solid var(--rrh-sage);background:var(--subtle);box-shadow:inset 0 0 0 1px var(--rrh-gold); }
        .icon-choice ha-icon { --mdc-icon-size:28px; }
        .consumers > .consumer { border-color: color-mix(in srgb, var(--rrh-sage) 28%, var(--line)); }
        .participants-panel { border:1px solid var(--line); border-radius:12px; padding:14px; min-width:0; }
        .participants-panel legend { font-size:13px; padding:0 8px; font-weight:700; }
        .energy-edit-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
        .energy-edit-grid > p { grid-column:1 / -1; }
        .energy-edit-grid > label { min-width:0; padding:11px; border:1px solid var(--line); border-radius:10px; background:var(--subtle); }
        .energy-edit-grid > label input,.energy-edit-grid > label select { background:var(--surface); }
        @container (max-width:720px) { .energy-edit-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
        @media (max-width:760px) { .energy-edit-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
        @media (max-width:520px) { .energy-edit-grid { grid-template-columns:minmax(0,1fr); } }
        .settings-danger { margin-top:14px; border-color:color-mix(in srgb, var(--error-color, #b64040) 35%, var(--line)); }
        .about-maker { font-weight:800; font-size:21px; color:var(--primary-text-color, #182830); }
        .about-handle { font-size:12px; color:var(--muted); margin-top:0; }
        .about-links { display:flex;flex-wrap:wrap;gap:9px; margin:12px 0; }
        .about-links a,.donation-link { color:var(--primary-color, #16786d); text-decoration:underline; text-underline-offset:3px; }
        .about-links a { border:1px solid var(--line);border-radius:9px;padding:8px 12px;min-height:42px; }
        .donation-link { display:inline-block; font-size:11px; margin-top:8px; }
        #donation-wrap[hidden] {display:none!important}
        #donation-info .info-wrap {margin-left:6px}
        .welcome-choices {display:grid;gap:10px;margin:20px 0}
        .welcome-choice {width:100%;display:grid;gap:6px;text-align:left;min-height:64px;padding:14px;border:1px solid var(--line);border-radius:11px;background:var(--card-background-color,var(--subtle));color:var(--primary-text-color,inherit);cursor:pointer}
        .welcome-choice strong {font-size:14px}
        .welcome-choice small {font-size:12px;opacity:.85}
        .welcome-choice:hover,.welcome-choice:focus-visible {border-color:var(--accent)}
        .icon-choice ha-icon { color:var(--accent); }
        .settings-tools { display:flex;flex-wrap:wrap;gap:10px;align-items:center; }
        #energy-form { margin-top:16px; }
        #energy-form details { border:none; padding:0; box-shadow:none; }
        .wizard-step[hidden],.wizard-steps[hidden] { display:none !important; }
        .wizard-step { display:grid; gap:12px; }
        .wizard-step label { font-size:13px; }
        .wizard-steps { font-size:12px; color:var(--muted); }
        #setup-wizard { width:min(750px,calc(100vw - 24px)); }
        .wizard-load { display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr) auto;gap:8px;align-items:end;margin:10px 0; }
        .wizard-load button { min-width:44px; }
        .safety-copy p { margin:8px 0; }
        @media(max-width:620px) { .wizard-load { grid-template-columns:repeat(2,minmax(0,1fr)); } }
        #rrh-live-chart svg, #energy-chart svg { display:block; width:100%; max-height:240px; }
        #rrh-live-chart svg { max-height:92px; }
        #rrh-live-chart { min-height:0; display:grid; align-items:center; }
        .energy-details { margin-top:12px; }
        .energy-details > summary { font-weight:700; cursor:pointer; padding:2px; }
        .energy-details > div { margin-top:14px; }
        .energy-caveat { font-size:.84rem; margin:12px 3px; }
        .stats-grid { display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px; }
        .stats-box { background:var(--subtle);padding:14px;border-radius:12px;min-width:0; }
        .stats-box strong { display:block;font-size:1.1rem;overflow-wrap:anywhere; }
        #page-howto article.card, #page-about article.card { overflow-wrap: anywhere; }
        .stats-box small { display:block;font-size:.82rem;overflow-wrap:anywhere; }
        .stats-table { width:100%;border-collapse:collapse;font-size:.91rem; }
        .stats-table td,.stats-table th { padding:8px;border-bottom:1px solid var(--line);text-align:start; }
        .stats-table td:not(:first-child),.stats-table th:not(:first-child) { text-align:end; }
        #energy-devices,#energy-days { overflow-x:auto; }
        .stats-checkboxes { display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:8px; }
        #energy-settings .settings-fields label { display:grid;gap:6px; }
        #energy-settings .settings-fields select,#energy-settings .settings-fields input { width:100%;min-width:0; }
        @media(max-width:620px) { .stats-grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
      </style>
      <main>
        <header class="card app-header">
          <img class="brand" src="/round_robin_hood/brand.png?v=0.9.2" alt="" aria-hidden="true" width="54" height="54">
          <div class="heading"><h1>Round Robin Hood</h1><div class="brand-tagline">Power your home. Not their profits.</div><div class="brand-subline">Less to the grid. More for the little guy.</div></div>
          <span class="version">${VERSION}</span>
        </header>
        <nav class="card page-nav" aria-label="RRH Seiten">
          <div class="nav-tabs">
            <button type="button" data-nav="dashboard">Dashboard</button>
            <button type="button" data-nav="consumers">Verbraucher</button>
            <button type="button" data-nav="profiles">Profile</button>
            <button type="button" data-nav="energy">Energie & Kosten</button>
            <button type="button" data-nav="settings">Einstellungen</button>
            <button type="button" data-nav="howto">Anleitung</button>
            <button type="button" data-nav="about">Über</button>
          </div>
          <label class="nav-mobile" id="page-choice-label">Seite: <select id="page-choice" aria-label="RRH Seite wählen">
            <option value="dashboard">Dashboard</option><option value="consumers">Verbraucher</option>
            <option value="profiles">Profile</option><option value="energy">Energie & Kosten</option>
            <option value="settings">Einstellungen</option><option value="howto">Anleitung</option><option value="about">Über</option>
          </select></label>
        </nav>
        <div id="connection-error" class="card alert" role="alert" hidden></div>
        <div id="command-error" class="card alert" role="alert" hidden></div>
        <section class="page" id="page-dashboard">
        <section class="card demo-active" id="demo-controls" hidden style="margin-bottom:14px">
          <div class="toolbar"><h2>DEMO · Unabhängige Simulation</h2><strong id="demo-power-label">1.600 W</strong></div>
          <label for="demo-power">Simulierte PV-Leistung vor Abzug der sechs virtuellen Verbraucher</label>
          <input id="demo-power" class="demo-slider" type="range" min="0" max="6000" step="50" value="1600">
          <small>Keine HA-Geräte oder Live-Profile werden im Demo-Modus geschaltet oder verändert.</small>
        </section>
        <section class="overview-grid" aria-label="Betrieb und Live-Status">
          <article class="card operation-card" aria-labelledby="operation-heading">
            <div class="toolbar">
              <div class="operation-title"><h2 id="operation-heading" data-i18n="mode">Betrieb</h2><div id="mode" class="badge"><span class="dot" aria-hidden="true"></span><span id="mode-text">Verbinden…</span></div></div>
              <div class="buttons"><button id="activate" class="primary" data-i18n="on" disabled>RRH EIN</button><button id="main-off" class="emergency-button" data-i18n="off" disabled>AUS · Alle abschalten</button><button id="pause" class="pause" data-i18n="pause" disabled>Pausieren (ohne Ausschalten)</button></div>
            </div>
            <p class="reason" id="reason" aria-live="polite">Status wird geladen.</p>
            <p class="last-action muted" id="last-action"></p>
            <p class="form-error" id="incomplete"></p>
          </article>
          <article class="card metric-card" id="grid-card" aria-labelledby="grid-title">
            <h2 class="metric-title" id="grid-title"><span id="grid-title-label">Netzleistung / Bezug</span></h2>
            <div class="metric-number" id="export">—</div>
            <p class="metric-sub muted" id="direction">Positiv = Einspeisung</p>
            <p class="form-error" id="source-error"></p>
            <div class="card-foot"><p class="source-line muted" id="source">Keine Netzquelle ausgewählt</p></div>
          </article>
          <article class="card metric-card" id="budget-card" aria-labelledby="budget-title">
            <h2 class="metric-title" id="budget-title" data-i18n="budget">Zusätzlich verfügbar</h2>
            <div class="metric-number" id="available">—</div>
            <p class="metric-sub muted" id="reserve"></p>
            <p class="card-foot metric-sub muted"><strong id="total-usable-label">Gesamtbudget: <span id="total-usable">—</span></strong></p>
          </article>
          <article class="card metric-card" id="managed-card"><h2 class="metric-title" id="managed-title" data-i18n="managed">Geschätzte verwaltete Leistung</h2><div class="metric-number" id="managed">—</div></article>
          <article class="card metric-card rrh-stat-card" id="rate-card"><h2 class="metric-title" data-i18n="rate">Netto-Vorteil jetzt</h2><div class="metric-number" id="rrh-live-eur-min">—</div><p class="metric-sub muted" id="rrh-live-price-hint"></p></article>
          <article class="card metric-card rrh-stat-card" id="total-net-card"><h2 class="metric-title" data-i18n="total_net">Bisheriger Netto-Vorteil</h2><div class="metric-number" id="rrh-total-eur">—</div><div id="donation-wrap"><a id="donation-link" class="donation-link" href="https://www.tipeeestream.com/satisfriedyt/donation" rel="noopener noreferrer" target="_blank" data-release-i18n="donation">Gib einen Drink aus</a><span id="donation-info"></span></div></article>
          <article class="card metric-card rrh-stat-card" id="total-energy-card"><h2 class="metric-title" data-i18n="total_energy">Von RRH genutzter Überschuss</h2><div class="metric-number" id="rrh-total-kwh">—</div></article>
          <article class="card metric-card rrh-stat-card" id="capture-card"><h2 class="metric-title" data-i18n="capture">Überschuss-Nutzungsquote</h2><div class="metric-number" id="rrh-capture">—</div></article>
          <article class="card metric-card rrh-stat-card" id="pv-power-card"><h2 class="metric-title" data-i18n="pv_power">PV-Leistung</h2><div class="metric-number" id="rrh-pv-power">—</div><p class="metric-sub muted" id="rrh-pv-capacity"></p></article>
          <article class="card metric-card rrh-stat-card chart-card" id="live-chart-card"><h2 class="metric-title" data-i18n="live_chart">Live-Effizienz</h2><div id="rrh-live-chart" role="img" aria-label="Live efficiency chart"></div><p class="muted metric-sub" id="rrh-chart-caption"></p></article>
        </section>
        <section class="section card pipeline-shell" aria-label="Aktuelle Reihenfolge">
          <h2 id="pipeline-title" data-i18n="pipeline">Aktuelle Vergabereihenfolge</h2>
          <div id="dashboard-pipeline"></div>
        </section>
        </section>
        <section class="page" id="page-consumers" hidden>
        <section class="section" aria-labelledby="consumers-heading">
          <div class="card section-bar section-title">
            <div class="section-copy"><h2 id="consumers-heading"><span data-i18n="consumerHeader">Verbraucher &amp; Reihenfolge</span> <span class="muted" id="consumer-count"></span></h2>
            </div>
            <button id="add" data-i18n="add">Verbraucher hinzufügen</button>
          </div>
          <div class="consumers" id="consumers"><div class="card empty muted">Verbindung wird hergestellt.</div></div>
        </section>
        </section>
        <section class="page" id="page-profiles" hidden>
          <div class="card section-bar section-title"><div class="section-copy"><h2 id="profiles-heading" data-i18n="profileInfo">Profile &amp; Priorität</h2></div><button id="add-profile">Profil erstellen</button></div>
          <div id="profiles-list"></div>
        </section>
        <section class="page" id="page-energy" hidden>
          <article class="card section-bar"><h2 id="energy-heading" data-i18n="energyInfo">Energie &amp; Kosten</h2><button type="button" id="reset-statistics" data-i18n="resetStats">Gesamtstatistik zurücksetzen</button></article>
          <p class="muted energy-caveat" data-i18n="dataCaveat">Schätzwerte aus Netzfluss und RRH.</p>
          <details class="card energy-details" open><summary data-i18n="overview">Übersicht</summary><div id="energy-overview" class="stats-grid"></div></details>
          <details class="card energy-details"><summary data-i18n="deviceStats">Verbraucher</summary><div id="energy-devices"></div></details>
          <details class="card energy-details"><summary data-i18n="dayStats">Tageswerte</summary><div id="energy-days"></div></details>
          <details class="card energy-details"><summary data-i18n="chartStats">Live-Verlauf</summary><div id="energy-chart" class="energy-full-chart"></div></details>
          <p id="energy-source-warnings" class="muted"></p>
          <form id="energy-form" class="card" aria-label="Energie- und Tarifkonfiguration">
            <p class="muted" id="energy-form-info" data-release-i18n="sensorChoose">Nur kompatible HA-Sensoren werden angezeigt.</p>
            <div class="form-actions" style="margin-top:16px"><button class="primary" id="save-energy" type="submit">Energieeinstellungen speichern</button><span id="energy-save-hint" class="muted" aria-live="polite"></span></div>
            <p id="energy-save-error" class="form-error" role="alert"></p>
          </form>
        </section>
        <section class="page" id="page-settings" hidden>
        <section class="section" id="settings" aria-labelledby="settings-heading">
          <div class="card section-bar"><h2 id="settings-heading">Einstellungen</h2></div>
          <div class="card settings-tools" style="margin-bottom:12px">
            <button id="demo-toggle" type="button" class="demo-toggle" disabled>Demo-Modus</button>
            <button type="button" id="show-wizard">Einrichtungsassistent erneut starten</button>
            <button type="button" id="show-notice">Sicherheitshinweis anzeigen</button>
            <span class="muted" id="notice-status"></span>
          </div>
          <form id="settings-form">
            <div class="settings-grid">
              <details class="card settings-card" id="source-settings">
                <summary><span class="settings-summary"><strong data-i18n="source">Netzquelle</strong><small id="source-summary">Sensor und Vorzeichen auswählen</small></span></summary>
                <div class="settings-fields">
                  <label>Netzleistung aus Home Assistant<select id="grid-entity" required></select><span class="help">Vorhandene Sensorentität mit momentaner Leistung in W oder kW. Kein Energiezähler in kWh.</span></label>
                  <label>Vorzeichen der Quelle<select id="sign"><option value="positive">Positiv = Einspeisung</option><option value="negative">Negativ = Einspeisung</option></select></label>
                  <label class="check"><input id="show-data-quality" type="checkbox"><span>Bereich „Datenqualität“ anzeigen</span></label>
                </div>
              </details>
              <details class="card settings-card" id="control-settings">
                <summary><span class="settings-summary"><strong data-i18n="control">Leistung &amp; Schaltverhalten</strong><small id="control-summary">Reserve und Abschaltverzögerung</small></span></summary>
                <div class="settings-fields">
                  <label>Leistungsreserve (W)<input id="reserve-input" type="number" required min="0" max="100000" step="any"></label>
                  <label class="check"><input id="global-delay-enabled" type="checkbox"><span>Globale Unterlastverzögerung aktivieren</span></label>
                  <label id="global-delay-fields">Globale Unterlastverzögerung (Sekunden)<input id="delay" type="number" required min="0" max="600" step="1"><span class="help">Standard für Verbraucher ohne eigene Verzögerung. Deaktiviert = sofortige Unterlastabschaltung; „AUS“ bleibt immer sofort.</span></label>
                  <label class="check"><input id="confirm-timer" type="checkbox"><span>Timer-Überspringen bestätigen</span></label>
                  <label class="check"><input id="confirm-profile" type="checkbox"><span>Profil-Deaktivierung bestätigen</span></label>

                </div>
              </details>
              <details class="card settings-card" id="startup-settings" open>
                <summary><span class="settings-summary"><strong data-release-i18n="startupTitle">Startverhalten bei HA-Neustart</strong><small data-release-i18n="startupHelp">Nur nach gültigen Messungen automatisch starten.</small></span></summary>
                <div class="settings-fields">
                  <label><span data-release-i18n="startupTitle">Startverhalten bei HA-Neustart</span><select id="startup-mode">
                    <option value="off" data-release-i18n="startupOff">Immer AUS (empfohlen)</option>
                    <option value="last" data-release-i18n="startupLast">Letzten Zustand wiederherstellen</option>
                    <option value="on" data-release-i18n="startupOn">Immer EIN</option>
                  </select></label>
                  <p class="help" data-release-i18n="startupHelp">Keine Schaltung ohne neue Messung und geprüfte Verbraucherzustände.</p>
                </div>
              </details>
              <details class="card settings-card" id="residual-settings">
                <summary><span class="settings-summary"><strong>Restüberschussverbraucher</strong><small>Nachrangige Nutzung verfügbarer PV-Leistung</small></span></summary>
                <div class="settings-fields">
                  <label>Verbraucher<select id="residual-consumer"><option value="">Keinen verwenden</option></select></label>
                  <p class="help">Nur mehrstufige oder stufenlos regelbare Verbraucher. Er erhält stets die niedrigste Priorität und kann keine normale Profilvergabe blockieren.</p>
                </div>
              </details>
              <details class="card settings-card" id="energy-settings">
                <summary><span class="settings-summary"><strong data-i18n="energySettings">Energie &amp; Kosten</strong><small data-i18n="energyHelp">Vorhandene HA-Sensoren oder feste Werte</small></span></summary>
                <div class="settings-fields energy-edit-grid">
                  <p class="muted" data-i18n="unitsNotice">PV-Nennleistung in W. Intern bleiben vorhandene kWp-Werte erhalten; Tarife pro kWh.</p>
                  <label>Währung<select id="stat-currency"><option value="EUR">EUR (€)</option><option value="CHF">CHF (Fr.)</option><option value="USD">USD ($)</option><option value="GBP">GBP (£)</option></select><span class="help">Keine automatische Umrechnung. Ein Wechsel nach bereits erfassten Geldwerten erfordert einen bewusst bestätigten Statistik-Neustart.</span></label>
                  <label><span data-i18n="pvSize">PV-Anlagengröße (W)</span><select id="stat-pv-mode"><option value="fixed" data-i18n="fixed">Fester Wert</option><option value="entity" data-i18n="entity">HA-Entität</option></select><input id="stat-pv-fixed" type="number" min="0" step="any" placeholder="z. B. 4000"><select id="stat-pv-entity"></select></label>
                  <label><span data-i18n="importPrice" id="import-price-label">Strompreis (EUR/kWh)</span><select id="stat-import-mode"><option value="fixed" data-i18n="fixed">Fester Wert</option><option value="entity" data-i18n="entity">HA-Entität</option></select><input id="stat-import-fixed" type="number" min="0" step="any" placeholder="0.30"><select id="stat-import-entity"></select></label>
                  <label><span data-i18n="feedPrice" id="feed-price-label">Einspeisevergütung (EUR/kWh)</span><select id="stat-feed-mode"><option value="fixed" data-i18n="fixed">Fester Wert</option><option value="entity" data-i18n="entity">HA-Entität</option></select><input id="stat-feed-fixed" type="number" min="0" step="any" placeholder="0.08"><select id="stat-feed-entity"></select></label>
                  <label><span data-i18n="solarPower">PV-Leistungssensor (optional)</span><select id="stat-pv-power-entity"></select></label>
                  <label><span data-i18n="solarEnergy">PV-Energiezähler (optional)</span><select id="stat-pv-energy-entity"></select></label>
                </div>
              </details>
              <details class="card settings-card" id="dashboard-settings">
                <summary><span class="settings-summary"><strong data-i18n="dashboardSettings">Dashboard-Anzeigen &amp; Sprache</strong><small>Diagramm und Karten auswählen</small></span></summary>
                <div class="settings-fields">
                  <label><span data-i18n="chartType">Live-Diagramm</span><select id="stat-chart-type"></select></label>
                  <label><span data-i18n="language">Sprache</span><select id="stat-language"></select></label>
                  <label class="check"><input type="checkbox" id="show-donation"><span data-release-i18n="donationSetting">Spendenhinweis im Dashboard anzeigen</span></label>
                  <strong data-i18n="showCards">Karten ein-/ausblenden</strong>
                  <div id="stat-card-toggles" class="stats-checkboxes"></div>
                </div>
              </details>
              <details class="card settings-card" id="freshness-settings">
                <summary><span class="settings-summary"><strong data-i18n="fresh">Datenqualität</strong><small id="freshness-summary">Zulässiges Meldungsalter</small></span></summary>
                <div class="settings-fields">
                  <label>Maximales Meldungsalter (Sekunden)<input id="max-age" type="number" required min="5" max="3600" step="1"><span class="help">Neue Meldungen zählen, auch bei gleichem Wert. Bloßes Ablesen macht eine Quelle nicht frisch.</span></label>

                </div>
              </details>
            </div>
            <div class="card settings-actions">
              <div class="form-actions"><button class="primary" id="save-settings" type="submit" data-i18n="save">Einstellungen speichern</button><button id="reset-settings" type="button" data-i18n="reset">Neu laden / verwerfen</button><span class="muted" id="settings-hint" aria-live="polite"></span></div>
              <div class="form-error" id="settings-error" role="alert"></div>
            </div>
          </form>
          <article class="card settings-danger" id="factory-reset-area">
            <h3 data-release-i18n="resetTitle">RRH vollständig zurücksetzen</h3>
            <p class="help" data-release-i18n="resetWarning">Verbraucher, Profile und Statistiken werden gelöscht; HA-Daten nicht.</p>
            <button type="button" class="danger" id="factory-reset-open" data-release-i18n="resetAction">Alle RRH-Daten löschen</button>
          </article>
        </section>
        </section>
        <section class="page" id="page-howto" hidden>
          <article class="card"><h2 data-i18n="howto">Anleitung</h2>
            <p id="howto-intro">Die RRH-Anleitung ist direkt hier verfügbar. Wähle links ein Kapitel oder nutze die Suche.</p>
            <iframe id="guide-frame" title="Round Robin Hood documentation" loading="lazy" style="width:100%;height:min(75vh,800px);min-height:450px;border:1px solid var(--line);border-radius:10px;background:#171b1c;margin-top:16px" sandbox="allow-scripts allow-same-origin" referrerpolicy="no-referrer"></iframe>
            <div class="stats-grid" style="margin-top:16px" hidden>
              <div class="stats-box"><strong>Dashboard</strong><small>Verteilung, Schaltzustände, Messwerte und Diagramme</small></div>
              <div class="stats-box"><strong>Verbraucher</strong><small>Geräte, Wattwerte, Symbole, Zeitregeln und Sicherheitsmaßnahmen</small></div>
              <div class="stats-box"><strong>Profile</strong><small>Prioritäten, Strategien und Bedingungen</small></div>
              <div class="stats-box"><strong>Energie &amp; Kosten</strong><small>Tarife, Statistik, Grenzen der Schätzung und 24-Stunden-Verlauf</small></div>
              <div class="stats-box"><strong>Einstellungen</strong><small>Quelle, Reserve, Verzögerung, Demo, Setup und Anzeige</small></div>
              <div class="stats-box"><strong>Sicherheit</strong><small>Schaltverhalten, Überhitzung, Kosten und Not-Aus</small></div>
            </div>
            <p class="help">Eine öffentliche GitHub-URL wird erst nach Veröffentlichung und Prüfung ergänzt.</p>
          </article>
        </section>
        <section class="page" id="page-about" hidden>
          <article class="card"><h2 data-i18n="about">Über</h2>
            <p class="muted" data-release-i18n="aboutMaker">Erstellt von</p>
            <div class="about-maker">Satisfried</div><div class="about-handle">Satisfried_yt</div>
            <h3 style="margin-top:18px" data-release-i18n="aboutLinks">Kanäle von Satisfried</h3>
            <div class="about-links">
              <a href="https://www.tiktok.com/@satisfried_yt" target="_blank" rel="noopener noreferrer">TikTok</a>
              <a href="https://www.youtube.com/@Satisfried_yt" target="_blank" rel="noopener noreferrer">YouTube</a>
              <a href="https://www.twitch.tv/satisfried_yt" target="_blank" rel="noopener noreferrer">Twitch</a>
              <a href="https://github.com/satisfried-yt" target="_blank" rel="noopener noreferrer">GitHub</a>
              <a href="http://satisfried.de/" target="_blank" rel="noopener noreferrer" data-release-i18n="aboutImprint">Impressum</a>
            </div>
            <h3 style="margin-top:18px" data-release-i18n="aboutVersions">Versionsinformationen</h3>
            <div class="stats-grid" style="margin:12px 0">
              <div class="stats-box"><small>Round Robin Hood</small><strong>${VERSION}</strong></div>
              <div class="stats-box"><small data-release-i18n="aboutHa">Home Assistant Core</small><strong id="ha-core-version">—</strong></div>
            </div>
            <p class="help" data-release-i18n="aboutSafety">Privates, KI-unterstützt entstandenes Projekt. Keine zertifizierte Sicherheitssteuerung.</p>
            <p class="help" data-release-i18n="aboutCopyright">Copyright (c) 2026 Satisfried. Apache-2.0-Lizenz; keine Markenrechte eingeräumt.</p>
          </article>
        </section>
        <dialog class="card" id="factory-reset-dialog" aria-labelledby="factory-reset-title">
          <h2 id="factory-reset-title" data-release-i18n="resetTitle">RRH vollständig zurücksetzen</h2>
          <p class="help" style="margin:12px 0" data-release-i18n="resetWarning">Alle RRH-Daten werden unwiderruflich gelöscht.</p>
          <label><span data-release-i18n="resetType">Zur Bestätigung RESET ROUND ROBIN HOOD eingeben</span><input id="reset-confirm-input" type="text" autocomplete="off" spellcheck="false"></label>
          <p class="form-error" id="factory-reset-error" role="alert"></p>
          <div class="form-actions"><button id="reset-cancel" type="button" data-release-i18n="resetCancel">Abbrechen</button><button class="danger" id="reset-proceed" type="button" disabled data-release-i18n="resetExecute">Alle AUS &amp; unwiderruflich löschen</button></div>
        </dialog>
        <dialog class="card" id="safety-dialog" aria-labelledby="safety-title">
          <h2 id="safety-title">Wichtige Sicherheitshinweise</h2>
          <div class="safety-copy" id="safety-copy"></div>
          <label class="check"><input type="checkbox" id="dismiss-notice"><span id="dismiss-notice-label">Verstanden, nicht wieder anzeigen</span></label>
          <p id="notice-error" class="form-error" role="alert"></p>
          <div class="form-actions"><button type="button" class="primary" id="notice-continue">Verstanden · weiter</button></div>
        </dialog>
        <dialog class="card" id="welcome-dialog" aria-labelledby="welcome-title">
          <h2 id="welcome-title" data-release-i18n="welcomeTitle">Willkommen bei Round Robin Hood</h2>
          <p data-release-i18n="welcomeLead">Wie möchtest du beginnen?</p>
          <div class="welcome-choices">
            <button type="button" class="welcome-choice" id="welcome-wizard"><strong data-release-i18n="welcomeWizard">Einrichtungsassistent starten</strong><small data-release-i18n="welcomeWizardHelp">Schritt für Schritt einrichten</small></button>
            <button type="button" class="welcome-choice" id="welcome-demo"><strong data-release-i18n="welcomeDemo">Demo-Modus ausprobieren</strong><small data-release-i18n="welcomeDemoHelp">Nur simulierte Geräte</small></button>
            <button type="button" class="welcome-choice" id="welcome-skip"><strong data-release-i18n="welcomeSkip">Einrichtung überspringen</strong><small data-release-i18n="welcomeSkipHelp">RRH bleibt AUS</small></button>
          </div>
          <p class="form-error" id="welcome-error" role="alert"></p>
        </dialog>
        <dialog class="card" id="setup-wizard" aria-labelledby="wizard-title">
          <div class="section-title"><h2 id="wizard-title">RRH einrichten</h2><button id="wizard-close" type="button" aria-label="Assistent schließen">×</button></div>
          <div class="wizard-steps" id="wizard-progress"></div>
          <form id="wizard-form" novalidate><div id="wizard-content" class="wizard-step"></div>
            <p class="form-error" id="wizard-error" role="alert"></p>
            <div class="form-actions"><button type="button" id="wizard-prev">Zurück</button><button type="button" class="primary" id="wizard-next">Weiter</button><button type="button" id="wizard-cancel">Abbrechen</button></div>
          </form>
        </dialog>
        <dialog class="card" id="editor" aria-labelledby="editor-title">
          <div class="section-title"><h2 id="editor-title">Verbraucher</h2><button id="close-editor" aria-label="Bearbeitung schließen">×</button></div>
          <form id="consumer-form">
            <label>Name<input id="consumer-name" required maxlength="80" autocomplete="off"></label>
            <label>Verbrauchertyp
              <select id="consumer-power-mode"><option value="fixed">Ein / Aus (Schalter)</option><option value="staged">Mehrstufig</option><option value="variable">Stufenlos regelbar (Watt-Sollwert)</option></select>
            </label>
            <label id="consumer-entity-label">HA-Steuerentität<select id="consumer-entity" required></select></label>
            <label id="consumer-watts-label">Nenn- oder Mindestleistung (W)<input id="consumer-watts" type="number" required min="1" max="100000" step="any"><span class="help">Planungswert, keine tatsächliche Leistungsmessung.</span></label>
            <div id="consumer-staged-fields" hidden>
              <label>Stufensteuerung über HA-Entität<select id="consumer-stage-entity"></select></label>
              <label>Leistungsstufen (eine je Zeile: Watt = HA-Wert)
                <textarea id="consumer-stage-lines" rows="4" placeholder="500=1&#10;1000=2&#10;1500=3&#10;2000=4"></textarea>
              </label>
              <label>AUS-Option (bei select-Hauptentität)<input id="consumer-off-option" maxlength="80" value="off"></label>
              <p class="help">Bei climate wird der Stufenwert mit climate.set_fan_mode gesetzt, bei select mit select.select_option. Bei einem separaten switch steuert dieser EIN/AUS. Wattwerte sind Schätzwerte und müssen am Gerät geprüft werden.</p>
            </div>
            <div id="consumer-variable-fields" hidden>
              <label>Maximale Leistung (W)<input id="consumer-max-watts" type="number" min="1" max="100000" step="any"></label>
              <label>Regelauflösung (W)<input id="consumer-power-step" type="number" min="1" max="10000" step="any" value="10"></label>
              <p class="help">Schreibt einen Watt-Sollwert über number.set_value. Gerät und Integration müssen Watt-Sollwerte unterstützen; ein HA-number-Feld für Temperatur ist ungeeignet. Ausschalten = Wert 0.</p>
            </div>
            <div id="consumer-regulation-common" hidden>
              <label>Regelhysterese / Mindeständerung (W)<input id="consumer-power-hysteresis" type="number" min="0" max="10000" step="any" value="100"></label>
              <label>Mindest-Regelintervall (s)<input id="consumer-power-interval" type="number" min="5" max="3600" step="1" value="10"></label>
            </div>
            <label class="check"><input id="consumer-enabled" type="checkbox"><span>Nimmt an der zyklischen Vergabe teil</span></label>
            <input id="consumer-icon" type="hidden" value="mdi:power-plug">
            <label id="icon-gallery-label" data-release-i18n="iconHint">Symbol auswählen</label>
            <div id="consumer-icon-gallery" class="icon-gallery" role="group" aria-labelledby="icon-gallery-label"></div>
            <div class="icon-preview" id="consumer-icon-preview"></div>
            <label>Eigenes Symbol als PNG oder WebP (maximal 48 KB)<input type="file" id="consumer-image" accept="image/png,image/webp"></label>
            <button type="button" id="consumer-image-clear">Eigenes Symbol entfernen</button>
            <label class="check"><input id="override-delay" type="checkbox"><span>Eigene Abschaltverzögerung für diesen Verbraucher</span></label>
            <label id="override-delay-fields" hidden>Abschaltverzögerung bei Unterlast (Sekunden)
              <input id="consumer-delay" type="number" min="0" max="600" step="1" value="30" required>
              <span class="help">Startet bei anhaltender Reserveunterschreitung; ersetzt für diesen Verbraucher den globalen Wert.</span>
            </label>
            <label class="check"><input id="min-enable" type="checkbox"><span>Mindestlaufzeit aktivieren</span></label>
            <div id="min-fields" class="time-group" hidden>
              <div class="time-controls">
                <label>Stunden<input id="min-h" type="number" min="0" max="24" step="1" value="0" required></label>
                <label>Minuten<input id="min-m" type="number" min="0" max="59" step="1" value="0" required></label>
                <label>Sekunden<input id="min-s" type="number" min="0" max="59" step="1" value="0" required></label>
              </div>
              <label class="check"><input id="min-strict" type="checkbox"><span>Mindestlaufzeit auch bei Leistungsdefizit erzwingen</span></label>
              <span class="help">Bei nicht erzwungener Mindestlaufzeit darf RRH bei anhaltendem Defizit früher ausschalten. Hauptschalter AUS hat immer Vorrang.</span>
            </div>
            <label class="check"><input id="cool-enable" type="checkbox"><span>Wiedereinschaltsperre aktivieren</span></label>
            <div id="cool-fields" class="time-group" hidden>
              <div class="time-controls">
                <label>Stunden<input id="cool-h" type="number" min="0" max="24" step="1" value="0" required></label>
                <label>Minuten<input id="cool-m" type="number" min="0" max="59" step="1" value="0" required></label>
                <label>Sekunden<input id="cool-s" type="number" min="0" max="59" step="1" value="0" required></label>
              </div>
              <label>Während der Sperre
                <select id="cool-mode"><option value="skip">Gesperrten Verbraucher überspringen</option><option value="wait">Auf diesen Verbraucher warten</option></select>
              </label>
              <span class="help">Startet nach jeder erkannten Ausschaltung, auch manuell oder durch Hauptschalter AUS.</span>
            </div>
            <section class="condition-edit">
              <label class="check"><input id="consumer-conditions-enable" type="checkbox"><span>Sensorbedingungen für diesen Verbraucher aktivieren</span></label>
              <div id="consumer-conditions-fields" hidden>
                <label>Mehrere Bedingungen verknüpfen<select id="consumer-conditions-logic"><option value="all">Alle müssen erfüllt sein (UND)</option><option value="any">Mindestens eine muss erfüllt sein (ODER)</option></select></label>
                <div class="condition-list" id="consumer-conditions-list"></div>
                <button type="button" id="consumer-conditions-add">+ Bedingung hinzufügen</button>
                <p class="help">Nur numerische Sensorzustände. Bei fehlendem/ungültigem Wert wird diese Bedingung gesperrt. Bei Bedingungsverlust sofort AUS, unabhängig von Mindestlaufzeit; ansonsten normale Round-Robin-Vergabe.</p>
              </div>
            </section>
            <div class="form-error" id="editor-error" role="alert"></div>
            <div class="form-actions"><button class="primary" type="submit" id="save-consumer">Speichern</button><button type="button" id="cancel-editor">Abbrechen</button></div>
          </form>
        </dialog>
        <dialog class="card" id="profile-editor" aria-labelledby="profile-editor-title">
          <div class="section-title"><h2 id="profile-editor-title">Profil bearbeiten</h2><button type="button" id="close-profile-editor" aria-label="Profil-Editor schließen">×</button></div>
          <form id="profile-form">
            <label>Profilname<input id="profile-name" required maxlength="80" autocomplete="off"></label>
            <label class="check"><input id="profile-enabled" type="checkbox"><span>Profil aktiv (nimmt am Betrieb teil)</span></label>
            <fieldset class="strategy-panel"><legend>Verteilstrategie &amp; Optimierung</legend>
            <label>Verteilstrategie<select id="profile-strategy">
                <option value="classic">Klassischer Round Robin</option>
                <option value="fair_runtime">Faire Laufzeitverteilung</option>
                <option value="fair_energy">Faire Energieverteilung</option>
                <option value="fixed_priority">Feste Priorität</option>
                <option value="maximum_efficiency">Maximale Effizienz</option>
                <option value="power_asc">Leistung aufsteigend</option>
                <option value="power_desc">Leistung absteigend</option>
                <option value="stable_operation">Stabiler Betrieb</option>
              </select></label>
            <div class="strategy-help" id="profile-strategy-help"></div>
            <div class="strategy-fields" id="profile-power-skip-fields" hidden>
              <label>Bei unzureichender Leistung
                <select id="profile-allow-power-skip">
                  <option value="false">Strikt warten (kein Überholen)</option>
                  <option value="true">Bei zu wenig Leistung überspringen</option>
                </select>
              </label>
            </div>
            <div class="strategy-fields" id="profile-fair-fields" hidden>
              <label>Fester Bewertungszeitraum<select id="profile-runtime-window">
                <option value="24h">24 Stunden</option><option value="7d">7 Tage</option>
                <option value="14d">14 Tage</option><option value="30d">30 Tage</option>
                <option value="all">Gesamt (kein automatischer Reset)</option>
              </select></label>
              <label>Früheste Rotation nach (Sekunden)<input id="profile-fair-rotation" type="number" min="60" max="86400" step="1" value="900"></label>
              <label id="profile-fair-gap-runtime-row">Mindestvorsprung für Wechsel (Sekunden)<input id="profile-fair-gap-runtime" type="number" min="1" max="86400" step="1" value="60"></label>
              <label id="profile-fair-gap-energy-row">Mindestvorsprung für Wechsel (Wh)<input id="profile-fair-gap-energy" type="number" min="0.001" max="100000" step="any" value="10"></label>
              <p class="muted" style="font-size:12px">Feste Zeiträume beginnen bei der ersten Aktivierung des Profils in dieser Fairness-Strategie (oder beim manuellen Reset) und laufen auch während einer Pause weiter. Bei Periodenende beginnt die Zählung automatisch bei 0. Nur bei aktivem RRH wächst der Wert. „Gesamt“ hat keinen automatischen Reset. Der Mindestvorsprung verhindert unnötige Wechsel.</p>
              <p id="profile-fair-period-info" class="muted" style="font-size:12px"></p>
              <button id="profile-fair-reset" type="button" class="danger" title="Setzt nur die Statistik dieser Fairness-Strategie in diesem Profil zurück. RRH muss pausiert sein.">Fairness-Statistik zurücksetzen</button>
            </div>
            <div class="strategy-fields" id="profile-efficiency-fields" hidden>
              <label>Mindestverbesserung für Austausch (W)<input id="profile-efficiency-gain" type="number" min="0" max="100000" step="any" value="200"></label>
              <label>Optimierungsintervall (Sekunden)<input id="profile-efficiency-interval" type="number" min="10" max="3600" step="1" value="60"></label>
              <label>Start-Sicherheitsabstand (W)<input id="profile-efficiency-margin" type="number" min="0" max="10000" step="any" value="50" title="Zusätzlicher Überschuss vor dem Einschalten; reduziert Pendeln durch Messschwankungen."></label>
            </div>
            </fieldset>
            <label id="profile-display-row">Reihenfolge der Karten im Dashboard
              <select id="profile-display"><option value="fixed">Feste Profilreihenfolge</option><option value="allocation">Dynamische Reihenfolge</option></select>
            </label>
            <section class="condition-edit">
              <label class="check"><input id="profile-conditions-enable" type="checkbox"><span>Sensorbedingungen für dieses Profil aktivieren</span></label>
              <div id="profile-conditions-fields" hidden>
                <label>Mehrere Bedingungen verknüpfen<select id="profile-conditions-logic"><option value="all">Alle müssen erfüllt sein (UND)</option><option value="any">Mindestens eine muss erfüllt sein (ODER)</option></select></label>
                <div class="condition-list" id="profile-conditions-list"></div>
                <button type="button" id="profile-conditions-add">+ Bedingung hinzufügen</button>
                <p class="help">Ist das Profil manuell aktiv, nimmt es nur bei erfüllten Bedingungen an der Vergabe teil. Verliert es die Freigabe, werden alle RRH-gesteuerten Profilverbraucher gemeinsam ausgeschaltet.</p>
              </div>
            </section>
            <fieldset class="participants-panel"><legend data-release-i18n="profileMembers">Teilnehmer des Profils</legend>
              <p class="help" id="profile-members-note">Verbraucher auswählen und ihre feste Grundreihenfolge festlegen.</p>
              <div class="profile-members" id="profile-members"></div>
            </fieldset>
            <div class="form-error" id="profile-error" role="alert"></div>
            <div class="form-actions"><button class="primary" type="submit" id="save-profile">Profil speichern</button><button type="button" id="cancel-profile">Abbrechen</button></div>
          </form>
        </dialog>
        <datalist id="numeric-sensors"></datalist>
      </main>`;
    // One canonical price/PV editor: its DOM node is moved, never duplicated.
    this.$("#energy-form").prepend(this.$("#energy-settings"));
    this.$("#page-energy").insertBefore(this.$("#energy-form"), this.$("#page-energy").querySelector(".energy-caveat"));
    this.$("#energy-settings").open = true;
    this.$("#energy-settings .settings-summary strong").dataset.releaseI18n = "energyConfig";
    this._built = true;
    this._setupInfo();
    // Native hover help for headings and controls; info controls remain for touch.
    const headingHelp = {
      "pipeline-title":"pipeline", "consumers-heading":"consumers", "profiles-heading":"profiles",
      "grid-title":"grid", "budget-title":"budget", "allocation-title":"candidate",
      "managed-title":"managed", "settings-heading":"settings"
    };
    for (const [id, key] of Object.entries(headingHelp)) {
      const el = this.$(`#${id}`);
      if (el) el.title = this._help(key);
    }
    this._compactFormHelp();
    this._translateStatic();
    this._setPage(this._page);
    this.$("#add").disabled = true;
    this.$("#add-profile").disabled = true;
    for (const el of this.shadowRoot.querySelectorAll("#settings-form input, #settings-form select, #save-settings, #energy-form input, #energy-form select, #save-energy")) el.disabled = true;
    this.$("#demo-toggle").onclick = async () => {
      const enable = !this._data?.demo_mode;
      if (enable && !confirm("DEMO starten? RRH muss vorher mit Alle AUS gestoppt sein. Deine echten Verbraucher und Profile werden ausgeblendet, aber unverändert gespeichert.")) return;
      if (await this._action("demo_mode", {demo_enabled:enable})) this._setPage("dashboard");
    };
    this.$("#demo-power").oninput = () => text(this.$("#demo-power-label"), watts(Number(this.$("#demo-power").value)));
    this.$("#demo-power").onchange = () => this._action("demo_power", {demo_power_w:Number(this.$("#demo-power").value)});
    this.$("#activate").onclick = () => this._action("activate");
    this.$("#main-off").onclick = () => this._action("emergency_off", {}, true);
    for (const tab of this.shadowRoot.querySelectorAll("[data-nav]")) tab.onclick = () => this._setPage(tab.dataset.nav);
    this.$("#page-choice").onchange = () => this._setPage(this.$("#page-choice").value);
    this.$("#pause").onclick = () => this._action("pause", {}, true);
    this.$("#add").onclick = () => this._edit(null);
    this.$("#add-profile").onclick = () => this._editProfile(null);
    for (const id of ["close-profile-editor", "cancel-profile"]) this.$(`#${id}`).onclick = () => this.$("#profile-editor").close();
    this.$("#profile-form").onsubmit = event => { event.preventDefault(); this._saveProfile(); };
    this.$("#profile-fair-reset").onclick = () => this._resetFairProfile();
    this.$("#profile-strategy").onchange = () => {
      // Changing strategy deliberately defaults to strict. Migrated profiles
      // retain their previous policy unless the user chooses a new strategy.
      this.$("#profile-allow-power-skip").value = "false";
      this._toggleProfileStrategy();
      this._renderProfileMembers();
    };
    // Native validation must be able to focus a field inside a collapsed card.
    this.$("#settings-form").addEventListener("invalid", event => {
      const card = event.target.closest("details");
      if (card) card.open = true;
    }, true);
    this.$("#settings-form").onsubmit = event => { event.preventDefault(); this._saveSettings(); };
    this.$("#energy-form").onsubmit = event => { event.preventDefault(); this._saveSettings(); };
    const trackEnergyEdit = event => {
      this._settingsDirty = true;
      const id=event.target.id;
      if(["stat-import-mode","stat-import-fixed","stat-import-entity"].includes(id)) this._tariffFieldsEdited.add("import");
      if(["stat-feed-mode","stat-feed-fixed","stat-feed-entity"].includes(id)) this._tariffFieldsEdited.add("feed");
      text(this.$("#energy-save-hint"),"Ungespeicherte Änderungen.");
    };
    this.$("#energy-form").oninput = trackEnergyEdit;
    this.$("#energy-form").onchange = trackEnergyEdit;
    this.$("#stat-currency").addEventListener("change",()=>{this._currencyLabels();for(const [key,kind] of [["pv","capacity"],["import","price"],["feed","price"]]){
      const el=this.$(`#stat-${key}-entity`);this._statOptions(el,el.value,kind);}});
    this.$("#settings-form").oninput = () => { this._settingsDirty = true; text(this.$("#settings-hint"), "Noch nicht gespeichert."); };
    this.$("#reset-settings").onclick = () => { this._settingsDirty = false; this._fillSettings(true); };
    this.$("#show-notice").onclick=()=>this._showNotice(true);
    this.$("#show-wizard").onclick=()=>this._openWizard(true);
    this.$("#factory-reset-open").onclick=()=>this._openFactoryReset();
    this.$("#reset-cancel").onclick=()=>this.$("#factory-reset-dialog").close();
    this.$("#reset-confirm-input").oninput=()=>{this.$("#reset-proceed").disabled=this.$("#reset-confirm-input").value !== "RESET ROUND ROBIN HOOD";};
    this.$("#reset-proceed").onclick=()=>this._factoryReset();
    this.$("#notice-continue").onclick=()=>this._confirmNotice();
    this.$("#welcome-wizard").onclick=()=>this._chooseWelcome("wizard");
    this.$("#welcome-demo").onclick=()=>this._chooseWelcome("demo");
    this.$("#welcome-skip").onclick=()=>this._chooseWelcome("skip");
    this.$("#wizard-close").onclick=this.$("#wizard-cancel").onclick=()=>this.$("#setup-wizard").close();
    this.$("#wizard-prev").onclick=()=>this._wizardMove(-1);
    this.$("#wizard-next").onclick=()=>this._wizardMove(1);
    this.$("#reset-statistics").onclick = async () => {
      if (!confirm(this._tr("resetStatsConfirm"))) return;
      await this._action("reset_statistics", {revision:this._data.revision});
    };
    for(const key of ["pv","import","feed"]) this.$(`#stat-${key}-mode`).onchange = () => this._toggleStatMode(key);
    this.$("#global-delay-enabled").onchange = () => this._toggleGlobalDelay();
    for (const id of ["close-editor", "cancel-editor"]) this.$(`#${id}`).onclick = () => this.$("#editor").close();
    this.$("#consumer-form").onsubmit = event => { event.preventDefault(); this._saveConsumer(); };
    this.$("#min-enable").onchange = () => this._toggleTimeFields();
    this.$("#cool-enable").onchange = () => this._toggleTimeFields();
    this.$("#override-delay").onchange = () => this._toggleDelayField();
    for (const prefix of ["consumer", "profile"]) {
      this.$(`#${prefix}-conditions-enable`).onchange = () => this._toggleConditions(prefix);
      this.$(`#${prefix}-conditions-add`).onclick = () => this._addConditionRule(prefix);
    }

    // No free-form MDI input: icons are selected using the accessible button grid.
    const iconNames = ["power-plug","radiator","fan","air-humidifier","air-filter","heat-wave","water","lightbulb","ev-station","washing-machine","server","solar-power","home-battery","flash"];
    const gallery=this.$("#consumer-icon-gallery");
    for(const iconName of iconNames){
      const value=`mdi:${iconName}`, button=node("button",null,"icon-choice");button.type="button";
      button.dataset.icon=value;button.setAttribute("aria-pressed","false");
      const visual=node("ha-icon");visual.setAttribute("icon",value);
      button.title=iconName.replaceAll("-"," ");
      button.setAttribute("aria-label",button.title);
      button.append(visual);
      button.onclick=()=>{this.$("#consumer-icon").value=value;this._renderIconPreview();};
      gallery.append(button);
    }
    this.$("#consumer-image-clear").onclick = () => { this._editorImage = null; this.$("#consumer-image").value = ""; this._renderIconPreview(); };
    this.$("#consumer-image").onchange = async () => {
      const file = this.$("#consumer-image").files?.[0];
      if (!file) return;
      if (!(["image/png", "image/webp"].includes(file.type)) || file.size > 48 * 1024) {
        text(this.$("#editor-error"), "Nur PNG oder WebP bis maximal 48 KB verwenden.");
        this.$("#consumer-image").value = ""; return;
      }
      const reader = new FileReader();
      reader.onload = () => { this._editorImage = String(reader.result); text(this.$("#editor-error"), ""); this._renderIconPreview(); };
      reader.onerror = () => text(this.$("#editor-error"), "Datei konnte nicht gelesen werden.");
      reader.readAsDataURL(file);
    };
    this.$("#consumer-power-mode").onchange = () => this._toggleConsumerPower();
    this.$("#consumer-entity").onchange = () => {
      this._toggleConsumerPower(false);
      if (!this.$("#consumer-name").value) this.$("#consumer-name").value = this._hass.states[this.$("#consumer-entity").value]?.attributes?.friendly_name || "";
    };
  }

  async _poll() {
    if (!this._built || !this.isConnected || this._polling || !this._hass?.callWS) return;
    clearTimeout(this._timer); this._timer = null;
    this._polling = true;
    try {
      this._accept(await this._hass.callWS({type: `${DOMAIN}/status`}));
      this.$("#connection-error").hidden = true;
    } catch (error) {
      const el = this.$("#connection-error");
      text(el, `Verbindung unterbrochen. Angezeigte Werte sind der letzte Stand. ${error.message || "Status nicht erreichbar."}`);
      el.hidden = false;
      this.$("#activate").disabled = true;
      this.$("#main-off").disabled = true;
    } finally {
      this._polling = false;
      if (this.isConnected) this._timer = setTimeout(() => { this._timer = null; this._poll(); }, 1500);
    }
  }

  _accept(data) {
    if (data.api_version !== 1 || data.version !== VERSION) throw new Error("Frontend und Backend passen nicht zusammen. Browser nach Paketupdate neu laden.");
    if (this._data && !!this._data.demo_mode !== !!data.demo_mode) {
      this._settingsRevision = null; this._settingsDirty = false; this._rowsFingerprint = "";
    }
    this._data = data;
    const configured = data.config?.dashboard?.language || "auto";
    const haLanguage = String(this._hass?.locale?.language || this._hass?.language || "de").toLowerCase();
    const nextLanguage = configured === "auto" ? (["de","en","fr","es","pt","it"].find(code=>haLanguage.startsWith(code)) || "en") : configured;
    if (this._language !== nextLanguage) { this._language=nextLanguage; if(this._built) this._translateStatic(); }
    this._render();
  }

  async _action(action, payload = {}, allowWhileBusy = false) {
    if (this._writing && !allowWhileBusy) return false;
    if (action === "emergency_off") {
      if (this._offRequested) return false;
      this._offRequested = true;
    }
    const ordinal = ++this._requestOrdinal;
    if (action === "emergency_off") this._emergencyOrdinal = ordinal;
    this._writeCount += 1;
    this._writing = true;
    this.$("#command-error").hidden = true;
    this._render();
    try {
      const result = await this._hass.callWS({type: `${DOMAIN}/command`, action, ...payload});
      if (ordinal >= this._emergencyOrdinal) this._accept(result);
      return true;
    } catch (error) {
      const el = this.$("#command-error");
      text(el, error.message || "Vorgang fehlgeschlagen. Keine automatische Wiederholung.");
      el.hidden = false;
      return false;
    } finally {
      if (action === "emergency_off") this._offRequested = false;
      this._writeCount -= 1;
      this._writing = this._writeCount > 0;
      this._render();
    }
  }

  _entityName(id) {
    if (!id) return "";
    return this._hass?.states?.[id]?.attributes?.friendly_name || id;
  }
  _shortWait(message) {
    const common = {
      "Wartet auf seinen Round-Robin-Turn":"Wartet auf Vergabe",
      "Bereit für die Vergabe":"Bereit",
      "Wiedereinschaltsperre läuft":"Sperre aktiv",
      "Wartet auf ausreichend Überschuss":"Wartet auf Überschuss",
      "Keinem Profil zugeordnet":"Kein Profil",
      "Profil manuell deaktiviert":"Profil deaktiviert"
    };
    return common[message] || message;
  }
  _render() {
    if (!this._data || !this._built) return;
    const d = this._data, p = d.power;
    const running = d.mode === "running", locked = running || !!d.pending || this._writing;
    const name = id => d.consumers.find(c => c.id === id)?.name;
    this.$("#demo-toggle").disabled = this._writing || !!d.pending || !!d.emergency_active || (!d.demo_mode && (running || d.emergency_unresolved));
    text(this.$("#demo-toggle"), this._tr(d.demo_mode ? "exitDemo" : "demo"));
    this.$("#demo-controls").hidden = !d.demo_mode;
    const slider = this.$("#demo-power");
    if (d.demo_mode && this.shadowRoot.activeElement !== slider) slider.value = d.demo_power_w ?? 1600;
    slider.disabled = this._writing;
    if (this.shadowRoot.activeElement !== slider) text(this.$("#demo-power-label"), watts(d.demo_power_w));
    this.$("#mode").className = `badge ${d.mode}`;
    text(this.$("#mode-text"), d.startup_pending ? this._tr("startupPending") : this._tr(d.mode === "running" ? "active" : d.mode));
    text(this.$("#activate"), this._tr("on"));
    text(this.$("#main-off"), d.emergency_active ? "AUS läuft…" : this._tr("off"));
    this.$("#activate").disabled = running || !!d.pending || this._writing || !!p.error || d.emergency_unresolved;
    this.$("#main-off").disabled = !!d.emergency_active || this._offRequested; // Main OFF overrides other busy/paused/error states.
    this.$("#pause").disabled = !running; // Pause is never blocked by a pending switch.
    this.$("#add").disabled = locked;
    this.$("#add-profile").disabled = locked;
    this.$("#show-wizard").disabled = locked || d.demo_mode;
    this.$("#factory-reset-open").disabled = this._writing || !!d.pending || !!d.emergency_active || d.demo_mode;
    this.$("#donation-wrap").hidden = d.config.dashboard?.show_donation === false;
    text(this.$("#ha-core-version"), String(this._hass?.config?.version || this._tr("aboutUnknown")));
    text(this.$("#export"), watts(p.export_w == null ? null : Math.abs(p.export_w)));
    text(this.$("#grid-title-label"), p.error ? "Letzte Netzleistung (nicht steuerbar)" :
      p.export_w == null || p.export_w === 0 ? "Netzleistung" : p.export_w > 0 ? "Netzeinspeisung" : "Netzbezug");
    text(this.$("#direction"), p.export_w == null ? "Positiv = Einspeisung" : p.export_w >= 0 ? "Einspeisung ins Netz" : "Bezug aus dem Netz");
    text(this.$("#available"), watts(p.available_w));
    text(this.$("#managed"), watts(d.managed_w));
    text(this.$("#total-usable"), watts(p.total_usable_w));
    text(this.$("#reserve"), `${watts(d.config.reserve_w)} Reserve berücksichtigt`);
    const currentProfile = d.profiles?.find(p => p.id === d.next_profile_id);
    const normalStopped = d.mode === "stopped" && !d.emergency_unresolved && !d.incomplete;
    const normalPaused = d.mode === "paused" && !d.incomplete && !d.emergency_unresolved &&
      /^(Pausiert\. Keine weiteren|Nach Start pausiert|Einstellungen gespeichert|Automatik pausiert)/.test(d.reason || "");
    text(this.$("#reason"), normalStopped ? "Betrieb gestoppt" : normalPaused ? "Betrieb pausiert" : d.reason);
    text(this.$("#consumer-count"), `(${d.consumers.length})`);
    const gridName = this._entityName(d.config.grid_entity);
    text(this.$("#source-summary"), gridName || "Keine Netzquelle ausgewählt");
    this.$("#freshness-settings").hidden = d.config.data_quality_visible === false;
    text(this.$("#control-summary"), `${watts(d.config.reserve_w)} Reserve · ${d.config.global_shutdown_delay_enabled === false ? "sofortige Abschaltung" : d.config.shutdown_delay_s + " s Verzögerung"}`);
    text(this.$("#freshness-summary"), `Maximal ${d.config.max_age_s} s · Fehlerpause bei Ausfall`);
    text(this.$("#source"), `${gridName || "Keine Netzquelle"} · ${p.raw ?? "—"} ${p.unit || ""}${d.config.data_quality_visible === false ? "" : ` · Alter: ${p.age_s == null ? "unbekannt" : `${fmt.format(p.age_s)} s`}`}`);
    this.$("#source").title = d.config.grid_entity || "";
    this.$("#grid-title").title = gridName ? `${gridName} · ${this._help("grid")}` : this._help("grid");
    text(this.$("#source-error"), p.error || "");
    text(this.$("#last-action"), d.mode === "error" || d.emergency_unresolved ? d.last_action : "");
    text(this.$("#incomplete"), d.incomplete && !d.pending ? "Letzter Auftrag unbestätigt. Bei erneuter Aktivierung wird ein unbestätigt eingeschaltetes Gerät nicht übernommen." : "");
    for (const el of this.shadowRoot.querySelectorAll("#settings-form input, #settings-form select, #save-settings, #energy-form input, #energy-form select, #save-energy")) el.disabled = locked;
    if (running) text(this.$("#settings-hint"), "Zum Bearbeiten zuerst pausieren.");
    else if (this.$("#settings-hint").textContent === "Zum Bearbeiten zuerst pausieren.") {
      text(this.$("#settings-hint"), this._settingsDirty ? "Noch nicht gespeichert." : "");
    }
    this._fillSettings();
    this._renderStats(d, locked);
    const fingerprint = JSON.stringify([d.consumers, d.profiles, d.next_id, d.demo_mode, d.residual_consumer_id, locked, !!d.pending, this._writing]);
    if (fingerprint !== this._rowsFingerprint) {
      // Timers cause regular card redraws. Do not collapse a diagnostic a user is reading.
      const areas = ["#consumers", "#dashboard-pipeline", "#profiles-list"];
      const expanded = new Map(areas.map(selector => [selector,
        new Set(Array.from(this.$(selector).querySelectorAll(".condition-status[open]"), el => el.dataset.statusKey))]));
      this._rowsFingerprint = fingerprint;
      this._renderConsumers(locked); this._renderPipeline(); this._renderProfiles(locked);
      for (const selector of areas) {
        for (const detail of this.$(selector).querySelectorAll(".condition-status")) {
          if (expanded.get(selector).has(detail.dataset.statusKey)) detail.open = true;
        }
      }
    }
    this._localizeLegacy();
    this._onboarding(d);
  }

  _onboarding(data) {
    if (!this.isConnected || !data || this.$("#safety-dialog")?.open || this.$("#setup-wizard")?.open || this.$("#welcome-dialog")?.open) return;
    const dismissed = !!data.notice_dismissed;
    text(this.$("#notice-status"), dismissed ? "Sicherheitshinweis dauerhaft ausgeblendet (jederzeit abrufbar)." : "Sicherheitshinweis beim nächsten Öffnen erneut anzeigen.");
    if (!this._noticeShownThisVisit && !dismissed) {
      this._noticeShownThisVisit = true;
      this._showNotice(false);
      return;
    }
    if (!this._wizardOfferedThisVisit && data.setup_needed && !data.demo_mode && !this._writing) {
      this._wizardOfferedThisVisit = true;
      this._showWelcome();
    }
  }

  _showWelcome() {
    if(!this._data || this.$("#welcome-dialog").open) return;
    text(this.$("#welcome-error"),"");
    this.$("#welcome-dialog").showModal();
  }

  async _chooseWelcome(choice) {
    if(this._writing || !this._data) return;
    if(choice === "wizard") {
      this.$("#welcome-dialog").close();
      this._openWizard(false);
      return;
    }
    this._wizardOfferedThisVisit=true;
    let ok=false;
    if(choice === "demo") {
      ok=await this._action("demo_mode",{demo_enabled:true});
    } else if(choice === "skip") {
      const cfg=copy(this._data.config);
      cfg.setup_complete=true; // Acknowledges onboarding; configuration can remain empty.
      ok=await this._action("configure",{config:cfg,revision:this._data.revision});
    }
    if(ok) {
      this.$("#welcome-dialog").close();
      this._setPage("dashboard");
    } else {
      text(this.$("#welcome-error"),this.$("#command-error").textContent || this._tr("welcomeError"));
      this._wizardOfferedThisVisit=false;
    }
  }

  _showNotice(manual = false) {
    if (!this._data || this.$("#setup-wizard").open) return;
    const en=this._language==="en", target=this.$("#safety-copy");
    const paragraphs=en ? [
      "Round Robin Hood is a private hobby project created primarily for its developer's own use, with AI assistance. It is not a certified safety controller.",
      "Software or sensor failures can leave consumers running, switch them incorrectly, cause unexpected electricity costs, property damage, overheating, fire or electric shock. No guaranteed safe operation or savings are promised.",
      "Place heaters and other appliances safely. Use appropriate wiring, independent thermostats and temperature cut-outs, fuses and electrical protections. Never use RRH as the only safeguard and monitor equipment on initial runs.",
      "The project does not provide a certified emergency stop. This notice does not waive statutory rights."
    ] : [
      "Round Robin Hood ist ein privates Hobbyprojekt, das sein Entwickler in erster Linie für sich selbst entwickelt – mit Unterstützung durch KI. Es ist keine zertifizierte Sicherheitssteuerung.",
      "Software-, Sensor- oder Gerätefehler können Verbraucher unbeabsichtigt weiterlaufen lassen oder falsch schalten. Dadurch sind zusätzliche Stromkosten, Sachschäden, Überhitzung, Brand oder Stromschlag möglich. Sicherer Betrieb und Ersparnisse werden nicht zugesichert.",
      "Heizlüfter und andere Geräte sicher aufstellen. Geeignete elektrische Absicherung, unabhängige Temperaturbegrenzer und weitere Schutzmaßnahmen verwenden. RRH niemals als alleinige Schutzeinrichtung benutzen. Geräte bei Inbetriebnahme überwachen.",
      "Alle AUS in RRH ist kein zertifizierter Not-Aus. Gesetzliche Ansprüche werden durch diesen Hinweis nicht ausgeschlossen."
    ];
    target.replaceChildren(...paragraphs.map(p=>node("p",p)));
    text(this.$("#safety-title"),en?"Important safety information":"Wichtige Sicherheitshinweise");
    text(this.$("#dismiss-notice-label"),en?"Understood, do not show again":"Verstanden, nicht wieder anzeigen");
    text(this.$("#notice-continue"),en?"Understood · continue":"Verstanden · weiter");
    this.$("#dismiss-notice").checked=!!this._data.notice_dismissed;
    text(this.$("#notice-error"),"");
    this._noticeShownThisVisit=true;
    this._noticeManual=manual;
    this.$("#safety-dialog").showModal();
  }

  async _confirmNotice() {
    const dismissed=this.$("#dismiss-notice").checked;
    this.$("#notice-continue").disabled=true;
    try {
      if(dismissed!==!!this._data.notice_dismissed){
        // This writes to the real persisted configuration, even in demo mode.
        const ok=await this._action("dismiss_notice",{notice_dismissed:dismissed},true);
        if(!ok){text(this.$("#notice-error"),this.$("#command-error").textContent);return;}
      }
      this.$("#safety-dialog").close();
      this._onboarding(this._data);
    } finally { this.$("#notice-continue").disabled=false; }
  }

  _openFactoryReset() {
    if (!this._data || this._data.demo_mode || this._writing || this._data.pending || this._data.emergency_active) return;
    text(this.$("#factory-reset-error"),"");
    this.$("#reset-confirm-input").value="";
    this.$("#reset-proceed").disabled=true;
    this.$("#factory-reset-dialog").showModal();
    this.$("#reset-confirm-input").focus();
  }

  async _factoryReset() {
    if (this.$("#reset-confirm-input").value !== "RESET ROUND ROBIN HOOD" || this._writing || this._data?.demo_mode) return;
    const button=this.$("#reset-proceed");button.disabled=true;
    const off=await this._action("emergency_off",{},true);
    if(!off){text(this.$("#factory-reset-error"),this.$("#command-error").textContent || this._tr("resetFailure"));return;}
    this.$("#factory-reset-dialog").close();
    // After successful storage commit the first-run safety notice and wizard
    // are shown in order, including on the same live browser session.
    this._noticeShownThisVisit=false;
    this._wizardOfferedThisVisit=false;
    const ok=await this._action("factory_reset",{revision:this._data.revision,confirmation:"RESET ROUND ROBIN HOOD"},true);
    if(!ok){this._noticeShownThisVisit=true;this._wizardOfferedThisVisit=true;}
  }

  _wizardText(de,en){
    // Keep new onboarding improvements localized alongside the six supported UI languages.
    const translations={
      "Wir richten die wichtigsten Einstellungen gemeinsam ein. Nichts wird automatisch eingeschaltet. Wähle zunächst den Netzsensor, dann Verbraucher, Strategie, Preise und Sicherheitsabstände. Fortgeschrittene Regelgeräte kannst du anschließend unter Verbraucher anlegen.":{
        fr:"Configurons ensemble le capteur réseau, les appareils, la stratégie, les tarifs et les protections. Aucun appareil ne sera activé automatiquement.",
        es:"Configuremos el sensor de red, los consumidores, la estrategia, las tarifas y los límites de seguridad. Ningún dispositivo se encenderá automáticamente.",
        pt:"Vamos configurar o sensor de rede, os consumidores, a estratégia, os preços e os limites de segurança. Nenhum dispositivo será ligado automaticamente.",
        it:"Configuriamo il sensore di rete, i dispositivi, la strategia, le tariffe e i limiti di sicurezza. Nessun dispositivo verrà acceso automaticamente."},
      "Füge einen oder mehrere Verbraucher mit eigenem Namen, HA-Steuerentität und geschätzter Leistung hinzu. Mehrstufige/stufenlose Geräte werden später in der Verbraucher-Ansicht eingerichtet. RRH bleibt AUS.":{
        fr:"Ajoutez un ou plusieurs appareils avec un nom personnalisé, une entité de commande HA et une puissance estimée. Configurez les appareils à plusieurs niveaux ou variables plus tard. RRH reste arrêté.",
        es:"Añade consumidores con nombre personalizado, entidad de control HA y potencia estimada. Configura los equipos de varios niveles o variables más adelante. RRH permanece apagado.",
        pt:"Adicione consumidores com nome próprio, entidade de controlo HA e potência estimada. Configure dispositivos de vários níveis ou variáveis mais tarde. RRH permanece desligado.",
        it:"Aggiungi dispositivi con nome personalizzato, entità di controllo HA e potenza stimata. Configura i dispositivi multilivello o variabili in seguito. RRH resta spento."},
      "HA-Steuerentität":{fr:"Entité de commande HA",es:"Entidad de control HA",pt:"Entidade de controlo HA",it:"Entità di controllo HA"},
      "+ Weiteren Verbraucher hinzufügen":{fr:"+ Ajouter un appareil",es:"+ Añadir consumidor",pt:"+ Adicionar consumidor",it:"+ Aggiungi dispositivo"},
      "Die Strategie bestimmt, wer zuerst Strom erhält. Nicht jede Strategie kann alle Geräte gleichzeitig betreiben. Details zu allen Strategien findest du unter Anleitung.":{
        fr:"La stratégie détermine les appareils prioritaires. Tous ne peuvent pas toujours fonctionner simultanément. Consultez le Guide pour les détails.",
        es:"La estrategia determina qué dispositivos reciben energía primero. No todos pueden funcionar al mismo tiempo. Consulta la Guía para más detalles.",
        pt:"A estratégia determina que dispositivos recebem energia primeiro. Nem todos podem funcionar em simultâneo. Consulte o Guia para os detalhes.",
        it:"La strategia decide quali dispositivi ricevono energia per primi. Non tutti possono funzionare contemporaneamente. Consulta la Guida per i dettagli."},
      "PV-Nennleistung und Tarife entweder als festen Wert oder aus einer HA-Entität beziehen. Ersparnisse sind Schätzungen, keine Stromrechnung.":{
        fr:"Utilisez des valeurs fixes ou des entités Home Assistant pour la capacité PV et les tarifs. Les économies sont des estimations, pas une facture.",
        es:"Usa valores fijos o entidades de Home Assistant para la potencia nominal FV y las tarifas. El ahorro es estimado, no una factura.",
        pt:"Utilize valores fixos ou entidades Home Assistant para a capacidade fotovoltaica e as tarifas. A poupança é estimada, não uma fatura.",
        it:"Usa valori fissi o entità Home Assistant per la potenza nominale FV e le tariffe. I risparmi sono stime, non una bolletta."},
      "Fester Wert":{fr:"Valeur fixe",es:"Valor fijo",pt:"Valor fixo",it:"Valore fisso"},
      "HA-Entität":{fr:"Entité HA",es:"Entidad HA",pt:"Entidade HA",it:"Entità HA"},
      "PV-Nennleistung (W, optional)":{fr:"Puissance nominale PV (W, facultatif)",es:"Potencia nominal FV (W, opcional)",pt:"Potência nominal FV (W, opcional)",it:"Potenza nominale FV (W, facoltativa)"},
      "Strombezugspreis (pro kWh)":{fr:"Prix d'achat (par kWh)",es:"Precio de compra (por kWh)",pt:"Preço de compra (por kWh)",it:"Prezzo di acquisto (per kWh)"},
      "Einspeisevergütung (pro kWh)":{fr:"Tarif d'injection (par kWh)",es:"Compensación de vertido (por kWh)",pt:"Tarifa de injeção (por kWh)",it:"Tariffa di immissione (per kWh)"},
      "Bitte eine HA-Entität auswählen.":{fr:"Sélectionnez une entité HA.",es:"Selecciona una entidad HA.",pt:"Selecione uma entidade HA.",it:"Seleziona un'entità HA."}
    };
    return translations[de]?.[this._language] ?? (this._language==="de"?de:en);
  }

  _openWizard(manual=false) {
    if(!this._data || this._data.demo_mode || this._data.mode==="running" || this._data.pending || this._writing) return;
    const existing=!!(this._data.config.grid_entity || this._data.config.consumers.length);
    if(manual && existing && !confirm(this._wizardText(
      "Den Assistenten auf einer bestehenden Konfiguration erneut öffnen? Vorhandene Verbraucher und Statistiken bleiben erhalten. Änderungen an Netzquelle, Tarif und Strategie werden erst nach Bestätigung gespeichert. RRH bleibt pausiert.",
      "Open the setup wizard on an existing configuration? Existing consumers and statistics are preserved. Changes to grid source, tariffs and strategy are only saved after review. RRH remains paused."))) return;
    this._wizardManual=manual;this._wizardRevision=this._data.revision;
    this._wizardDraft=copy(this._data.config);
    this._wizardLoads=[];
    this._wizardRateEdited=new Set();
    this._wizardStep=0;
    this._wizardOfferedThisVisit=true;
    this._wizardRender();
    this.$("#setup-wizard").showModal();
  }

  _wizardAppendLoad(load={}) {
    const row=node("div",null,"wizard-load"), entity=node("select"),name=node("input"),wattsInput=node("input"),remove=node("button","×");
    entity.className="wizard-entity";name.className="wizard-name";wattsInput.className="wizard-watts";
    entity.required=true;name.required=true;name.maxLength=80;name.placeholder=this._wizardText("Name","Name");
    wattsInput.type="number";wattsInput.min="1";wattsInput.max="100000";wattsInput.step="any";wattsInput.required=true;wattsInput.placeholder="W";
    this._options(entity,"switch",load.entity_id||"");name.value=load.name||"";wattsInput.value=load.watts??"";
    entity.onchange=()=>{ if(!name.value) name.value=this._entityName(entity.value); };
    remove.type="button";remove.title=this._wizardText("Entfernen","Remove");
    remove.onclick=()=>{this._wizardCollectLoads();this._wizardLoads.splice(Number(row.dataset.index),1);this._wizardRender();};
    row.dataset.index=String(this.$("#wizard-load-list").childElementCount);
    for (const [labelText,control] of [[this._wizardText("HA-Steuerentität","HA control entity"),entity],[this._wizardText("Name","Name"),name],[this._wizardText("Leistung (W)","Power (W)"),wattsInput]]) {
      const label=node("label",labelText);label.append(control);row.append(label);
    }
    row.append(remove);this.$("#wizard-load-list").append(row);
  }

  _wizardCollectLoads() {
    this._wizardLoads=Array.from(this.$("#wizard-load-list")?.querySelectorAll(".wizard-load")||[],row=>({
      entity_id:row.querySelector(".wizard-entity").value,
      name:row.querySelector(".wizard-name").value.trim(),
      watts:Number(row.querySelector(".wizard-watts").value)
    }));
  }

  _wizardReadStep(validate) {
    const step=this._wizardStep,d=this._wizardDraft;
    if(validate) {
      for(const input of this.$("#wizard-content").querySelectorAll("input,select")) {
        if(!input.checkValidity()){input.reportValidity();return false;}
      }
    }
    if(step===1){d.grid_entity=this.$("#wizard-grid").value;d.export_positive=this.$("#wizard-sign").value==="positive";}
    if(step===2) {
      this._wizardCollectLoads();
      if(validate && !d.consumers.length && !this._wizardLoads.length){text(this.$("#wizard-error"),this._wizardText("Bitte mindestens einen Verbraucher hinzufügen.","Add at least one consumer."));return false;}
      const all=[...d.consumers.map(c=>c.entity_id),...this._wizardLoads.map(c=>c.entity_id)];
      if(validate && new Set(all).size!==all.length){text(this.$("#wizard-error"),this._wizardText("Eine Steuerentität darf nicht doppelt vorkommen.","Control entities must be unique."));return false;}
    }
    if(step===3){d._wizardStrategy=this.$("#wizard-strategy").value;}
    if(step===4) {
      const newCurrency=this.$("#wizard-currency").value;
      if(validate && newCurrency !== (this._data?.config?.energy?.currency || "EUR") &&
        (!this._wizardRateEdited.has("buy") || !this._wizardRateEdited.has("feed") ||
         !(this.$("#wizard-buy-mode").value==="entity"?this.$("#wizard-buy-entity").value:this.$("#wizard-buy").value.trim()) || !(this.$("#wizard-feed-mode").value==="entity"?this.$("#wizard-feed-entity").value:this.$("#wizard-feed").value.trim()))) {
        text(this.$("#wizard-error"),this._wizardText("Bitte beide Tarife bewusst in der neuen Währung neu eingeben.","Re-enter both tariffs explicitly in the new currency."));
        return false;
      }
      d.energy.currency=newCurrency;
      for(const [key,source] of [["pv","pv_size"],["buy","import_price"],["feed","feed_in_price"]]) {
        const mode=this.$(`#wizard-${key}-mode`).value;
        const raw=this.$(`#wizard-${key}`).value.trim();
        const entity=this.$(`#wizard-${key}-entity`).value;
        if(mode==="entity") {
          if(validate && !entity) {text(this.$("#wizard-error"),this._wizardText("Bitte eine HA-Entität auswählen.","Select a Home Assistant entity."));return false;}
          d.energy[source]={mode:"entity",value:null,entity_id:entity};
        } else {
          if(raw!=="")d.energy[source]={mode:"fixed",value:key==="pv"?Number(raw)/1000:Number(raw),entity_id:""};
          else if(validate && ["buy","feed"].includes(key)) {text(this.$("#wizard-error"),this._wizardText("Bitte beide Tarife eingeben.","Enter both tariffs."));return false;}
          else d.energy[source]={mode:"fixed",value:null,entity_id:""};
        }
      }
    }
    if(step===5){
      d.reserve_w=Number(this.$("#wizard-reserve").value);
      d.shutdown_delay_s=Number(this.$("#wizard-delay").value);
      d.global_shutdown_delay_enabled=this.$("#wizard-delay-enabled").checked;
      d.max_age_s=Number(this.$("#wizard-age").value);
    }
    return true;
  }

  _wizardRender() {
    const $=(sel)=>this.$(sel), d=this._wizardDraft, step=this._wizardStep;
    const L=(de,en)=>this._wizardText(de,en);
    text($("#wizard-title"),L("Round Robin Hood einrichten","Set up Round Robin Hood"));
    text($("#wizard-progress"),L(`Schritt ${step+1} von 7`,`Step ${step+1} of 7`));
    text($("#wizard-error"),"");
    const content=$("#wizard-content");
    const intro=(heading,paragraph)=>{content.replaceChildren(node("h3",heading),node("p",paragraph,"muted"));};
    if(step===0)intro(L("Willkommen bei RRH","Welcome to RRH"),L(
      "Wir richten die wichtigsten Einstellungen gemeinsam ein. Nichts wird automatisch eingeschaltet. Wähle zunächst den Netzsensor, dann Verbraucher, Strategie, Preise und Sicherheitsabstände. Fortgeschrittene Regelgeräte kannst du anschließend unter Verbraucher anlegen.",
      "Configure the grid sensor, consumers, allocation strategy, prices and safety limits. No device will be turned on automatically. Advanced staged/variable devices can be added afterward in Consumers."));
    if(step===1){
      content.innerHTML=`<h3>${L("Netzleistung und Vorzeichen","Grid power and direction")}</h3><p class="help">${L("Einen Leistungssensor (W/kW) auswählen, keinen Energiezähler (kWh). Ein positiver Wert kann Einspeisung oder Bezug bedeuten.","Select a live power sensor (W/kW), not an energy counter (kWh). Positive values can mean export or import depending on the sensor.")}</p><label>${L("Netzleistungssensor","Grid power sensor")}<select id="wizard-grid" required></select></label><label>${L("Vorzeichen","Sign convention")}<select id="wizard-sign"><option value="positive">${L("Positiv = Einspeisung","Positive = export")}</option><option value="negative">${L("Negativ = Einspeisung","Negative = export")}</option></select></label>`;
      this._options($("#wizard-grid"),"sensor",d.grid_entity,true);$("#wizard-sign").value=d.export_positive?"positive":"negative";
    }
    if(step===2){
      intro(L("Verbraucher zuordnen","Choose consumers"),L(
        "Füge einen oder mehrere Verbraucher mit eigenem Namen, HA-Steuerentität und geschätzter Leistung hinzu. Mehrstufige/stufenlose Geräte werden später in der Verbraucher-Ansicht eingerichtet. RRH bleibt AUS.",
        "Add one or more consumers with a custom name, HA control entity and estimated watts. Configure staged/variable devices later in Consumers. RRH stays OFF."));
      if(d.consumers.length){const existing=node("p",L("Bereits vorhanden (bleiben unverändert): ","Existing (kept unchanged): ")+d.consumers.map(c=>c.name).join(", "),"help");content.append(existing);}
      content.append(node("div",null,"wizard-load-list"));content.lastChild.id="wizard-load-list";
      this._wizardLoads.forEach(load=>this._wizardAppendLoad(load));
      const add=node("button",L("+ Weiteren Verbraucher hinzufügen","+ Add another consumer"));add.type="button";
      add.onclick=()=>{this._wizardCollectLoads();this._wizardLoads.push({});this._wizardRender();};content.append(add);
      if(!this._wizardLoads.length&&!d.consumers.length)this._wizardAppendLoad();
    }
    if(step===3){
      content.innerHTML=`<h3>${L("Verteilstrategie","Allocation strategy")}</h3><p class="help">${L("Die Strategie bestimmt, wer zuerst Strom erhält. Nicht jede Strategie kann alle Geräte gleichzeitig betreiben. Details zu allen Strategien findest du unter Anleitung.","Choose how RRH prioritizes appliances. No strategy guarantees all devices will run at once. Detailed explanations are in Help / Guide.")}</p><label>${L("Strategie","Strategy")}<select id="wizard-strategy"></select></label><p id="wizard-strategy-help" class="help"></p>`;
      const profile=d.profiles[0];const select=$("#wizard-strategy");
      for(const key of Object.keys(STRATEGY_LABELS))select.add(new Option(this._strategyLabel(key),key));
      select.value=d._wizardStrategy||profile?.strategy||"classic";
      const help=()=>text($("#wizard-strategy-help"),(this._language==="en"?STRATEGY_HELP_EN:STRATEGY_HELP)[select.value]||select.value);
      select.onchange=help;help();
    }
    if(step===4){
      content.innerHTML=`<h3>${L("Energie und Kosten","Energy and costs")}</h3><p class="help">${L("PV-Nennleistung und Tarife entweder als festen Wert oder aus einer HA-Entität beziehen. Ersparnisse sind Schätzungen, keine Stromrechnung.","Use fixed values or Home Assistant entities for nominal PV capacity and tariffs. Savings are estimates, not billing.")}</p><label>${L("Währung (keine Umrechnung)","Currency (no conversion)")}<select id="wizard-currency"><option value="EUR">EUR</option><option value="CHF">CHF</option><option value="USD">USD</option><option value="GBP">GBP</option></select></label>`;
      $("#wizard-currency").value=d.energy.currency||"EUR";
      $("#wizard-currency").onchange=()=>{
        for(const [key,kind] of [["pv","capacity"],["buy","price"],["feed","price"]]){
          const el=$("#wizard-"+key+"-entity");if(el)this._statOptions(el,el.value,kind);
        }
      };
      for(const [key,source,label] of [["pv","pv_size",L("PV-Nennleistung (W, optional)","Nominal PV capacity (W, optional)")],["buy","import_price",L("Strombezugspreis (pro kWh)","Grid import price (per kWh)")],["feed","feed_in_price",L("Einspeisevergütung (pro kWh)","Feed-in tariff (per kWh)")]]) {
        const current=d.energy[source];
        const field=node("label",label,"wizard-source");
        const mode=node("select");mode.id=`wizard-${key}-mode`;
        mode.add(new Option(L("Fester Wert","Fixed value"),"fixed"));mode.add(new Option(L("HA-Entität","HA entity"),"entity"));
        const val=node("input");val.id=`wizard-${key}`;val.type="number";val.min="0";val.step="any";
        val.max=key==="pv"?"100000000":"1000";
        const entity=node("select");entity.id=`wizard-${key}-entity`;
        this._statOptions(entity,current.entity_id,key==="pv"?"capacity":"price");
        val.value=current.mode==="fixed"&&current.value!=null?(key==="pv"?current.value*1000:current.value):"";
        mode.value=current.mode||"fixed";
        const change=()=>{const isEntity=mode.value==="entity";val.hidden=isEntity;val.disabled=isEntity;entity.hidden=!isEntity;entity.disabled=!isEntity;
          };
        mode.onchange=()=>{change();if(key==="buy"||key==="feed")this._wizardRateEdited.add(key);};val.oninput=entity.onchange=()=>{if(key==="buy"||key==="feed")this._wizardRateEdited.add(key);};
        field.append(mode,val,entity);content.append(field);change();
      }
    }
    if(step===5){
      content.innerHTML=`<h3>${L("Betrieb und Schutzabstände","Operation and safety limits")}</h3><p class="help">${L("Reserve verhindert das Ausnutzen jeder einzelnen Wattspitze. Eine Abschaltverzögerung reduziert Pendeln, kann aber kurzfristig Netzbezug erzeugen. Maximalalter schützt vor veralteten Messwerten.","Reserve reduces switching on minor peaks. Shutdown delay avoids rapid cycling but may briefly draw from the grid. Maximum age rejects stale readings.")}</p><label>${L("Reserve (W)","Reserve (W)")}<input id="wizard-reserve" type="number" required min="0" max="100000" step="any"></label><label>${L("Abschaltverzögerung (s)","Shutdown delay (seconds)")}<input id="wizard-delay" type="number" required min="0" max="600" step="1"></label><label class="check"><input id="wizard-delay-enabled" type="checkbox"><span>${L("Globale Abschaltverzögerung aktiv","Enable global shutdown delay")}</span></label><label>${L("Maximales Messalter (s)","Maximum sensor age (seconds)")}<input id="wizard-age" type="number" required min="5" max="3600" step="1"></label>`;
      $("#wizard-reserve").value=d.reserve_w;$("#wizard-delay").value=d.shutdown_delay_s;
      $("#wizard-age").value=d.max_age_s;$("#wizard-delay-enabled").checked=d.global_shutdown_delay_enabled!==false;
    }
    if(step===6){
      intro(L("Zusammenfassung · Noch ausgeschaltet","Summary · Remains OFF"),L(
        "Prüfe die wichtigsten Einstellungen. Der Abschluss speichert alles in einem einzigen Backend-Aufruf. RRH bleibt danach pausiert; echte Aktoren werden nicht automatisch geschaltet.",
        "Review the configuration. Finish saves everything in one backend call. RRH remains paused; real appliances will not turn on automatically."));
      const existing=d.consumers.map(c=>c.name),added=this._wizardLoads.map(c=>`${c.name} (${c.watts} W)`);
      for (const value of [
        `${L("Netzquelle","Grid sensor")}: ${d.grid_entity}`,
        `${L("Vorzeichen","Sign")}: ${d.export_positive?"+":"-"}`,
        `${L("Verbraucher","Consumers")}: ${[...existing,...added].join(", ")}`,
        `${L("Strategie","Strategy")}: ${this._strategyLabel(d._wizardStrategy||d.profiles[0]?.strategy||"classic")}`,
        `${L("Währung","Currency")}: ${d.energy.currency}`,
        `${L("Reserve","Reserve")}: ${d.reserve_w} W`,
        `${L("Maximales Messalter","Maximum age")}: ${d.max_age_s} s`
      ]) content.append(node("p",value,"help"));
    }
    text($("#wizard-prev"),L("Zurück","Back"));$("#wizard-prev").disabled=step===0;
    text($("#wizard-next"),step===6?L("Prüfen und speichern","Review and save"):L("Weiter","Next"));
    text($("#wizard-cancel"),L("Abbrechen","Cancel"));
  }

  async _wizardMove(delta) {
    if(this._writing) return;
    text(this.$("#wizard-error"),"");
    if(delta>0 && !this._wizardReadStep(true)) return;
    if(delta<0) this._wizardReadStep(false);
    if(delta>0&&this._wizardStep===6){await this._wizardSave();return;}
    this._wizardStep=Math.max(0,Math.min(6,this._wizardStep+delta));
    this._wizardRender();
  }

  async _wizardSave() {
    const d=copy(this._wizardDraft),newLoads=this._wizardLoads;
    if(!d.grid_entity){text(this.$("#wizard-error"),"Netzleistungssensor fehlt.");return;}
    const newlyAuthorized=newLoads.map(load=>`${load.name}: ${load.entity_id}`);
    if(newlyAuthorized.length && !confirm(this._wizardText(
      `Diese realen Home-Assistant-Schalter dürfen durch RRH geschaltet werden: ${newlyAuthorized.join(", ")}. Unabhängige Schutzmaßnahmen (insbesondere für Heizgeräte) sind erforderlich. Ausdrücklich freigeben?`,
      `Authorize RRH to control these real Home Assistant switches: ${newlyAuthorized.join(", ")}. Independent safety protections (especially for heaters) are required. Explicitly authorize?`)))return;
    const strategy=d._wizardStrategy||d.profiles[0]?.strategy||"classic";
    delete d._wizardStrategy;
    for(const load of newLoads){
      d.consumers.push({id:identifier(),name:load.name,entity_id:load.entity_id,watts:load.watts,enabled:true,virtual_confirmed:true});
    }
    if(d.profiles.length){
      d.profiles[0].strategy=strategy;
      if(!POWER_SKIP_STRATEGIES.has(strategy))d.profiles[0].allow_power_skip=false;
      for(const c of (newLoads.length ? d.consumers.slice(-newLoads.length) : [])) if(!d.profiles.some(p=>p.consumer_ids.includes(c.id)))d.profiles[0].consumer_ids.push(c.id);
    }else if(d.consumers.length){d.profiles=[{id:"standard",name:"Standard",enabled:true,strategy,consumer_ids:d.consumers.map(c=>c.id),dashboard_order:"fixed",allow_power_skip:false}];}
    d.setup_complete=true;
    this.$("#wizard-next").disabled=true;
    const currencyChanged=d.energy.currency !== (this._data?.config?.energy?.currency || "EUR");
    const ok=await this._action("configure",{config:d,revision:this._wizardRevision,currency_tariffs_confirmed:currencyChanged});
    this.$("#wizard-next").disabled=false;
    if(ok){this.$("#setup-wizard").close();this._wizardOfferedThisVisit=true;this._setPage("dashboard");}
    else text(this.$("#wizard-error"),this.$("#command-error").textContent);
  }

  _conditionIndicator(item, label) {
    if (!item?.conditions?.enabled) return null;
    const checks = item.condition_checks || [];
    const total = checks.length;
    const passed = checks.filter(check => check.passed).length;
    const missing = checks.filter(check => check.invalid).length;
    const blocked = item.conditions_allowed === false;
    const detail = node("details", null, `condition-status${blocked ? " is-blocked" : ""}`);
    const summary = node("summary");
    summary.title = "Bedingungsdetails anzeigen";
    const failed = checks.filter(check => !check.passed).length;
    const suffix = missing ? " · Sensor fehlt" : failed ? ` · ${failed} Grenzwert${failed === 1 ? "" : "e"}` : "";
    summary.append(node("span", `${label}: ${passed}/${total} erfüllt${suffix}`, "condition-summary-extra"));
    const icon = node("span", "i", "info-bubble"); icon.setAttribute("aria-hidden", "true");
    summary.append(icon);
    const body = node("div", null, "condition-details");
    body.append(node("div", `${item.conditions.logic === "any" ? "ODER" : "UND"} · ${blocked ? "Gesperrt" : "Freigegeben"}`));
    for (const check of checks) {
      const detailText = check.invalid
        ? `${check.entity_id}: Sensorwert nicht verfügbar oder ungültig`
        : `${check.entity_id}: ${fmt.format(check.reading)} ${check.operator} ${fmt.format(check.threshold)} · Hysterese ${fmt.format(check.hysteresis)}`;
      body.append(node("div", `${check.passed ? "✓" : "✕"} ${detailText}`, `condition-check${check.passed ? "" : " failed"}`));
    }
    detail.dataset.statusKey = `${label}:${item.id}`;
    detail.append(summary, body);
    return detail;
  }
  _fairPeriodText(profile) {
    if (profile.runtime_window === "all") return "Fairness: Gesamt · kein automatischer Reset";
    if (profile.fair_period_start == null || profile.fair_period_end == null)
      return `Feste Periode (${profile.runtime_window}): beginnt beim ersten Aktivieren`;
    const fmt = seconds => new Date(seconds * 1000).toLocaleString("de-DE", {dateStyle:"short",timeStyle:"short"});
    return `Feste Periode (${profile.runtime_window}): ${fmt(profile.fair_period_start)} – ${fmt(profile.fair_period_end)} · danach Neustart bei 0`;
  }

  _profileCard(profile, index, locked, editing) {
    const d = this._data;
    const card = node("article", null, `card profile-card${profile.enabled ? "" : " is-inactive"}`);
    const heading = node("div", null, "profile-heading");
    const titleArea = node("div");
    titleArea.append(node("h3", profile.name));
    titleArea.append(node("span", profile.enabled ? "Aktiv" : "Inaktiv", profile.enabled ? "profile-active-label" : "profile-inactive-label"));
    const profileConditions = this._conditionIndicator(profile, "Bedingungen");
    if (profileConditions) titleArea.append(profileConditions);
    const displaySelection = ORDER_CHOICE_STRATEGIES.has(profile.strategy)
      ? ` · ${profile.dashboard_order === "allocation" ? "Dynamische Reihenfolge" : "Feste Reihenfolge"}` : "";
    const skipSelection = POWER_SKIP_STRATEGIES.has(profile.strategy)
      ? ` · ${profile.allow_power_skip ? "Überspringen erlaubt" : "Strikt"}` : "";
    const meta = node("div", `Priorität ${index + 1} · ${this._strategyLabel(profile.strategy)} · ${profile.running_count || 0}/${profile.consumer_ids.length} ein${skipSelection}${displaySelection}`, "profile-meta");
    meta.title = STRATEGY_HELP[profile.strategy] || "";
    titleArea.append(meta);
    if (["fair_runtime", "fair_energy"].includes(profile.strategy)) {
      const period = node("small", this._fairPeriodText(profile), "fair-period");
      titleArea.append(period);
    }
    heading.append(titleArea);
    if (editing) {
      const actions = node("div", null, "profile-controls");
      const btn = (label, title, click, disabled = false, css = "") => {
        const b = node("button", label, css); b.type = "button"; b.title = title;
        b.disabled = disabled; b.onclick = click; actions.append(b);
      };
      btn(profile.enabled ? "Deaktivieren" : "Aktivieren", "Profilstatus ändern", async () => {
        if (profile.enabled && d.mode === "running" && d.config.confirm_profile_toggle !== false && !confirm(`Profil „${profile.name}“ deaktivieren? Laufende RRH-Verbraucher dieser Gruppe werden ausgeschaltet.`)) return;
        await this._action("profile_participation", {profile_id:profile.id, enabled:!profile.enabled, revision:d.revision});
      }, !!d.pending || this._writing);
      btn("↑", "Priorität erhöhen", () => this._moveProfile(index, -1), locked || index === 0);
      btn("↓", "Priorität verringern", () => this._moveProfile(index, 1), locked || index === d.profiles.length - 1);
      btn("Bearbeiten", "Profil bearbeiten", () => this._editProfile(profile), locked);
      btn("Entfernen", "Profil entfernen", () => this._removeProfile(profile), locked || d.profiles.length === 1, "danger");
      heading.append(actions);
    }
    card.append(heading);
    const group = node("div", null, "pipeline");
    const ids = !ORDER_CHOICE_STRATEGIES.has(profile.strategy) || profile.dashboard_order === "allocation"
      ? profile.display_ids : profile.consumer_ids;
    for (const id of ids) {
      const c = d.consumers.find(x => x.id === id);
      if (!c) continue;
      const isNext = id === d.next_id && profile.enabled;
      const mini = node("article", null, `card pipe-card${c.state === "on" ? " pipe-on" : ""}${isNext ? " pipe-next" : ""}`);
      mini.append(consumerIcon(c));
      const detail = node("div", null, "pipe-detail");
      detail.append(node("strong", c.name));
      const state = c.state === "on" ? (c.owned ? "Ein · RRH-gesteuert" : "Ein · extern") : c.state === "off" ? "Aus" : "Unbekannt";
      detail.append(node("small", `${state} · ${watts(c.watts)}${isNext ? " · Nächster Kandidat" : ""}`));
      if (!c.enabled) detail.append(node("small", "Von RRH ausgenommen"));
      if (c.wait_reason && !c.wait_reason.startsWith("Profilbedingung gesperrt:")) {
        if (c.wait_reason.startsWith("Verbraucherbedingung gesperrt:")) {
          const indicator = this._conditionIndicator(c, "Bedingungen");
          if (indicator) detail.append(indicator);
        } else {
          const status = node("small", this._shortWait(c.wait_reason));
          status.title = c.wait_reason;
          detail.append(status);
        }
      }
      if (["fair_runtime", "fair_energy"].includes(profile.strategy)) {
        const amount = profile.fair_values?.[c.id] ?? 0;
        const unit = profile.strategy === "fair_runtime"
          ? `Fair-Zeit (${profile.runtime_window}): ${duration(amount)}`
          : `Fair-Energie (${profile.runtime_window}): ${(amount / 1000).toLocaleString("de-DE", {minimumFractionDigits:3, maximumFractionDigits:3})} kWh`;
        const fairText = node("small", unit, "fairness-stat");
        fairText.title = "Nur während dieser Fairness-Strategie und bei aktivem RRH-Betrieb gezählt.";
        detail.append(fairText);
      }
      if (c.deficit_remaining_s != null && c.owned && c.state === "on") {
        detail.append(node("small", this._deficitText(c)));
      }
      if (c.min_remaining_s > 0) detail.append(this._timerControl(c, "minimum", `Mindestlaufzeit: ${duration(c.min_remaining_s)}`));
      if (c.cooldown_remaining_s > 0) detail.append(this._timerControl(c, "cooldown", `Sperre: ${duration(c.cooldown_remaining_s)}`));
      mini.append(detail); group.append(mini);
    }
    if (!ids.length) group.append(node("div", "Noch keine Verbraucher zugeordnet.", "card empty muted"));
    card.append(group);
    return card;
  }

  _renderPipeline() {
    const target = this.$("#dashboard-pipeline"); target.replaceChildren();
    if (!this._data.profiles?.length) {
      target.append(node("div", "Noch keine Profile. Erstelle unter „Profile“ eine Gruppe.", "card empty muted"));
      return;
    }
    this._data.profiles.forEach((profile, index) => target.append(this._profileCard(profile, index, false, false)));
    const grouped = new Set(this._data.profiles.flatMap(p => p.consumer_ids));
    const unassigned = this._data.consumers.filter(c => !grouped.has(c.id) && c.id !== this._data.residual_consumer_id);
    const residual = this._data.consumers.find(c => c.id === this._data.residual_consumer_id);
    if (residual) target.append(node("div", `Restüberschuss: ${residual.name} · nutzt nur übrig gebliebene Leistung`, "card notice"));
    if (unassigned.length) target.append(node("div", `${unassigned.length} Verbraucher ohne Profil: werden nicht automatisch eingeschaltet.`, "card notice muted"));
  }

  _renderProfiles(locked) {
    const target = this.$("#profiles-list"); target.replaceChildren();
    if (!this._data.profiles?.length) {
      target.append(node("div", "Noch keine Profile. Erstelle die erste Gruppe, um Verbraucher zuzuweisen.", "card empty muted"));
      return;
    }
    this._data.profiles.forEach((profile, index) => target.append(this._profileCard(profile, index, locked, true)));
  }

  async _moveProfile(index, delta) {
    const cfg = copy(this._data.config);
    [cfg.profiles[index], cfg.profiles[index + delta]] = [cfg.profiles[index + delta], cfg.profiles[index]];
    await this._action("configure", {config:cfg, revision:this._data.revision});
  }

  async _removeProfile(profile) {
    if (this._data.config.profiles.length === 1) return;
    if (!confirm(`Profil „${profile.name}“ löschen? Seine Verbraucher bleiben erhalten, sind danach aber keiner Gruppe zugeordnet. Es wird kein HA-Schalter betätigt.`)) return;
    const cfg = copy(this._data.config);
    cfg.profiles = cfg.profiles.filter(p => p.id !== profile.id);
    await this._action("configure", {config:cfg, revision:this._data.revision});
  }

  _sensorDatalist() {
    const list = this.$("#numeric-sensors"); list.replaceChildren();
    const ids = Object.keys(this._hass?.states || {}).filter(id => /^(sensor|number|input_number)\.[a-z0-9_]+$/.test(id));
    ids.sort((a,b) => a.localeCompare(b, "de"));
    for (const id of ids) {
      const option = node("option"); option.value = id;
      option.label = `${this._entityName(id)} – ${id}`;
      list.append(option);
    }
  }

  _toggleConditions(prefix) {
    const enabled = this.$(`#${prefix}-conditions-enable`).checked;
    const fields = this.$(`#${prefix}-conditions-fields`);
    fields.hidden = !enabled;
    for (const el of fields.querySelectorAll("input,select,button")) el.disabled = !enabled;
    for (const row of fields.querySelectorAll(".condition-row")) {
      const op = row.querySelector('[data-field="operator"]');
      const hysteresis = row.querySelector('[data-field="hysteresis"]');
      if (op && hysteresis && ["==", "!="].includes(op.value)) hysteresis.disabled = true;
    }
  }

  _addConditionRule(prefix, entry = {}) {
    const target = this.$(`#${prefix}-conditions-list`);
    if (target.children.length >= 12) return;
    const row = node("div", null, "condition-row");
    row.dataset.ruleId = entry.id || identifier();
    const grid = node("div", null, "condition-grid");
    const labeled = (title, ctrl, field) => {
      const label = node("label", title);
      ctrl.dataset.field = field; label.append(ctrl); grid.append(label);
    };
    const entity = node("input"); entity.type = "text"; entity.setAttribute("list", "numeric-sensors");
    entity.placeholder = "sensor.room_temperature"; entity.value = entry.entity_id || "";
    entity.required = true; entity.maxLength = 255;
    labeled("Home-Assistant-Sensor", entity, "entity_id");
    const op = node("select");
    for (const item of ["<", "<=", ">", ">=", "==", "!="]) op.add(new Option(item === "==" ? "=" : item, item));
    op.value = entry.operator || "<"; labeled("Operator", op, "operator");
    const val = node("input"); val.type = "number"; val.step = "any"; val.required = true;
    val.value = entry.value ?? ""; labeled("Grenzwert", val, "value");
    const hyst = node("input"); hyst.type = "number"; hyst.step = "any"; hyst.min = "0";
    hyst.max = "1000000"; hyst.required = true; hyst.value = entry.hysteresis ?? 0;
    labeled("Hysterese", hyst, "hysteresis");
    op.onchange = () => { if (["==", "!="].includes(op.value)) hyst.value = "0"; hyst.disabled = !this.$(`#${prefix}-conditions-enable`).checked || ["==", "!="].includes(op.value); };
    const remove = node("button", "Entfernen"); remove.type = "button"; remove.onclick = () => row.remove();
    row.append(grid, remove); target.append(row);
    this._toggleConditions(prefix);
  }

  _fillConditionEditor(prefix, conditions) {
    this._sensorDatalist();
    const set = conditions || {enabled:false,logic:"all",rules:[]};
    this.$(`#${prefix}-conditions-enable`).checked = !!set.enabled;
    this.$(`#${prefix}-conditions-logic`).value = set.logic || "all";
    this.$(`#${prefix}-conditions-list`).replaceChildren();
    for (const rule of set.rules || []) this._addConditionRule(prefix, rule);
    this._toggleConditions(prefix);
  }

  _readConditions(prefix) {
    const enabled = this.$(`#${prefix}-conditions-enable`).checked;
    const logic = this.$(`#${prefix}-conditions-logic`).value;
    const rules = Array.from(this.$(`#${prefix}-conditions-list`).children).map(row => {
      const val = field => row.querySelector(`[data-field="${field}"]`).value;
      return {id:row.dataset.ruleId, entity_id:val("entity_id").trim(), operator:val("operator"),
        value:Number(val("value")), hysteresis:Number(val("hysteresis"))};
    });
    if (enabled && !rules.length) throw new Error("Bitte mindestens eine Bedingung hinzufügen.");
    if (enabled && rules.some(r => !r.entity_id || !Number.isFinite(r.value) || !Number.isFinite(r.hysteresis)))
      throw new Error("Bitte gültige Sensoren, Grenzwerte und Hysterese eingeben.");
    return {enabled, logic, rules};
  }

  _toggleProfileStrategy() {
    const strategy = this.$("#profile-strategy").value;
    const fair = strategy === "fair_runtime" || strategy === "fair_energy", efficiency = strategy === "maximum_efficiency";
    const powerSkip = POWER_SKIP_STRATEGIES.has(strategy);
    this.$("#profile-fair-fields").hidden = !fair;
    this.$("#profile-fair-gap-runtime-row").hidden = strategy !== "fair_runtime";
    this.$("#profile-fair-gap-energy-row").hidden = strategy !== "fair_energy";
    this.$("#profile-efficiency-fields").hidden = !efficiency;
    this.$("#profile-power-skip-fields").hidden = !powerSkip;
    this.$("#profile-fair-reset").disabled = !fair || !this._profileConfig?.profiles?.some(p => p.id === this._profileId) || this._data?.mode === "running";
    const activeProfile = this._data?.profiles?.find(p => p.id === this._profileId && p.strategy === strategy);
    text(this.$("#profile-fair-period-info"), fair && activeProfile
      ? this._fairPeriodText(activeProfile)
      : "Der Zeitraum wird beim ersten aktiven Start dieser Strategie festgelegt (sofern noch keine Periode besteht).");
    this.$("#profile-allow-power-skip").disabled = !powerSkip;
    this.$("#profile-display-row").hidden = !ORDER_CHOICE_STRATEGIES.has(strategy);
    for (const input of this.$("#profile-fair-fields").querySelectorAll("input, select")) input.disabled = !fair;
    for (const input of this.$("#profile-efficiency-fields").querySelectorAll("input, select")) input.disabled = !efficiency;
    text(this.$("#profile-strategy-help"), STRATEGY_HELP[strategy] || "");
    this.$("#profile-strategy").title = STRATEGY_HELP[strategy] || "";
  }

  _editProfile(profile) {
    this._profileConfig = copy(this._data.config);
    this._profileRevision = this._data.revision;
    this._profileId = profile?.id || identifier();
    this._profileDraftIds = [...(profile?.consumer_ids || [])];
    text(this.$("#profile-editor-title"), profile ? "Profil bearbeiten" : "Profil erstellen");
    this.$("#profile-name").value = profile?.name || "";
    this.$("#profile-enabled").checked = profile?.enabled ?? true;
    this.$("#profile-display").value = profile?.dashboard_order || "fixed";
    this.$("#profile-strategy").value = profile?.strategy || "classic";
    this.$("#profile-allow-power-skip").value = String(profile?.allow_power_skip ?? ((profile?.strategy === "power_asc" || profile?.strategy === "power_desc") && profile?.allow_power_skip === undefined));
    this.$("#profile-runtime-window").value = profile?.runtime_window || "7d";
    this.$("#profile-fair-rotation").value = profile?.fair_rotation_s ?? 900;
    this.$("#profile-fair-gap-runtime").value = profile?.fair_min_gap_s ?? 60;
    this.$("#profile-fair-gap-energy").value = profile?.fair_min_gap_wh ?? 10;
    this.$("#profile-efficiency-gain").value = profile?.efficiency_min_gain_w ?? 200;
    this.$("#profile-efficiency-interval").value = profile?.efficiency_interval_s ?? 60;
    this.$("#profile-efficiency-margin").value = profile?.efficiency_start_margin_w ?? 50;
    this._toggleProfileStrategy();
    this._fillConditionEditor("profile", profile?.conditions);
    text(this.$("#profile-error"), "");
    this._renderProfileMembers();
    this.$("#profile-editor").showModal();
    this.$("#profile-name").focus();
  }

  _renderProfileMembers() {
    const target = this.$("#profile-members"); target.replaceChildren();
    const members = this._profileDraftIds;
    const consumers = this._profileConfig.consumers;
    const assignedElsewhere = new Set(this._profileConfig.profiles
      .filter(p => p.id !== this._profileId).flatMap(p => p.consumer_ids));
    const strategy = this.$("#profile-strategy").value;
    const ordered = [...members];
    if (strategy === "power_asc" || strategy === "power_desc") {
      const lookup = new Map(consumers.map(c => [c.id, c.watts]));
      const original = new Map(members.map((id, i) => [id, i]));
      const sign = strategy === "power_asc" ? 1 : -1;
      ordered.sort((a,b) => sign * ((lookup.get(a) ?? 0) - (lookup.get(b) ?? 0)) || original.get(a) - original.get(b));
    }
    const ids = [...ordered, ...consumers.map(c => c.id).filter(id => !members.includes(id) && !assignedElsewhere.has(id))];
    for (const id of ids) {
      const c = consumers.find(x => x.id === id);
      if (!c) continue;

      const row = node("div", null, "member-row");
      const label = node("label", null, "check");
      const check = node("input"); check.type = "checkbox"; check.checked = members.includes(id);
      check.onchange = () => {
        this._profileDraftIds = check.checked ? [...this._profileDraftIds, id] : this._profileDraftIds.filter(x => x !== id);
        this._renderProfileMembers();
      };
      const description = node("span", c.name);
      description.append(node("small", `${watts(c.watts)} · ${c.entity_id}`));
      label.append(check, description); row.append(label);
      const i = members.indexOf(id);
      if (i >= 0 && !["power_asc", "power_desc"].includes(this.$("#profile-strategy").value)) {
        for (const [label, delta] of [["↑", -1],["↓", 1]]) {
          const button = node("button", label); button.type = "button";
          button.title = `Reihenfolge ${delta < 0 ? "nach oben" : "nach unten"}`;
          button.disabled = i + delta < 0 || i + delta >= members.length;
          button.onclick = () => {
            [this._profileDraftIds[i], this._profileDraftIds[i + delta]] = [this._profileDraftIds[i + delta], this._profileDraftIds[i]];
            this._renderProfileMembers();
          }; row.append(button);
        }
      }
      target.append(row);
    }
    if (!ids.length) target.append(node("p", "Zuerst unter „Verbraucher“ Testgeräte anlegen.", "muted"));
  }

  async _resetFairProfile() {
    const kind = this.$("#profile-strategy").value;
    const original = this._profileConfig?.profiles?.find(p => p.id === this._profileId);
    if (!original || !["fair_runtime", "fair_energy"].includes(kind)) {
      text(this.$("#profile-error"), "Bitte zuerst das Profil speichern."); return;
    }
    if (this._data.mode === "running") {
      text(this.$("#profile-error"), "Zum Zurücksetzen RRH zuerst pausieren."); return;
    }
    if (!confirm(`Fairness-Statistik für „${original.name}“ zurücksetzen? Nur ${this._strategyLabel(kind)} wird zurückgesetzt; allgemeine Laufzeiten und die andere Fairness-Strategie bleiben erhalten.`)) return;
    const ok = await this._action("reset_fair", {profile_id:this._profileId, metric:kind, revision:this._profileRevision});
    if (ok) {
      // Reset changes the revision, not the pending editor selections. Keep
      // the chosen strategy visible without requiring a close/reopen cycle.
      this._profileConfig = copy(this._data.config);
      this._profileRevision = this._data.revision;
      this._toggleProfileStrategy();
      text(this.$("#profile-error"), "Fairness-Statistik zurückgesetzt. Profiländerungen bei Bedarf noch speichern.");
    } else text(this.$("#profile-error"), this.$("#command-error").textContent);
  }

  async _saveProfile() {
    if (this._writing) return;
    const cfg = copy(this._profileConfig);
    const name = this.$("#profile-name").value.trim();
    if (!name) { text(this.$("#profile-error"), "Bitte einen Profilnamen eingeben."); return; }
    const ids = [...this._profileDraftIds];
    let conditions;
    try { conditions = this._readConditions("profile"); }
    catch (err) { text(this.$("#profile-error"), err.message); return; }
    if (this.$("#profile-strategy").value === "maximum_efficiency" && ids.length > 24) {
      text(this.$("#profile-error"), "Maximum Efficiency unterstützt maximal 24 Verbraucher pro Profil."); return;
    }
    const updated = {id:this._profileId, name, enabled:this.$("#profile-enabled").checked,
      strategy:this.$("#profile-strategy").value, consumer_ids:ids,
      runtime_window:this.$("#profile-runtime-window").value,
      fair_rotation_s:Number(this.$("#profile-fair-rotation").value),
      fair_min_gap_s:Number(this.$("#profile-fair-gap-runtime").value),
      fair_min_gap_wh:Number(this.$("#profile-fair-gap-energy").value),
      efficiency_min_gain_w:this.$("#profile-strategy").value === "maximum_efficiency" ? Number(this.$("#profile-efficiency-gain").value) : 200,
      efficiency_interval_s:this.$("#profile-strategy").value === "maximum_efficiency" ? Number(this.$("#profile-efficiency-interval").value) : 60,
      efficiency_start_margin_w:this.$("#profile-strategy").value === "maximum_efficiency" ? Number(this.$("#profile-efficiency-margin").value) : 50,
      allow_power_skip:POWER_SKIP_STRATEGIES.has(this.$("#profile-strategy").value) && this.$("#profile-allow-power-skip").value === "true",
      dashboard_order:this.$("#profile-display").value, conditions};
    if (cfg.profiles.some(p => p.id !== this._profileId && p.consumer_ids.some(id => ids.includes(id)))) {
      text(this.$("#profile-error"), "Ein ausgewählter Verbraucher wird bereits in einem anderen Profil verwendet. Bitte neu laden."); return;
    }
    cfg.profiles = cfg.profiles.map(p => p.id === this._profileId ? updated : p);
    if (!cfg.profiles.some(p => p.id === this._profileId)) cfg.profiles.push(updated);
    this.$("#save-profile").disabled = true;
    const ok = await this._action("configure", {config:cfg, revision:this._profileRevision});
    this.$("#save-profile").disabled = false;
    if (ok) this.$("#profile-editor").close();
    else text(this.$("#profile-error"), this.$("#command-error").textContent);
  }

  _options(select, domain, selected, powerOnly = false) {
    select.replaceChildren(new Option("Bitte auswählen", ""));
    const states = this._hass?.states || {};
    const domains = domain.split("|");
    const ids = Object.keys(states).filter(id => domains.some(d => id.startsWith(`${d}.`)) && (!powerOnly || ["W","kW"].includes(states[id].attributes?.unit_of_measurement)));
    if (selected && !ids.includes(selected)) ids.push(selected);
    ids.sort((a,b) => a.localeCompare(b, "de"));
    for (const id of ids) {
      const state = states[id];
      select.add(new Option(`${state?.attributes?.friendly_name || id} – ${id}${state ? "" : " (fehlt)"}`, id));
    }
    select.value = selected || "";
  }

  _fillSettings(force = false) {
    if (!this._data || (!force && (this._settingsDirty || this._settingsRevision === this._data.revision))) return;
    const cfg = this._data.config;
    this._settingsConfig = copy(cfg);
    this._tariffFieldsEdited.clear();
    this._settingsRevision = this._data.revision;
    this._options(this.$("#grid-entity"), "sensor", cfg.grid_entity, true);
    this.$("#sign").value = cfg.export_positive ? "positive" : "negative";
    this.$("#reserve-input").value = cfg.reserve_w;
    this.$("#global-delay-enabled").checked = cfg.global_shutdown_delay_enabled !== false;
    this.$("#delay").value = cfg.shutdown_delay_s;
    this._toggleGlobalDelay();
    this.$("#max-age").value = cfg.max_age_s;
    this.$("#startup-mode").value=cfg.startup_mode || "off";
    this.$("#confirm-timer").checked = cfg.confirm_timer_skip !== false;
    this.$("#confirm-profile").checked = cfg.confirm_profile_toggle !== false;
    this.$("#show-data-quality").checked = cfg.data_quality_visible !== false;
    const residualSelect = this.$("#residual-consumer");
    residualSelect.replaceChildren(new Option("Keinen Restüberschussverbraucher", ""));
    for (const c of cfg.consumers.filter(c => c.power_mode && c.power_mode !== "fixed"))
      residualSelect.add(new Option(`${c.name} (${c.power_mode === "variable" ? "stufenlos" : "mehrstufig"})`, c.id));
    residualSelect.value = cfg.residual_consumer_id || "";
    this.$("#freshness-settings").hidden = cfg.data_quality_visible === false;
    const opt=cfg.energy;
    this.$("#stat-currency").value=opt.currency || "EUR";
    for(const [key,source] of [["pv",opt.pv_size],["import",opt.import_price],["feed",opt.feed_in_price]]) {
      this.$(`#stat-${key}-mode`).value=source.mode;
      this.$(`#stat-${key}-fixed`).value=key==="pv" && source.value!=null ? Number((source.value*1000).toFixed(4)) : source.value ?? "";
      this._statOptions(this.$(`#stat-${key}-entity`),source.entity_id,key==="pv"?"capacity":"price");
      this._toggleStatMode(key);
    }
    this.$("#stat-currency").value=opt.currency || "EUR";
    this._currencyLabels();
    for(const [id,value,kind] of [["stat-pv-power-entity",opt.pv_power_entity,"power"],["stat-pv-energy-entity",opt.pv_energy_entity,"energy"]])
      this._statOptions(this.$(`#${id}`),value,kind);
    const view=cfg.dashboard;
    this.$("#stat-chart-type").replaceChildren(...Object.keys(CHART_LABELS).map(key=>new Option(this._tr(CHART_LABELS[key]),key)));
    this.$("#stat-chart-type").value=view.chart_type;
    this.$("#stat-language").replaceChildren(...[["auto",this._tr("automatic")],["de","Deutsch"],["en","English"],["fr","Français"],["es","Español"],["pt","Português"],["it","Italiano"]].map(([value,label])=>new Option(label,value)));
    this.$("#stat-language").value=view.language;
    this.$("#show-donation").checked=view.show_donation !== false;
    const toggles=this.$("#stat-card-toggles"); toggles.replaceChildren();
    for(const key of Object.keys(CARD_NAMES)){
      const label=node("label",null,"check"),cb=node("input");cb.type="checkbox";cb.dataset.statCard=key;cb.checked=view.visible[key]!==false;
      label.append(cb,node("span",this._tr(CARD_NAMES[key])));toggles.append(label);
    }
    text(this.$("#settings-error"), "");text(this.$("#energy-save-error"),"");
    text(this.$("#settings-hint"), this._data.mode === "running" ? "Zum Bearbeiten zuerst pausieren." : "");
  }

  _toggleGlobalDelay() {
    const enabled = this.$("#global-delay-enabled").checked;
    this.$("#global-delay-fields").parentElement.hidden = !enabled;
    this.$("#delay").disabled = !enabled;
  }

  async _saveSettings() {
    const cfg = copy(this._settingsConfig);
    Object.assign(cfg, {grid_entity:this.$("#grid-entity").value, export_positive:this.$("#sign").value === "positive", reserve_w:Number(this.$("#reserve-input").value), shutdown_delay_s:Number(this.$("#delay").value), global_shutdown_delay_enabled:this.$("#global-delay-enabled").checked, max_age_s:Number(this.$("#max-age").value), confirm_timer_skip:this.$("#confirm-timer").checked, confirm_profile_toggle:this.$("#confirm-profile").checked,
      data_quality_visible:this.$("#show-data-quality").checked,
      startup_mode:this.$("#startup-mode").value,
      residual_consumer_id:this.$("#residual-consumer").value});
    for(const [key,field] of [["pv","pv_size"],["import","import_price"],["feed","feed_in_price"]]) {
      const mode=this.$(`#stat-${key}-mode`).value;
      const raw=this.$(`#stat-${key}-fixed`).value;
      cfg.energy[field]={mode,value:raw.trim()===""?null:(key==="pv"?Number(raw)/1000:Number(raw)),entity_id:mode==="entity"?this.$(`#stat-${key}-entity`).value:""};
    }
    const newCurrency=this.$("#stat-currency").value;
    const currencyChanged=newCurrency !== (this._settingsConfig.energy.currency || "EUR");
    if(currencyChanged){
      const importPrice=cfg.energy.import_price,feedPrice=cfg.energy.feed_in_price;
      const isExplicit=source => source.mode==="entity" ? !!source.entity_id : source.value!==null;
      if(!this._tariffFieldsEdited.has("import") || !this._tariffFieldsEdited.has("feed") ||
         !isExplicit(importPrice) || !isExplicit(feedPrice)){
        text(this.$("#energy-save-error"),"Währungswechsel: Beide Tarife in der neuen Währung erneut eingeben bzw. ihre Tarif-Sensoren ausdrücklich auswählen.");
        return;
      }
      if(!confirm("Währung ändern? Beide Tarife wurden neu bestätigt. Es erfolgt keine Umrechnung. Bestehende monetäre Statistiken verhindern den Wechsel, bis sie bewusst exportiert und zurückgesetzt wurden."))return;
    }
    cfg.energy.currency=newCurrency;
    cfg.energy.pv_power_entity=this.$("#stat-pv-power-entity").value;
    cfg.energy.pv_energy_entity=this.$("#stat-pv-energy-entity").value;
    // Preserve existing optional export-meter configuration; it is not a grid-power sensor.
    cfg.dashboard.chart_type=this.$("#stat-chart-type").value;
    cfg.dashboard.show_donation=this.$("#show-donation").checked;
    cfg.dashboard.language=this.$("#stat-language").value;
    cfg.dashboard.visible=Object.fromEntries(Array.from(this.shadowRoot.querySelectorAll("[data-stat-card]"),el=>[el.dataset.statCard,el.checked]));
    if (await this._action("configure", {config:cfg, revision:this._settingsRevision, currency_tariffs_confirmed:currencyChanged})) {
      this._settingsDirty = false; this._fillSettings(true);
      text(this.$("#settings-hint"), "Gespeichert. Automatik bleibt pausiert.");
      text(this.$("#energy-save-hint"), "Gespeichert.");
    } else { text(this.$("#settings-error"), this.$("#command-error").textContent); text(this.$("#energy-save-error"), this.$("#command-error").textContent); }
  }

  _currencyLabels() {
    const code=this.$("#stat-currency").value || "EUR";
    const labels={
      de:["Strompreis","Einspeisevergütung"],en:["Grid import price","Feed-in tariff"],
      fr:["Tarif d’achat","Tarif d’injection"],es:["Precio de compra","Tarifa de vertido"],
      pt:["Preço de compra","Tarifa de injeção"],it:["Prezzo di acquisto","Tariffa di immissione"]
    }[this._language] || ["Grid import price","Feed-in tariff"];
    text(this.$("#import-price-label"), `${labels[0]} (${code}/kWh)`);
    text(this.$("#feed-price-label"), `${labels[1]} (${code}/kWh)`);
  }

  _toggleStatMode(key) {
    const entity=this.$(`#stat-${key}-mode`).value==="entity";
    this.$(`#stat-${key}-fixed`).hidden=entity;
    this.$(`#stat-${key}-entity`).hidden=!entity;
  }
  _sourceScale(kind, unit, currency) {
    const u=String(unit||"").replace(/\s/g,"").toLowerCase();
    if(kind==="capacity") return {w:.001,wp:.001,kw:1,kwp:1}[u];
    if(kind==="power") return {w:1,kw:1000}[u];
    if(kind==="energy") return {wh:.001,kwh:1,mwh:1000}[u];
    const units={EUR:{"€/kwh":1,"eur/kwh":1,"euro/kwh":1,"ct/kwh":.01,"cent/kwh":.01,"c/kwh":.01,"€/mwh":.001,"eur/mwh":.001},
      CHF:{"chf/kwh":1,"fr./kwh":1,"fr/kwh":1,"chf/mwh":.001},
      USD:{"usd/kwh":1,"$/kwh":1,"usd/mwh":.001},
      GBP:{"gbp/kwh":1,"£/kwh":1,"gbp/mwh":.001}};
    return kind==="price" ? units[currency||"EUR"]?.[u] : undefined;
  }
  _statOptions(select, value, kind) {
    const states=this._hass?.states || {};
    const currency=select.id.startsWith("wizard-")?(this.$("#wizard-currency")?.value||this._data?.config?.energy?.currency):this.$("#stat-currency")?.value;
    select.replaceChildren(new Option(this._tr("disabled"),""));
    const allowed=kind==="price"||kind==="capacity"?/^(sensor|number|input_number)\./:/^sensor\./;
    const ids=Object.keys(states).filter(id=>allowed.test(id) &&
      this._sourceScale(kind,states[id]?.attributes?.unit_of_measurement,currency)!==undefined &&
      Number.isFinite(Number(states[id].state)) && states[id].state!=="" &&
      Number(states[id].state)>=0 && Number(states[id].state)<1e10 &&
      !states[id]?.attributes?.restored).sort();
    if(value && !ids.includes(value)) ids.unshift(value); // Existing source shown as invalid instead of silently removed.
    for(const id of ids){
      const state=states[id]; const unit=state?.attributes?.unit_of_measurement || "";
      const valid=this._sourceScale(kind,unit,currency)!==undefined && state && Number.isFinite(Number(state.state)) && Number(state.state)>=0 && Number(state.state)<1e10;
      select.add(new Option(`${state?.attributes?.friendly_name || id} · ${id}${unit?` (${unit})`:""}${valid?"":" ⚠"}`,id));
    }
    select.value=value||"";
  }
  _number(val, digits=2) {if(val==null || !Number.isFinite(Number(val)))return "—"; const n=Number(val); const shown=Math.abs(n)<0.5*(10**-digits)?0:n; return new Intl.NumberFormat(LOCALE_KEYS[this._language] || "de-DE", {minimumFractionDigits:digits,maximumFractionDigits:digits}).format(shown);}
  _euro(val,digits=2){if(val==null)return "—";const currency=this._data?.config?.energy?.currency||"EUR";return new Intl.NumberFormat(LOCALE_KEYS[this._language]||"de-DE",{style:"currency",currency,minimumFractionDigits:digits,maximumFractionDigits:digits}).format(Number(val));}
  _renderStats(data,locked){
    const stat=data.statistics; if(!stat)return;
    const live=stat.live||{}, total=stat.total||{}, src=stat.sensors||{};
    const display=data.config.dashboard?.visible||{};
    for(const [key,selector] of [["grid","grid-card"],["budget","budget-card"],["managed","managed-card"],["live_chart","live-chart-card"],["rate","rate-card"],["total_net","total-net-card"],["total_energy","total-energy-card"],["capture","capture-card"],["pipeline","dashboard-pipeline"],["pv_power","pv-power-card"]]){
      const el=this.$(`#${selector}`); if(el) (key==="pipeline" ? el.closest(".pipeline-shell") : el).hidden=display[key]===false;
    }
    text(this.$("#rrh-live-eur-min"),live.net_eur_min==null?"—":this._euro(live.net_eur_min*60,2)+"/h");
    text(this.$("#rrh-live-price-hint"),live.buy_eur_kwh==null||live.feed_eur_kwh==null?this._tr("priceMissing"):`${this._number(live.buy_eur_kwh,3)} − ${this._number(live.feed_eur_kwh,3)} ${this._data?.config?.energy?.currency || "EUR"}/kWh`);
    const hasFinancialData=(total.valued_kwh||0)>0 || (live.buy_eur_kwh!=null && live.feed_eur_kwh!=null);
    text(this.$("#rrh-total-eur"),hasFinancialData?this._euro(total.net_benefit_eur):"—");
    text(this.$("#rrh-total-kwh"),`${this._number(total.rrh_kwh,2)} kWh`);
    text(this.$("#rrh-capture"),live.capture_pct==null?"—":`${this._number(live.capture_pct,1)} %`);
    text(this.$("#rrh-pv-power"),src.pv_power_w==null?"—":watts(src.pv_power_w));
    text(this.$("#rrh-pv-capacity"),src.pv_size_kwp==null?"":`${this._number(src.pv_size_kwp*1000,0)} W`);
    const tracked=total.potential_kwh>0?100*total.rrh_kwh/total.potential_kwh:null;
    const stats=[["captured",`${this._number(total.rrh_kwh,3)} kWh`],["potential",`${this._number(total.potential_kwh,3)} kWh`],
      ["exported",`${this._number(total.export_kwh,3)} kWh`],["captureAvg",tracked==null?"—":`${this._number(tracked,1)} %`],
      ["gross",hasFinancialData?this._euro(total.gross_value_eur):"—"],["lost",hasFinancialData?this._euro(total.export_value_eur):"—"],
      ["total_net",hasFinancialData?this._euro(total.net_benefit_eur):"—"],["moneyCoverage",`${this._number(total.valued_kwh,3)} kWh`],
      ["timeRunning",`${this._number(total.runtime_h,2)} h`],["pvSize",src.pv_size_kwp==null?"—":`${this._number(src.pv_size_kwp*1000,0)} W`],
      ["pv_power",src.pv_power_w==null?"—":watts(src.pv_power_w)],["solarEnergy",`${this._number(total.pv_generation_kwh,3)} kWh`],
      ["gridExportEnergy",`${this._number(total.meter_export_kwh,3)} kWh`],
      ["rate",live.net_eur_min==null?"—":this._euro(live.net_eur_min*60,4)+"/h"]];
    const overview=this.$("#energy-overview");overview.replaceChildren();
    for(const [key,value] of stats){const card=node("div",null,"stats-box");card.append(node("small",this._tr(key)),node("strong",value));overview.append(card);}
    this._statTable("#energy-devices",[this._tr("consumerHeader"),this._tr("captured"),this._tr("consumption"),this._tr("durationLabel"),this._tr("starts")],
      Object.entries(stat.consumer||{}).map(([id,v])=>[data.consumers.find(c=>c.id===id)?.name||id,this._number(v.kwh,3),this._number(v.load_kwh,3),this._number(v.runtime_h,2),this._number(v.starts,0)]));
    this._statTable("#energy-days",[this._tr("dayStats"),this._tr("captured"),this._tr("exported"),this._tr("total_net")],
      (stat.daily||[]).map(row=>[row.date,`${this._number(row.rrh_kwh||0,3)} kWh`,`${this._number(row.export_kwh||0,3)} kWh`,(row.valued_kwh||0)>0?this._euro(row.net_benefit_eur||0):"—"]));
    text(this.$("#energy-source-warnings"),(src.warnings||[]).join(" · "));
    this.$("#reset-statistics").disabled=locked;
    this._drawChart(this.$("#rrh-live-chart"),stat,data.config.dashboard?.chart_type||"gauge");
    this._drawHistory24h(this.$("#energy-chart"),stat);
    text(this.$("#rrh-chart-caption"),`${this._number(live.rrh_w,0)} W / ${this._number(live.surplus_w,0)} W`);
  }
  _statTable(selector,heads,rows){
    const target=this.$(selector),table=node("table",null,"stats-table"),thead=node("thead"),tr=node("tr");
    for(const h of heads)tr.append(node("th",h));thead.append(tr);table.append(thead);
    const body=node("tbody");
    for(const values of rows){const line=node("tr");for(const v of values)line.append(node("td",v));body.append(line);}
    table.append(body);target.replaceChildren(table);
  }
  _drawHistory24h(target,stat) {
    const all=stat.history||[],now=Date.now()/1000,start=now-24*3600;
    const hist=all.filter(r=>r[0]>=start&&r[0]<=now+60),en=this._language==="en";
    const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","0 0 960 260");
    svg.setAttribute("role","img");svg.setAttribute("aria-label",en?"24-hour surplus utilization in percent":"24-Stunden-Überschussnutzung in Prozent");
    const ns="http://www.w3.org/2000/svg";
    const shape=(tag,attributes)=>{const el=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attributes))el.setAttribute(k,String(v));svg.append(el);return el;};
    const label=(x,y,value,anchor="middle")=>{const el=shape("text",{x,y,fill:"currentColor","font-size":14,"text-anchor":anchor});el.textContent=value;};
    for(const pct of [0,50,100]){
      const y=218-pct*1.7;
      shape("line",{x1:48,x2:939,y1:y,y2:y,stroke:"var(--divider-color, #666)",opacity:.6});
      label(38,y+4,`${pct}%`,"end");
    }
    for(const hours of [24,18,12,6,0]){
      const x=48+(24-hours)/24*891;
      label(x,246,hours===0?(en?"Now":"Jetzt"):`−${hours}h`);
    }
    const xVal=t=>48+Math.max(0,Math.min(1,(t-start)/(24*3600)))*891;
    const paths=[];let current=[];
    const flush=()=>{if(current.length>1)paths.push(current);current=[];};
    let lastValidTimestamp=null;
    for(const row of hist){
      if(row[5]===false || row[4]<=0){flush();lastValidTimestamp=null;continue;}
      if(lastValidTimestamp!==null && row[0]-lastValidTimestamp>90) flush();
      const value=Math.max(0,Math.min(100,Number(row[3])));
      current.push([xVal(row[0]),218-1.7*value]);
      lastValidTimestamp=row[0];
    }
    flush();
    for(const points of paths)shape("polyline",{points:points.map(p=>p.join(",")).join(" "),fill:"none",stroke:"var(--primary-color, #10a8c5)","stroke-width":3,"stroke-linejoin":"round"});
    for(const row of hist.filter(r=>r[5]!==false&&r[4]>0).slice(-5)){
      shape("circle",{cx:xVal(row[0]),cy:218-1.7*Math.max(0,Math.min(100,row[3])),r:3,fill:"var(--primary-color, #10a8c5)"});
    }
    target.replaceChildren(svg);
    const description=node("p",en?
      `Last 24 hours · ${hist.length} samples (30s nominal interval). Utilization = RRH-controlled watts ÷ (RRH watts + measured positive export) × 100. Pauses, stale readings and missing points are gaps. Estimates, not a revenue meter.`:
      `Letzte 24 Stunden · ${hist.length} Messpunkte (normalerweise alle 30 s). Nutzungsquote = RRH-gesteuerte Leistung ÷ (RRH-Leistung + gemessene positive Einspeisung) × 100. Pause, veraltete Messwerte und Ausfälle erzeugen Lücken. Schätzung, kein Abrechnungszähler.`,"help");
    target.append(description);
  }

  _drawChart(target,stat,type){
    const hist=stat.history||[],live=stat.live||{};
    const pct=Math.max(0,Math.min(100,live.capture_pct||0));
    const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
    svg.setAttribute("viewBox","0 -16 480 172");svg.setAttribute("aria-label",`${this._tr("live_chart")}: ${this._number(live.capture_pct,1)} %`);
    const shape=(name,attrs)=>{const el=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,String(value));svg.append(el);return el;};
    const label=(x,y,value,size=16)=>{const el=shape("text",{x,y,fill:"currentColor","text-anchor":"middle","font-size":size});el.textContent=value;};
    const green="var(--primary-color, #168b70)",gray="var(--secondary-text-color, #8aa0a6)";
    if(type==="gauge"){
      // Compact horizontal efficiency indicator. Retain stored "gauge" choice for upgrades.
      svg.setAttribute("viewBox","0 0 480 70");
      const segments=[[0,45,"#d77372"],[45,75,"#f1cc75"],[75,100,"#97d4b1"]];
      for(const [from,to,color] of segments)shape("rect",{x:16+448*from/100,y:30,width:448*(to-from)/100,height:19,fill:color,opacity:.38});
      shape("rect",{x:16,y:30,width:448*pct/100,height:19,rx:4,fill:pct<45?"#d77372":pct<75?"#e4bd56":"#64bd8d"});
      shape("rect",{x:16,y:30,width:448,height:19,rx:4,fill:"none",stroke:gray,"stroke-width":1});
      label(240,22,`${this._number(live.capture_pct,1)} %`,19);
      target.replaceChildren(svg);return;
    } else if(type==="legacy_gauge"){
      const circumference=Math.PI*113;
      shape("path",{d:"M115 125 A125 125 0 0 1 365 125",fill:"none",stroke:gray,"stroke-width":23,"stroke-linecap":"round"});
      shape("path",{d:"M115 125 A125 125 0 0 1 365 125",fill:"none",stroke:green,"stroke-width":23,"stroke-linecap":"round","stroke-dasharray":`${circumference*pct/100} ${circumference}`,opacity:pct>0?1:0});
      label(240,112,`${this._number(live.capture_pct,1)} %`,28);
    } else if(type==="donut"){
      shape("circle",{cx:240,cy:72,r:50,fill:"none",stroke:gray,"stroke-width":19});
      shape("circle",{cx:240,cy:72,r:50,fill:"none",stroke:green,"stroke-width":19,"stroke-dasharray":`${Math.PI*pct} ${Math.PI*100}`,transform:"rotate(-90 240 72)"});
      label(240,80,`${this._number(live.capture_pct,1)} %`,21);
    } else if(type==="stacked"){
      shape("rect",{x:16,y:55,width:448,height:36,rx:13,fill:gray});
      shape("rect",{x:16,y:55,width:448*pct/100,height:36,rx:13,fill:green});
      label(240,124,`${this._number(live.capture_pct,1)} %`,20);
    } else {
      const points=(hist.length?hist:[[0,0,0,pct,0]]).slice(type==="sparkline"?-45:-90);
      const coords=points.map((point,index)=>[18+(444*index/Math.max(1,points.length-1)),125-1.05*Math.max(0,Math.min(100,point[3]))]);
      shape("line",{x1:18,y1:125,x2:462,y2:125,stroke:gray,"stroke-width":1,opacity:.6});
      if(type==="bar"){
        const width=444/Math.max(1,coords.length);
        for(const [index,point] of coords.entries())shape("rect",{x:point[0]-width*.35,y:point[1],width:Math.max(2,width*.7),height:Math.max(0,125-point[1]),fill:green});
      } else {
        if(type==="area")shape("polygon",{points:[`18,125`,...coords.map(c=>c.join(",")),"462,125"].join(" "),fill:green,opacity:.16});
        shape("polyline",{points:coords.map(c=>c.join(",")).join(" "),fill:"none",stroke:green,"stroke-width":type==="sparkline"?3:2.5,"stroke-linejoin":"round"});
      }
      label(240,20,`${this._number(live.capture_pct,1)} %`,18);
    }
    target.replaceChildren(svg);
  }

  _renderConsumers(locked) {
    const target = this.$("#consumers");
    // Keep keyboard focus on the same consumer/action after a reorder or status update.
    const focused = this.shadowRoot.activeElement;
    const focusId = focused?.closest(".consumer")?.dataset.consumer;
    const focusAction = focused?.dataset.control;
    target.replaceChildren();
    if (!this._data.consumers.length) {
      target.append(node("div", "Noch keine Verbraucher. Füge einen vorhandenen HA-Verbraucher hinzu.", "card empty muted"));
      return;
    }
    this._data.consumers.forEach((c, i) => {
      const isNext = c.id === this._data.next_id;
      const row = node("article", null, `card consumer${isNext ? " is-next" : ""}`);
      row.dataset.consumer = c.id;
      const head = node("div", null, "consumer-head");
      const icon = consumerIcon(c);
      const title = node("div", null, "consumer-title");
      const heading = node("h3", c.name);
      // Backend-validated IDs are stable; never interpolate names as HTML.
      heading.id = `consumer-title-${c.id}`;
      row.setAttribute("aria-labelledby", heading.id);
      title.append(heading);
      if (isNext) title.append(node("span", "Nächster Kandidat", "chip next-chip"));
      head.append(icon, title);
      const state = c.state === "on"
        ? (c.owned ? "Ein · RRH-gesteuert" : "Ein · extern / nicht übernommen")
        : c.state === "off" ? "Aus" : "Nicht verfügbar / unbekannt";
      row.append(head, node("div", state, "consumer-state"));
      const facts = node("dl", null, "consumer-facts");
      const power = node("div"), participation = node("div");
      power.append(node("dt", c.power_mode === "fixed" ? "Nennleistung" : "Mindestleistung"), node("dd", watts(c.watts)));
      if (c.power_mode !== "fixed") power.append(node("dt", "Aktuelle Sollleistung"), node("dd", watts(c.active_watts)));
      if (c.id === this._data.residual_consumer_id) row.append(node("p", "Restüberschussverbraucher · niedrigste Priorität", "muted"));
      const memberProfile = this._data.profiles.find(p => p.consumer_ids.includes(c.id));
      participation.append(node("dt", "Teilnahme"), node("dd", c.enabled ? (memberProfile ? (memberProfile.enabled ? "Aktiv" : "Profil inaktiv") : "Ohne Profil") : "Aus", "participation-value"));
      facts.append(power, participation);
      row.append(facts, node("div", `${c.entity_id} · Profil: ${memberProfile?.name || "nicht zugeordnet"}`, "consumer-entity muted"));
      if (c.min_remaining_s > 0) row.append(this._timerControl(c, "minimum", `⏱ Mindestlaufzeit: ${duration(c.min_remaining_s)}`));
      if (c.cooldown_remaining_s > 0) row.append(this._timerControl(c, "cooldown", `⏳ Sperre: ${duration(c.cooldown_remaining_s)}`));
      if (memberProfile?.enabled && memberProfile.conditions?.enabled && !memberProfile.conditions_allowed) {
        const profileIndicator = this._conditionIndicator(memberProfile, "Profilbedingungen");
        if (profileIndicator) row.append(profileIndicator);
      }
      const consumerIndicator = this._conditionIndicator(c, "Verbraucherbedingungen");
      if (consumerIndicator) row.append(consumerIndicator);
      if (c.wait_reason && !c.wait_reason.startsWith("Profilbedingung gesperrt:") &&
          !c.wait_reason.startsWith("Verbraucherbedingung gesperrt:")) {
        const brief = node("div", this._shortWait(c.wait_reason), "muted consumer-entity");
        brief.title = c.wait_reason;
        row.append(brief);
      }
      if (memberProfile && ["fair_runtime", "fair_energy"].includes(memberProfile.strategy)) {
        const amount = memberProfile.fair_values?.[c.id] ?? 0;
        const unit = memberProfile.strategy === "fair_runtime"
          ? `Fair-Zeit (${memberProfile.runtime_window}): ${duration(amount)}`
          : `Fair-Energie (${memberProfile.runtime_window}): ${(amount / 1000).toLocaleString("de-DE", {minimumFractionDigits:3, maximumFractionDigits:3})} kWh`;
        const info = node("div", unit, "muted consumer-entity fairness-stat");
        info.title = "Nur während der gewählten Fairness-Strategie und bei aktivem RRH gezählt.";
        row.append(info);
      }
      if (c.deficit_remaining_s != null && c.owned && c.state === "on") {
        row.append(node("div", this._deficitText(c), "timer-chip"));
      }
      if (!c.enabled && c.owned && c.state === "on") {
        row.append(node("p", "Ausschalten bei aktivem Betrieb ausstehend.", "consumer-warning"));
      }
      const controls = node("div", null, "consumer-controls");
      const top = node("div", null, "participation-controls"), bottom = node("div", null, "edit-controls");
      const button = (parent, key, label, title, handler, disabled, cls = "") => {
        const el = node("button", label, cls);
        el.type = "button"; el.title = title; el.dataset.control = key;
        el.setAttribute("aria-label", `${title}: ${c.name}`);
        el.disabled = disabled; el.onclick = handler; parent.append(el); return el;
      };
      const toggle = button(top, "participation", c.enabled ? "Teilnahme beenden" : "Teilnehmen", "Teilnahme umschalten",
        () => this._action("participation", {consumer_id:c.id, enabled:!c.enabled, revision:this._data.revision}),
        !!this._data.pending || this._writing);
      toggle.setAttribute("aria-pressed", String(c.enabled));
      button(top, "up", "↑", "Nach oben", () => this._move(i, -1), locked || i === 0);
      button(top, "down", "↓", "Nach unten", () => this._move(i, 1), locked || i === this._data.consumers.length - 1);
      button(bottom, "edit", "Bearbeiten", "Bearbeiten", () => this._edit(c), locked);
      button(bottom, "remove", "Entfernen", "Entfernen", () => this._remove(c), locked, "danger");
      controls.append(top, bottom); row.append(controls); target.append(row);
    });
    if (focusId && focusAction) {
      const row = Array.from(target.children).find(el => el.dataset.consumer === focusId);
      const button = row && Array.from(row.querySelectorAll("button")).find(el => el.dataset.control === focusAction);
      if (button && !button.disabled) button.focus({preventScroll: true});
    }
  }

  _timerControl(c, timer, label) {
    const wrap = node("div", null, "timer-line");
    wrap.append(node("span", label, "timer-chip"));
    const btn = node("button", "⏭", "timer-skip");
    btn.type = "button";
    btn.title = timer === "minimum" ? "Mindestlaufzeit beenden" : "Wiedereinschaltsperre beenden";
    btn.setAttribute("aria-label", `${btn.title}: ${c.name}`);
    btn.disabled = !!this._data.pending || this._writing;
    btn.onclick = async () => {
      if (this._data.config.confirm_timer_skip !== false && !confirm(`${btn.title} für „${c.name}“? Nur der Timer wird aufgehoben; RRH entscheidet danach regulär.`)) return;
      await this._action("skip_timer", {consumer_id:c.id, timer, revision:this._data.revision});
    };
    wrap.append(btn);
    return wrap;
  }

  _deficitText(c) {
    if (c.min_on_strict && c.min_remaining_s > 0 && c.deficit_remaining_s <= 0) {
      return `Unterlast · Mindestlaufzeit schützt noch ${duration(c.min_remaining_s)}`;
    }
    return c.deficit_remaining_s > 0
      ? `Unterlast · Abschaltung von ${c.name} in ${duration(c.deficit_remaining_s)}`
      : `Unterlast · Abschaltung von ${c.name} fällig`;
  }

  async _move(index, delta) {
    const cfg = copy(this._data.config);
    const consumerId = cfg.consumers[index].id;
    const otherId = cfg.consumers[index + delta].id;
    const firstProfile = cfg.profiles.find(p => p.consumer_ids.includes(consumerId));
    const secondProfile = cfg.profiles.find(p => p.consumer_ids.includes(otherId));
    if (firstProfile && firstProfile.id === secondProfile?.id) {
      const i = firstProfile.consumer_ids.indexOf(consumerId), j = firstProfile.consumer_ids.indexOf(otherId);
      [firstProfile.consumer_ids[i], firstProfile.consumer_ids[j]] = [firstProfile.consumer_ids[j], firstProfile.consumer_ids[i]];
    }
    [cfg.consumers[index], cfg.consumers[index+delta]] = [cfg.consumers[index+delta], cfg.consumers[index]];
    await this._action("configure", {config:cfg, revision:this._data.revision});
    // The write temporarily disables all sort buttons. Restore focus afterwards.
    const row = Array.from(this.$("#consumers").children).find(el => el.dataset.consumer === consumerId);
    const control = delta < 0 ? "up" : "down";
    const sortButton = row?.querySelector(`[data-control="${control}"]`);
    const focusTarget = sortButton && !sortButton.disabled ? sortButton : row?.querySelector('[data-control="edit"]');
    focusTarget?.focus({preventScroll: true});
  }
  async _remove(c) {
    if (!confirm(`Verbraucher "${c.name}" aus RRH entfernen? Die HA-Entität bleibt erhalten. Es wird dadurch kein Schaltbefehl gesendet.`)) return;
    const cfg = copy(this._data.config); cfg.consumers = cfg.consumers.filter(item => item.id !== c.id);
    cfg.profiles = cfg.profiles.map(p => ({...p, consumer_ids:p.consumer_ids.filter(id => id !== c.id)}));
    await this._action("configure", {config:cfg, revision:this._data.revision});
  }
  _toggleTimeFields() {
    this.$("#min-fields").hidden = !this.$("#min-enable").checked;
    this.$("#cool-fields").hidden = !this.$("#cool-enable").checked;
    for (const prefix of ["min", "cool"]) {
      const enabled = this.$(`#${prefix}-enable`).checked;
      for (const unit of ["h", "m", "s"]) this.$(`#${prefix}-${unit}`).disabled = !enabled;
    }
  }
  _toggleDelayField() {
    const enabled = this.$("#override-delay").checked;
    this.$("#override-delay-fields").parentElement.hidden = !enabled;
    this.$("#consumer-delay").disabled = !enabled;
  }
  _renderIconPreview() {
    const target = this.$("#consumer-icon-preview");
    target.replaceChildren(consumerIcon({icon:this.$("#consumer-icon").value || "mdi:power-plug", icon_image:this._editorImage}));
    target.append(node("span", this._editorImage ? "Eigenes Symbol aktiv" : "Vorschau des HA-Symbols", "muted"));
    for(const button of this.shadowRoot.querySelectorAll(".icon-choice")) button.setAttribute("aria-pressed",String(button.dataset.icon===this.$("#consumer-icon").value));
  }
  _setDuration(prefix, seconds) {
    const n = Math.max(0, Math.floor(seconds || 0));
    this.$(`#${prefix}-h`).value = Math.floor(n / 3600);
    this.$(`#${prefix}-m`).value = Math.floor(n % 3600 / 60);
    this.$(`#${prefix}-s`).value = n % 60;
  }
  _getDuration(prefix) {
    return ["h","m","s"].map(unit => Number(this.$(`#${prefix}-${unit}`).value))
      .reduce((total, value, i) => total + value * [3600,60,1][i], 0);
  }
  _toggleConsumerPower(refresh = true, selected = null, stageSelected = null) {
    const mode = this.$("#consumer-power-mode").value;
    this.$("#consumer-staged-fields").hidden = mode !== "staged";
    this.$("#consumer-variable-fields").hidden = mode !== "variable";
    this.$("#consumer-regulation-common").hidden = mode === "fixed";
    const eid = this.$("#consumer-entity");
    const domain = mode === "fixed" ? "switch" : mode === "variable" ? "number" : "switch|select|climate";
    if (refresh) this._options(eid, domain, selected ?? eid.value);
    else if (selected !== null) eid.value = selected;
    const stages = this.$("#consumer-stage-entity");
    this._options(stages, "select|climate", stageSelected ?? stages.value ?? "");
    if (mode === "staged" && !stages.value && /^(select|climate)\./.test(eid.value)) stages.value = eid.value;
    this.$("#consumer-entity-label").firstChild.textContent = mode === "variable" ? "HA-Watt-Sollwert (number)" : mode === "staged" ? "HA-Hauptsteuerung (switch, climate oder select)" : "Vorhandener Schalter";
  }

  _edit(c) {
    this._editorConfig = copy(this._data.config);
    this._editorRevision = this._data.revision;
    this._editorId = c?.id || identifier();
    text(this.$("#editor-title"), c ? "Verbraucher bearbeiten" : "Verbraucher hinzufügen");
    this.$("#consumer-name").value = c?.name || "";
    this.$("#consumer-watts").value = c?.watts ?? "";
    this.$("#consumer-power-mode").value = c?.power_mode || "fixed";
    this.$("#consumer-stage-lines").value = (c?.power_steps || []).map(s => `${s.watts}=${s.option}`).join("\n");
    this.$("#consumer-off-option").value = c?.off_option || "off";
    this.$("#consumer-max-watts").value = c?.max_watts || "";
    this.$("#consumer-power-step").value = c?.power_step_w ?? 10;
    this.$("#consumer-power-hysteresis").value = c?.power_hysteresis_w ?? 100;
    this.$("#consumer-power-interval").value = c?.power_interval_s ?? 10;
    this.$("#consumer-enabled").checked = c?.enabled ?? true;
    this.$("#consumer-icon").value = c?.icon || "mdi:power-plug";
    this._editorImage = c?.icon_image || null;
    this.$("#consumer-image").value = "";
    this._renderIconPreview();
    this.$("#override-delay").checked = c?.shutdown_delay_s != null;
    this.$("#consumer-delay").value = c?.shutdown_delay_s ?? this._data.config.shutdown_delay_s;
    this._toggleDelayField();
    this.$("#min-enable").checked = (c?.min_on_s ?? 0) > 0;
    this.$("#min-strict").checked = c?.min_on_strict ?? false;
    this._setDuration("min", c?.min_on_s ?? 0);
    this.$("#cool-enable").checked = (c?.cooldown_s ?? 0) > 0;
    this.$("#cool-mode").value = c?.cooldown_wait ? "wait" : "skip";
    this._setDuration("cool", c?.cooldown_s ?? 0);
    this._toggleTimeFields();
    this._fillConditionEditor("consumer", c?.conditions);
    this._toggleConsumerPower(true, c?.entity_id || "", c?.stage_entity_id || "");
    text(this.$("#editor-error"), "");
    this.$("#editor").showModal();
    this.$("#consumer-name").focus();
  }
  async _saveConsumer() {
    if (this._writing) return;
    const cfg = copy(this._editorConfig);
    let conditions;
    try { conditions = this._readConditions("consumer"); }
    catch (err) { text(this.$("#editor-error"), err.message); return; }
    const consumer = {id:this._editorId, name:this.$("#consumer-name").value.trim(), entity_id:this.$("#consumer-entity").value, watts:Number(this.$("#consumer-watts").value), enabled:this.$("#consumer-enabled").checked, virtual_confirmed:true,
      min_on_s:this.$("#min-enable").checked ? this._getDuration("min") : 0,
      min_on_strict:this.$("#min-enable").checked && this.$("#min-strict").checked,
      cooldown_s:this.$("#cool-enable").checked ? this._getDuration("cool") : 0,
      cooldown_wait:this.$("#cool-enable").checked && this.$("#cool-mode").value === "wait",
      shutdown_delay_s:this.$("#override-delay").checked ? Number(this.$("#consumer-delay").value) : null,
      icon:this.$("#consumer-icon").value.trim(), icon_image:this._editorImage, conditions,
      power_mode:this.$("#consumer-power-mode").value,
      power_steps:[], stage_entity_id:"", off_option:"off", max_watts:0,
      power_step_w:10, power_hysteresis_w:100, power_interval_s:10};
    if (consumer.power_mode === "staged") {
      consumer.stage_entity_id = this.$("#consumer-stage-entity").value;
      consumer.off_option = this.$("#consumer-off-option").value.trim();
      try {
        consumer.power_steps = this.$("#consumer-stage-lines").value.split(/\r?\n/).map(v => v.trim()).filter(Boolean).map(line => {
          const match = line.match(/^([0-9]+(?:[.,][0-9]+)?)\s*=\s*(.{1,80})$/);
          if (!match) throw Error("Leistungsstufen als '500=1' eingeben, eine Zeile je Stufe.");
          return {watts:Number(match[1].replace(",",".")), option:match[2].trim()};
        });
      } catch(err) { text(this.$("#editor-error"), err.message); return; }
    }
    if (consumer.power_mode === "variable") {
      consumer.max_watts = Number(this.$("#consumer-max-watts").value);
      consumer.power_step_w = Number(this.$("#consumer-power-step").value);
    }
    if (consumer.power_mode !== "fixed") {
      consumer.power_hysteresis_w = Number(this.$("#consumer-power-hysteresis").value);
      consumer.power_interval_s = Number(this.$("#consumer-power-interval").value);
    }
    if ((this.$("#min-enable").checked && !consumer.min_on_s) || (this.$("#cool-enable").checked && !consumer.cooldown_s)) {
      text(this.$("#editor-error"), "Für aktivierte Zeitregeln bitte eine Dauer größer 0 eingeben."); return;
    }
    const existing=cfg.consumers.find(c=>c.id===consumer.id);
    if (!existing || existing.entity_id !== consumer.entity_id || existing.power_mode !== consumer.power_mode || existing.stage_entity_id !== consumer.stage_entity_id) {
      const message = `Steuerentität ausdrücklich freigeben: ${consumer.entity_id} (${consumer.name}). RRH kann diese Entität real schalten. Bei Heizgeräten: unabhängiger Temperaturbegrenzer und elektrische Schutzmaßnahmen erforderlich. Geräte sicher aufstellen. Freigeben?`;
      if (!confirm(message)) return;
    }
    const index = cfg.consumers.findIndex(c => c.id === consumer.id);
    if (index < 0) {
      cfg.consumers.push(consumer);
      // Preserve the original behaviour for the migrated single Standard
      // profile. With multiple custom profiles, explicit assignment is safer.
      if (cfg.profiles.length === 1 && cfg.profiles[0].id === "standard")
        cfg.profiles[0].consumer_ids.push(consumer.id);
    } else cfg.consumers[index] = consumer;
    this.$("#save-consumer").disabled = true;
    const ok = await this._action("configure", {config:cfg, revision:this._editorRevision});
    this.$("#save-consumer").disabled = false;
    if (ok) this.$("#editor").close();
    else text(this.$("#editor-error"), this.$("#command-error").textContent);
  }
}
if (!customElements.get("rrh-hood-panel")) customElements.define("rrh-hood-panel", RrhHoodPanel);
