# Instalación y actualizaciones

Antes de actualizar, pulsa **Apagar todo** y comprueba que los equipos están apagados físicamente. Pausar no desconecta la corriente. Crea una copia de seguridad completa de Home Assistant, incluido `.storage`.

Para una instalación nueva, copia `custom_components/round_robin_hood` a `/config/custom_components/`, reinicia Home Assistant Core y agrega la integración desde **Ajustes > Dispositivos y servicios**. A continuación, configura RRH desde su panel lateral.

Para actualizar desde **0.9.2**, utiliza las instrucciones de `docs/UPDATE_0.9.3.md`. Para volver atrás restaura **juntos** el código y el archivo de datos RRH de `.storage`, con Home Assistant Core detenido. Las modificaciones posteriores a la copia se perderán.

---

[Inicio](index.md) | [Seguridad](safety.md)
