# Preguntas frecuentes

**¿Hace falta una automatización de simulación?** No. En uso normal RRH utiliza un sensor real de potencia de red; la demo está separada.

**¿Por qué una carga sigue encendida si el excedente baja a cero?** El consumo de esa carga ya aparece reflejado en la medida de red y no debe descontarse dos veces.

**¿Pausa apaga los dispositivos?** No. Usa Apagar todo y verifica su estado.

**¿Las cifras de costes equivalen a la factura?** No: son estimaciones con potencia nominal y tarifas configuradas.

---

[Inicio](index.md) | [Seguridad](safety.md)


## FAQ de la versión 0.9.5

- ¿Por qué no arranca una carga con excedente? Comprueba el perfil, ambos horarios, los sensores, el tiempo de espera y el medidor de red. El estado indica el motivo.
- ¿Cómo permitir lunes 22:00 hasta martes 02:00? Marca lunes e introduce 22:00–02:00. El día es el de inicio y el fin queda excluido.
- ¿Se permiten varias franjas? Sí. Una franja basta dentro de su horario, pero los horarios de perfil y consumidor deben cumplirse ambos.
- ¿Apaga RRH al terminar? Sí, las cargas activas que controla incluso durante el tiempo mínimo. No asume equipos encendidos externamente.
- ¿Hay notificaciones móviles o altavoces? No, están previstas para una versión posterior.
