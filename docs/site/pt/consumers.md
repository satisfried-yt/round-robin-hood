# Consumidores

Cada consumidor possui **nome**, **ícone**, **entidade de controlo HA** e **potência nominal (W)**. A entidade de comando não deve ser atribuída a dois consumidores RRH. Os cartões mostram estado confirmado, participação e razões de espera.

Tipos: **interruptor**, **multi-estágio** e **potência ajustável continuamente**. Configure a potência e a ação de desligar de cada nível. Verifique que `number: 0` desliga realmente o aparelho. Tempo mínimo de funcionamento e intervalo de reinício evitam comutações repetidas.

Remover um consumidor do RRH não elimina a entidade do Home Assistant.

---

[Início](index.md) | [Segurança](safety.md)


## Novo em 0.9.5: pesquisa e horário do consumidor

Em Consumidores → Editar, selecione entidades de controlo e etapas no seletor pesquisável Home Assistant por nome ou ID. As escolhas anteriores mantêm-se.

Ative o horário apenas se necessário. Adicione vários períodos, escolha os dias seg–dom e defina início e fim (HH:MM). Um horário desativado não restringe a operação.

Para segunda 22:00–terça 02:00, escolha segunda como dia de início. A hora final é exclusiva. Vários períodos usam OU; o horário do perfil e as condições dos sensores também devem permitir (E).

Quando um período termina, o RRH desliga o consumidor ativo que gere mesmo com tempo mínimo estrito. Não substitui proteção elétrica ou térmica independente. A próxima abertura usa o fuso horário HA.
