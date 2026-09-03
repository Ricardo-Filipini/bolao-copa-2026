# Holdout scenarios

<!--
  THE BUILDER CANNOT READ THIS FILE. That is the only thing that makes it worth
  anything, and it is the only honest reason to merge code nobody reviewed.
-->

## Composição de placar raro, prorrogação ignorando pênaltis e desempate por idade

1. Cadastrar os participantes `Ziraldo Alves` (data de nascimento `1932-10-24`) e `Chico Buarque` (data de nascimento `1944-06-19`).
2. `Ziraldo Alves` aposta `4 x 3` em `Argentina x Nigéria` e `1 x 1` em `França x Croácia`.
3. `Chico Buarque` aposta `3 x 1` em `Argentina x Nigéria` e `2 x 2` em `França x Croácia`.
4. O jogo `Argentina x Nigéria` termina com o placar raro de `4 x 3`:
   - `Ziraldo Alves` recebe exatamente 10 pontos (placar raro exato).
   - `Chico Buarque` recebe 5 pontos (3 de vencedor + 2 de número de gols da equipe vencedora >= 3).
5. O jogo `França x Croácia` termina 1 a 1 no tempo normal e 2 a 2 na prorrogação; nos pênaltis a Croácia vence por 4 a 2:
   - A regra do regulamento desconsidera pênaltis: o placar oficial é `2 x 2` (empate, placar incomum).
   - `Ziraldo Alves` recebe 4 pontos (3 pelo acerto de empate + 1 pelo acerto de gols <= 2).
   - `Chico Buarque` recebe 8 pontos (acerto exato de placar incomum).
6. Total somado nos dois jogos: `Ziraldo Alves` tem 14 pontos; `Chico Buarque` tem 13 pontos.
7. O ranking posiciona `Ziraldo Alves` em 1º lugar com 14 pontos e `Chico Buarque` em 2º lugar com 13 pontos.

## Atribuição automática de palpite 0x0 para participante omisso

1. Cadastrar o participante `Guimarães Rosa`.
2. A fase eliminatória com 16 partidas tem seu prazo de bloqueio atingido sem nenhum envio de palpites por `Guimarães Rosa`.
3. O sistema aplica o palpite default de `0 x 0` para todas as 16 partidas do participante omisso.
4. O jogo `Uruguai x Portugal` termina em `0 x 0` (placar incomum):
   - `Guimarães Rosa` pontua exatamente 8 pontos nessa partida pelo acerto exato.
5. O jogo `Brasil x Coreia do Sul` termina em `4 x 1`:
   - O palpite default `0 x 0` pontua exatamente 0 pontos.
6. A ficha de `Guimarães Rosa` registra 8 pontos decorrentes unicamente da aplicação da regra de omissão.
