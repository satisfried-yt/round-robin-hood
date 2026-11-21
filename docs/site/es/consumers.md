# Consumidores

Para cada consumidor define **nombre**, **icono**, **entidad HA de control** y **potencia nominal (W)**. No reutilices la misma entidad en varios consumidores RRH. Las tarjetas muestran estado confirmado, participación, potencia y motivo de espera.

Tipos admitidos: **interruptor**, **varias etapas** y **regulación continua**. Configura potencia y acciones de apagado por etapa; comprueba que el valor `0` de una entidad `number` apaga realmente el equipo. Las duraciones mínimas y el tiempo de reactivación protegen frente a cambios rápidos.

Eliminar un consumidor de RRH no elimina la entidad correspondiente en Home Assistant.

---

[Inicio](index.md) | [Seguridad](safety.md)
