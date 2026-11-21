# Consumidores

Cada consumidor possui **nome**, **ícone**, **entidade de controlo HA** e **potência nominal (W)**. A entidade de comando não deve ser atribuída a dois consumidores RRH. Os cartões mostram estado confirmado, participação e razões de espera.

Tipos: **interruptor**, **multi-estágio** e **potência ajustável continuamente**. Configure a potência e a ação de desligar de cada nível. Verifique que `number: 0` desliga realmente o aparelho. Tempo mínimo de funcionamento e intervalo de reinício evitam comutações repetidas.

Remover um consumidor do RRH não elimina a entidade do Home Assistant.

---

[Início](index.md) | [Segurança](safety.md)
