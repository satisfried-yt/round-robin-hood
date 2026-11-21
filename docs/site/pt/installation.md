# Instalação e atualizações

Antes de atualizar, utilize **Desligar tudo** e confirme fisicamente que todos os aparelhos estão desligados. A pausa não corta a alimentação. Crie uma cópia de segurança completa do Home Assistant, incluindo `.storage`.

Para instalação nova, copie `custom_components/round_robin_hood` para `/config/custom_components/`, reinicie o Home Assistant Core e adicione a integração em **Definições > Dispositivos e serviços**. Depois use o painel lateral do RRH.

Para atualizar de **0.9.2**, siga `docs/UPDATE_0.9.3.md`. Para reverter, restaure **em conjunto** o código e o ficheiro correspondente de `.storage` com o HA Core parado; os dados alterados depois da cópia serão perdidos.

---

[Início](index.md) | [Segurança](safety.md)
