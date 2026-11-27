# Consumidores

Para cada consumidor define **nombre**, **icono**, **entidad HA de control** y **potencia nominal (W)**. No reutilices la misma entidad en varios consumidores RRH. Las tarjetas muestran estado confirmado, participación, potencia y motivo de espera.

Tipos admitidos: **interruptor**, **varias etapas** y **regulación continua**. Configura potencia y acciones de apagado por etapa; comprueba que el valor `0` de una entidad `number` apaga realmente el equipo. Las duraciones mínimas y el tiempo de reactivación protegen frente a cambios rápidos.

Eliminar un consumidor de RRH no elimina la entidad correspondiente en Home Assistant.

---

[Inicio](index.md) | [Seguridad](safety.md)


## Nuevo en 0.9.5: búsqueda y horario del consumidor

En Consumidores → Editar, selecciona las entidades de control y etapas mediante el selector Home Assistant con búsqueda por nombre o ID. Se mantienen las selecciones existentes.

Activa el horario solo si lo necesitas. Añade varias franjas, marca los días lun–dom y escribe inicio y fin (HH:MM). Si está desactivado no limita el uso.

Para lunes 22:00–martes 02:00, marca lunes como día inicial. La hora de fin queda excluida. Varias franjas se unen con O; el horario del perfil y las condiciones de sensores también deben cumplirse (Y).

Al terminar la franja RRH apaga los consumidores activos que gestiona incluso durante el tiempo mínimo estricto. No sustituye protecciones independientes. El siguiente inicio se muestra en la zona horaria de HA.
