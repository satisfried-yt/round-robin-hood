# Resolução de problemas

Se o RRH não retomar, reveja o modo de arranque, medição da rede (sinal, unidade, atualização), estados dos dispositivos e **registos do Home Assistant**. Um atuador indisponível pode bloquear o arranque.

Se não houver cargas ativas, reveja potência disponível, reserva, perfis, condições e temporizadores. Se o preço não aparecer na seleção, verifique a unidade. Se a atualização falhar, não repita cegamente o comando: use o procedimento de reposição e a cópia.

---

[Início](index.md) | [Segurança](safety.md)


## Resolução de problemas: horários e pesquisa (0.9.5)

Não arranca com excedente: consulte os estados do perfil e consumidor. Ambos os horários e os sensores têm de permitir. Verifique também o medidor, reserva, watts e bloqueio de religação.

Hora ou dia inesperado: confirme o fuso horário do Home Assistant. Períodos noturnos pertencem ao dia de início. Mudanças de hora podem omitir ou repetir horas locais.

Entidade ausente: confirme entidade, domínio e unidade compatíveis. As referências anteriores mantêm-se quando possível. Se surgir a interface antiga, atualize a cache e reinicie HA.

Se faltar confirmação de desligamento, verifique o dispositivo físico e os registos HA. RRH não é um corte elétrico de emergência.
