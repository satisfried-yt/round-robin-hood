# Condiciones de sensores

Las condiciones comparan una entidad numérica HA mediante `<`, `<=`, `>` o `>=` con un umbral y una **histéresis**. Los grupos **TODAS** y **CUALQUIERA** combinan condiciones de un consumidor o perfil.

Si el sensor está `unknown` o `unavailable`, la condición no autoriza un nuevo arranque. Una condición de temperatura de software no sustituye un limitador independiente de sobretemperatura.

---

[Inicio](index.md) | [Seguridad](safety.md)


## Combinar condiciones de sensores y horarios (0.9.5)

Las condiciones numéricas y los horarios semanales se activan por separado. Las reglas de sensores conservan Y/O; el horario siempre se añade mediante Y.

Un consumidor inicia solo si el perfil está activo, el horario del perfil lo permite, su horario individual lo permite y se cumplen las condiciones numéricas aplicables.

Un sensor inválido impide el inicio. Al terminar la franja, RRH apaga las cargas que controla sin esperar el tiempo mínimo. Las reglas de software no sustituyen protecciones independientes.

Busca entidades numéricas con el selector Home Assistant. Configura las franjas en los editores de perfiles y consumidores.
