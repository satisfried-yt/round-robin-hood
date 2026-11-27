# Solución de problemas

Si RRH no se activa tras reiniciar, comprueba la política de inicio, el sensor de red (signo, unidades, fecha de actualización), estados de dispositivos y **registros de Home Assistant**. Una entidad indisponible puede bloquear el arranque automático.

Si no se conectan consumidores, revisa la reserva, la potencia disponible, perfiles, condiciones, temporizadores y confirmaciones. Si una entidad de tarifa no aparece, comprueba su unidad. Tras un error de instalación no repitas ciegamente los comandos: revisa la salida y usa el procedimiento de reversión.

---

[Inicio](index.md) | [Seguridad](safety.md)


## Solución de problemas: horarios y búsqueda (0.9.5)

No arranca con excedente: consulta el estado del perfil y consumidor. Deben cumplirse ambos horarios y los sensores. Comprueba también el medidor, reserva, potencia y bloqueo de reinicio.

Hora o día inesperado: verifica la zona horaria de Home Assistant. Las franjas nocturnas corresponden al día de inicio. Un cambio horario puede omitir o repetir horas locales.

Entidad ausente: comprueba entidad, dominio y unidad compatibles. Se conservan referencias anteriores cuando es posible. Si aparece la interfaz vieja, actualiza la caché y reinicia HA.

Si falla la confirmación de apagado, revisa el actuador real y los registros HA. RRH no es un interruptor de emergencia.
