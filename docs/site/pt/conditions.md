# Condições de sensores

As condições usam um sensor HA numérico, comparação (`<`, `<=`, `>`, `>=`), limite e **histerese**. Pode combinar regras do perfil ou consumidor com **TODAS** ou **QUALQUER**.

Sensores `unknown` ou `unavailable` não autorizam novo arranque. Uma condição de temperatura via software não substitui um limitador térmico independente.

---

[Início](index.md) | [Segurança](safety.md)


## Combinar condições de sensores e horários (0.9.5)

As condições numéricas e os horários semanais são ativados separadamente. As regras de sensores mantêm E/OU; o horário é sempre uma condição E adicional.

Um consumidor só inicia com perfil ativo, horário do perfil permitido, horário do consumidor permitido e condições numéricas aplicáveis cumpridas.

Um sensor inválido impede o início. No fim do período, o RRH desliga os dispositivos que gere sem esperar pelo tempo mínimo. Estas regras não substituem proteções independentes.

Procure entidades numéricas no seletor Home Assistant. Configure os períodos nos editores de perfil e consumidor.
