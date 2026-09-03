# End-to-end journeys

Each journey describes a real user interacting with the Bolão da Copa 2026 application through its HTTP interface.

---

## O participante envia o palpite de campeão e palpites da primeira fase respeitando a cota de 25%

1. Acessar a tela inicial do bolão e cadastrar o participante `Carlos Drummond`.
2. Registrar o palpite de campeão da copa como `Brasil`.
3. Preencher palpites para as partidas da primeira fase garantindo no máximo 18 partidas com placar `2 x 1` ou `1 x 2` (25% de 72).
4. Submeter a cartela de palpites da fase.
5. Recarregar a página de palpites e confirmar que todos os 72 jogos permanecem preenchidos e a contagem de palpites 2x1/1x2 exibe `18 de 18 utilizados`.

**O que faria falhar:** O sistema permitir submeter um 19º palpite com placar 2x1 ou 1x2 na primeira fase, ou os palpites não serem persistidos após o recarregamento.

## O organizador bloqueia a fase e os palpites de todos os concorrentes ficam públicos

1. O administrador aciona o bloqueio da `1ª Fase - Fase de Grupos`.
2. O participante `Carlos Drummond` tenta alterar seu palpite do jogo `México x África do Sul`.
3. O sistema rejeita a alteração com erro de fase bloqueada.
4. Outro participante (`Clarice Lispector`) acessa a visão da tabela do bolão e consegue visualizar integralmente os placares apostados por `Carlos Drummond`.

**O que faria falhar:** O sistema aceitar modificações de palpites com a fase já bloqueada, ou ocultar os palpites dos demais concorrentes após o travamento oficial.

## Apuração de partida com placar incomum e atualização do ranking geral

1. O administrador cadastra o resultado oficial do jogo `Espanha x Holanda` como `3 x 0` (placar incomum, valendo 8 pontos).
2. O participante que apostou exatamente `3 x 0` tem 8 pontos somados em seu saldo.
3. O participante que apostou `1 x 0` (acertou apenas o vencedor com margem simples) tem 3 pontos somados.
4. A tabela de ranking geral é consultada e reflete a nova ordem de pontuação imediatamente.

**O que faria falhar:** Um placar `3 x 0` pontuar como ordinário (7 pontos) em vez de incomum (8 pontos), ou a tabela de ranking não atualizar as posições relativas.
