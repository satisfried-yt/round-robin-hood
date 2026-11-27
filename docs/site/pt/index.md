# Round Robin Hood - Início

**Version 0.9.5** | [Deutsch](../) | [English](../en/)

Round Robin Hood (RRH) distribui o excedente solar medido por consumidores autorizados, de acordo com as potências nominais e os perfis. A entrada principal é a potência instantânea de rede (W ou kW), não um contador de energia em kWh.

**Segurança:** RRH pode controlar equipamentos reais. Não substitui proteções elétricas ou térmicas independentes nem um corte físico de emergência. Falhas podem causar custos, sobreaquecimento ou incêndio.

## Início

- [Instalação e atualizações](installation.md)
- [Configuração](setup.md)
- [Painel](dashboard.md)
- [Consumidores](consumers.md)
- [Perfis e estratégias](profiles.md)
- [Condições de sensores](conditions.md)
- [Energia e custos](energy.md)
- [Definições](settings.md)
- [Sensores do Home Assistant](sensors.md)
- [Comportamento no reinício](startup.md)
- [Resolução de problemas](troubleshooting.md)
- [Segurança](safety.md)
- [Perguntas frequentes](faq.md)
- [Glossário](glossary.md)
- [Sobre](about.md)


## Novidades da versão 0.9.5

- Seleção pesquisável de entidades Home Assistant nas definições, assistente, consumidores, condições e energia, também em telemóveis.
- Horários semanais opcionais para perfis e consumidores, com dias à escolha, vários períodos e intervalos que atravessam a meia-noite.
- As condições dos sensores e ambos os horários devem permitir o funcionamento. Ao terminar o período, o RRH desliga os dispositivos que gere mesmo antes do tempo mínimo.
- A configuração existente é mantida e os horários começam desativados. Faça um backup completo de HA, incluindo .storage, antes de atualizar.
