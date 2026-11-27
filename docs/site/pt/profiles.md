# Perfis e estratégias

Todos os perfis partilham um único orçamento de potência; a **prioridade** determina a ordem de distribuição. Cada perfil define participantes, estratégia e respetivas opções. Condições de sensores podem bloquear a entrada do perfil.

As oito estratégias estão descritas abaixo. Conforme a estratégia pode configurar passagem de consumidores sem potência suficiente, janelas de tempo, rotação, melhoria mínima e intervalo de otimização.

## Perfis e estratégias

- Round Robin clássico: alternaência dos consumidores elegíveis.
- Tempo justo: prioridade ao menor tempo confirmado.
- Energia justa: prioridade a menos Wh estimados recebidos.
- Prioridade fixa: respeita a ordem configurada.
- Eficiência máxima: combina cargas para aproveitar melhor o excedente.
- Potência crescente: cargas pequenas primeiro.
- Potência decrescente: cargas grandes primeiro.
- Operação estável: evita comutações desnecessárias.

---

[Início](index.md) | [Segurança](safety.md)


## Horários semanais por perfil (desde 0.9.5)

Em Perfis → Editar, ative um horário independente para o perfil. Cada período permite vários dias, início, fim e vários períodos no mesmo dia.

Os horários do perfil e do consumidor são independentes. Um início requer perfil ativo, ambos os horários permitidos e condições dos sensores válidas. A estratégia escolhe depois a carga elegível.

Quando o período do perfil termina, o RRH solicita o desligamento confirmado dos dispositivos ativos que gere; vários podem usar o desligamento em grupo. Dispositivos ligados externamente não são assumidos.

Períodos que atravessam a meia-noite pertencem ao dia inicial. Usa-se o fuso horário de Home Assistant com mudanças de hora. O painel mostra a próxima abertura.
