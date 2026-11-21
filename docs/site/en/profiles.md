# Profiles, priorities and strategies

A profile groups unique consumers; a consumer can belong to one profile only (except a separately assigned residual-surplus load). Profiles have ordered priority and, under safety constraints, a higher-priority profile may reclaim power from a lower one.

## Eight strategies

| Strategy | Behavior | Use case |
|---|---|---|
| **Classic Round Robin** | Rotate in fixed order; Strict or Skip when a load will not fit. | Cyclic sharing. |
| **Fair Runtime** | Prioritize lowest confirmed RRH operating time; minimum gap/rotation delay limits thrashing. | Balanced running hours. |
| **Fair Energy** | Prioritize least estimated credited Wh (declared W × runtime); uses a separate minimum credit gap. | Consumers of differing wattage. |
| **Fixed Priority** | Highest listed eligible load first, Strict or Skip if insufficient power. | Predictable priority. |
| **Maximum Efficiency** | Select a combination yielding greater surplus utilization; at most 24 consumers per profile. | Maximize use of available watts. |
| **Power Ascending** | Prefer lower-watt loads; Strict or Skip. | Favor smaller appliances. |
| **Power Descending** | Prefer larger-watt loads; Strict or Skip. | Favor larger appliances. |
| **Stable Operation** | Favor continuity, avoid avoidable switching. | Loads sensitive to repeated starts. |

## Profile editor fields and defaults

| Field | Meaning / default |
|---|---|
| **Name / enabled** | Unique display label and profile participation toggle. |
| **Priority ↑/↓** | Profile order, separate from consumer ordering. |
| **Member list** | Unique consumer assignment across profiles. |
| **Strategy** | Allocation algorithm; relevant options nested inside one bordered group. |
| **Dashboard order** | Fixed or dynamic order where supported. |
| **Strict / Skip** | Strict can block later eligible loads when a candidate does not fit; Skip may proceed to a fitting one. Not available for every strategy. |
| **Fair comparison period** | Lifetime or fixed 24 h, 7 d, 14 d, 30 d. The wall-clock period does not stop during Pause. |
| **Fair rotation interval** | Minimum time between elective rotations, default **900 s** (60–86400). |
| **Fair runtime gap** | Minimum credited time advantage, default **60 s**. |
| **Fair energy gap** | Minimum credited energy advantage, default **10 Wh**. |
| **Efficiency minimum gain** | Required extra watt usage, default **200 W**. |
| **Optimization interval** | Minimum spacing between optimizations, default **60 s** (10–3600). |
| **Efficiency start margin** | Extra safe startup headroom, default **50 W**. |
| **Sensor conditions** | Profile-level ALL/ANY predicates and hysteresis. |
| **Reset fairness credit** | Resets selected fair score only; energy/money ledger and other score remain intact. |

Fair scores count only confirmed RRH allocation while the associated fair strategy is operating, not all lifetime appliance hours. Minimum-run, cooldown, data-quality rules and **All OFF** still apply. See [Conditions](conditions.md).

## Profile participants

The profile editor groups member selection and base order inside the labelled **Profile participants** fieldset. This is a presentation change; profile priority and strategy behaviour are unchanged.
