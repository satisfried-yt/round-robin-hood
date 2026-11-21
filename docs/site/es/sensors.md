# Sensores de Home Assistant

La **fuente de red** debe ser una potencia instantánea W/kW. Un contador kWh no sirve para controlar excedentes. Comprueba el signo en las herramientas de Home Assistant.

Los **precios** requieren valores numéricos con unidades compatibles por kWh (p. ej. `EUR/kWh` o `ct/kWh`). La potencia FV utiliza W/kW y los contadores de energía Wh/kWh/MWh. Los valores `unknown`, `unavailable` y no numéricos no son válidos. Para arrancar de forma segura tras reiniciar HA se necesita una nueva medida, no solo un valor restaurado.

---

[Inicio](index.md) | [Seguridad](safety.md)
