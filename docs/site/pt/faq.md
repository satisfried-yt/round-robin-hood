# Perguntas frequentes

**Preciso de criar uma simulação?** Não. A utilização normal usa a medição de rede; a demo é opcional.

**Por que permanece uma carga ligada com exportação 0 W?** A carga já está refletida na medição, não sendo descontada novamente.

**Pausar desliga fisicamente?** Não. Use Desligar tudo e confirme.

**As estatísticas são valores de fatura?** Não, são estimativas a partir de potências nominais e tarifas.

---

[Início](index.md) | [Segurança](safety.md)


## FAQ da versão 0.9.5

- Porque não arranca um consumidor apesar do excedente? Verifique o perfil, ambos os horários, sensores, bloqueio de religação e medidor. O estado mostra a razão.
- Como permitir segunda 22:00 até terça 02:00? Escolha segunda e 22:00–02:00. O dia indica o início e a hora final é exclusiva.
- São possíveis vários períodos? Sim. Basta um período dentro do mesmo horário, mas os horários do perfil e consumidor têm ambos de permitir.
- O RRH desliga no fim? Sim, os consumidores ativos que gere, mesmo durante o tempo mínimo. Não assume dispositivos ligados externamente.
- Há notificações para telemóveis/colunas? Não, estão previstas para uma versão futura.
