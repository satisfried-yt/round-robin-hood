# Instalação e atualizações

Antes de atualizar, utilize **Desligar tudo** e confirme fisicamente que todos os aparelhos estão desligados. A pausa não corta a alimentação. Crie uma cópia de segurança completa do Home Assistant, incluindo `.storage`.

Para instalação nova, copie `custom_components/round_robin_hood` para `/config/custom_components/`, reinicie o Home Assistant Core e adicione a integração em **Definições > Dispositivos e serviços**. Depois use o painel lateral do RRH.

Para atualizar de **0.9.4**, siga `docs/UPDATE_0.9.5.md`. Para reverter, restaure **em conjunto** o código e o ficheiro correspondente de `.storage` com o HA Core parado; os dados alterados depois da cópia serão perdidos.

---

[Início](index.md) | [Segurança](safety.md)


## Atualizar de 0.9.4 para 0.9.5

- Use Desligar tudo no RRH e confirme cada dispositivo. Pausa não desliga os consumidores.
- Crie uma cópia de segurança completa do Home Assistant, incluindo /config/.storage. Escolha Sempre desligado se não pretender arranque automático durante a atualização.
- Instale v0.9.5 pelo HACS/Marketplace ou pelo pacote oficial GitHub. Manualmente, substitua apenas custom_components/round_robin_hood. Consulte docs/UPDATE_0.9.5.md para atualização e reversão.
- Reinicie HA Core e verifique consumidores, perfis, condições, estatísticas, pesquisa de entidades e horários.
- Os novos horários começam desativados. Para reverter, restaure o código e o .storage correspondentes com o HA Core parado.
