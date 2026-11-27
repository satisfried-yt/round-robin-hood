# Round Robin Hood - Inicio

**Version 0.9.5** | [Deutsch](../) | [English](../en/)

Round Robin Hood (RRH) distribuye el excedente solar medido entre consumidores autorizados, según sus potencias nominales y perfiles. El dato principal es la potencia de red instantánea (W o kW), no un contador de energía en kWh.

**Seguridad:** RRH puede controlar equipos reales. No sustituye protecciones eléctricas ni térmicas independientes ni un interruptor físico de emergencia. Los fallos pueden provocar costes inesperados, sobrecalentamiento o incendios.

## Inicio

- [Instalación y actualizaciones](installation.md)
- [Configuración](setup.md)
- [Panel de control](dashboard.md)
- [Consumidores](consumers.md)
- [Perfiles y estrategias](profiles.md)
- [Condiciones de sensores](conditions.md)
- [Energía y costes](energy.md)
- [Ajustes](settings.md)
- [Sensores de Home Assistant](sensors.md)
- [Comportamiento tras reinicio](startup.md)
- [Solución de problemas](troubleshooting.md)
- [Seguridad](safety.md)
- [Preguntas frecuentes](faq.md)
- [Glosario](glossary.md)
- [Acerca de](about.md)


## Novedades de la versión 0.9.5

- Selección de entidades Home Assistant con búsqueda en ajustes, asistente, consumidores, condiciones y energía, también desde móviles.
- Horarios semanales opcionales para perfiles y consumidores con días seleccionables, varias franjas y periodos que cruzan medianoche.
- Deben cumplirse las condiciones de sensores y ambos horarios. Cuando termina una franja, RRH apaga los equipos que controla, incluso antes del tiempo mínimo.
- Se conserva la configuración y los horarios empiezan desactivados. Guarda una copia completa de HA, incluida .storage, antes de actualizar.
