# Instalación y actualizaciones

Antes de actualizar, pulsa **Apagar todo** y comprueba que los equipos están apagados físicamente. Pausar no desconecta la corriente. Crea una copia de seguridad completa de Home Assistant, incluido `.storage`.

Para una instalación nueva, copia `custom_components/round_robin_hood` a `/config/custom_components/`, reinicia Home Assistant Core y agrega la integración desde **Ajustes > Dispositivos y servicios**. A continuación, configura RRH desde su panel lateral.

Para actualizar desde **0.9.4**, utiliza las instrucciones de `docs/UPDATE_0.9.5.md`. Para volver atrás restaura **juntos** el código y el archivo de datos RRH de `.storage`, con Home Assistant Core detenido. Las modificaciones posteriores a la copia se perderán.

---

[Inicio](index.md) | [Seguridad](safety.md)


## Actualizar de 0.9.4 a 0.9.5

- Usa Apagar todo en RRH y comprueba físicamente cada actuador. Pausar no apaga las cargas.
- Guarda una copia completa de Home Assistant, incluida /config/.storage. Selecciona Siempre apagado si no quieres un inicio automático durante la actualización.
- Instala v0.9.5 mediante HACS/Marketplace o el paquete oficial de GitHub. Manualmente, sustituye solo custom_components/round_robin_hood. Consulta docs/UPDATE_0.9.5.md para los pasos y la restauración.
- Reinicia HA Core y comprueba consumidores, perfiles, condiciones, estadísticas, búsqueda de entidades y horarios.
- Los horarios nuevos empiezan desactivados. Para volver atrás, restaura código y .storage de la misma copia con HA Core detenido.
