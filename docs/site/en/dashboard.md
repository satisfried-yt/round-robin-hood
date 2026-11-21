# Dashboard – every card and action

## Operation controls

| Indicator/action | Meaning |
|---|---|
| **Operation** | Current controller state and any blocking reason. |
| **RRH ON** | Starts automatic allocation if configuration and fresh grid reading are valid; it may turn on real authorized devices. |
| **All OFF** | Requests OFF for RRH-managed devices; verify actual feedback. Not a certified physical emergency stop. |
| **Pause** | Suspends allocation; **existing loads may stay running**. |

## Metrics and money

| Card | Definition, unit and limitation |
|---|---|
| **Grid export** | Signed measured grid power in W; negative values mean import. Observe reading freshness. |
| **Additional available** | Positive export minus reserved watts, floored at 0 W. |
| **Total budget** | Additional available plus confirmed currently RRH-managed W; estimate, not a meter. |
| **Estimated managed power** | Sum of confirmed ON consumers' configured ratings in W. |
| **Net benefit now** | Estimated RRH-controlled kW × (purchase – feed-in tariff), **currency per hour**; live rate, not cumulative. Missing tariffs show “—”. |
| **Accumulated net benefit** | Historical estimated credited energy value minus forgone feed-in income, not a guaranteed invoice saving. |
| **RRH-used surplus** | Estimated integrated RRH-attributed PV energy in kWh. |
| **Surplus utilization ratio** | Current managed load watts / reconstructed available positive surplus watts as a percentage; unavailable with invalid input. |
| **PV power** | Optional independent HA PV production sensor in W; installed nominal watts shown below where set. |

## Full-width live chart

The chart stretches over the full content row and offers **gauge, line, bar, area, donut, stacked and sparkline**. It depicts estimated capture percentage, not overall solar production. Hide/show any dashboard metric from **Settings → Dashboard appearance & language**. The chart stays full row when other cards are hidden.

## Current allocation order

Profiles are shown in their priority order; member chips show physical state, planned watts, confirmed allocation, conditions and waiting reasons. Green marks confirmed RRH-owned ON consumers. Conditions may block an entire profile even with surplus. See [Profiles](profiles.md) and [Energy & costs](energy.md).

## Features and usage

The dashboard now shows the international tagline **Power your home. Not their profits.** / **Less to the grid. More for the little guy.** The estimated live monetary benefit is displayed **per hour** with two decimal places; it is not a certified savings measurement. Estimated RRH-used surplus is also shown with two decimal places in kWh.

The optional **Buy me a drink** link below lifetime net benefit opens an external donation page only when clicked; hide it under **Settings → Dashboard**.

**Control loop:** If a rated 500 W device starts with 500 W net export and measured export consequently drops to 0 W, RRH must not stop it for that reason alone. Additional available power is the **current** positive export less reserve. Running owned watts are added only for estimated overall potential. Genuine import is handled by the configured deficit-shedding protections.

## Features and usage

The optional donation link beneath **Total net advantage** now says **“Buy me a drink”**. Its information icon displays a hover/tap hint: **“Large amounts of rum and cola fueled this project. That isn't free.”** RRH embeds no third-party donation content until the external link is opened. Disable the link under **Settings → Dashboard** at any time.

