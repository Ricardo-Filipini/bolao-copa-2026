# Mission

**Derived from:** Documento Oficial de Regras do Bolão da Copa 2026 (Confraria do Café do Deinf)
**Last reconciled with it:** 2026-09-02

## What Bolão Copa 2026 is

O Bolão Copa 2026 é um aplicativo web voltado ao gerenciamento completo de palpites e apuração de resultados para centenas de participantes da Confraria do Café. Ele permite registrar o palpite de campeão e os palpites de cada partida por fases, valida estritamente a cota de 25% de placares 2x1/1x2, bloqueia atualizações antes do início das rodadas, calcula pontuações segundo a raridade dos placares (ordinário, incomum, raro, gols e resultado considerando prorrogação e ignorando pênaltis) e mantém o ranking geral e por fases com critérios determinísticos de desempate e rateio de premiações.

O sistema é concebido como uma instância única, single-tenant, focada na estabilidade e integridade dos palpites e na transparência do ranking para todos os participantes.

## Who it is for

- Participantes do bolão que buscam registrar seus palpites e acompanhar seus pontos e posições no ranking geral e das fases em tempo real.
- Organizadores e administradores responsáveis por homologar participantes, bloquear fases e cadastrar os placares oficiais das partidas.

Bolão Copa 2026 is not uma casa de apostas com dinheiro real nem uma plataforma multi-torneios.

## Core capabilities (in scope)

The factory may accept issues in these areas.

**Gestão de Participantes e Palpite de Campeão**
- Cadastro de participantes com chave única e data de nascimento (para desempate de idade).
- Registro do palpite de campeão da Copa (vale 10 pontos ao final) até a data limite da 1ª fase.

**Registro e Validação de Palpites por Fase**
- Preenchimento dos 72 jogos da fase de grupos e jogos das fases eliminatórias.
- Validação automática da trava de 25% de palpites 2x1 e 1x2 nas fases regulamentadas (máx 18 na 1ª fase, 4 na 2ª, 2 nas oitavas, 1 nas quartas).
- Aplicação do palpite padrão "0 x 0" em todas as partidas da fase caso o participante não envie a tempo.

**Bloqueio de Fases e Visibilidade**
- Travamento de submissão 1 dia antes do primeiro jogo de cada fase.
- Liberação pública da visualização dos palpites de todos os concorrentes assim que a fase é bloqueada.

**Motor de Pontuação e Regras Especiais**
- Pontuação de acerto de campeão (10 pts).
- Pontuação por partida: placar ordinário (7 pts), incomum (8 pts), raro (10 pts), acerto de gols (1 ou 2 pts), resultado seco (3 pts), e combinações (4 ou 5 pts).
- Cômputo do placar após prorrogação e desconsideração explícita de disputas por pênaltis (empate na prorrogação permanece empate).
- Pontuação zero para todos em jogos com W.O. ou cancelamento.

**Classificação, Desempates e Premiação**
- Ranking geral acumulado e rankings isolados para cada fase.
- Aplicação ordenada dos 6 critérios de desempate e critério de maior idade para top 4 geral.
- Divisão em partes iguais em caso de empate entre campeões de fase.
- Rateio percentual dos prêmios (50%, 25%, 12%, 5,5% no geral; 4%, 1,5%, 2% para fases).

## Out of scope -- the factory must never build this

**Operações Financeiras no App**
- Gateway de pagamento integrado, PIX automático ou carteira digital (o investimento de R$ 60 é pago diretamente via PIX ao organizador).
- Módulo de saque ou transferências bancárias dentro do sistema.

**Comunicação Interna**
- Sistema de chat interno, fórum de comentários ou mensagens privadas (o canal oficial obrigatório é o grupo de WhatsApp).

**Expansão Multi-Torneio**
- Suporte a outros campeonatos, criação de ligas privadas independentes ou múltiplos bolões simultâneos.

**Regras Alternativas de Futebol**
- Pontuação para resultado de disputas de pênaltis (a prorrogação encerra o placar oficial do bolão).
- Permitir edição de palpites após o prazo de bloqueio da fase.
- Permitir flexibilização da trava de 25% para os placares 2x1/1x2 nas fases limitadas.

**Plataformas Nativas**
- Aplicativos móveis nativos iOS ou Android (o sistema deve ser exclusivamente uma aplicação web responsiva).

## Hard invariants -- not tunable by any issue

1. **Bloqueio Irreversível de Fase.** Palpites enviados após o horário limite ou após o bloqueio manual do administrador são estritamente rejeitados pelo sistema.
2. **Pênaltis são ignorados.** O placar final considerado para o jogo é sempre o do apito final do tempo normal ou da prorrogação; cobranças de pênaltis não afetam placar nem vencedor no cálculo de pontos.
3. **Limite Rígido de 25% para 2x1/1x2.** O sistema rejeita qualquer submissão de palpites que exceda a cota calculada para a respectiva fase (máx 18, 4, 2 e 1).
4. **The factory cannot modify governance files.** `MISSION.md`, `FACTORY_RULES.md` and the conventions file are the constitution. A PR touching any of them is an automatic reject.
5. **The factory cannot modify its own judge.** `harness/`, `.factory/locks/` and `.factory/holdout/` define what "working" means here. Adding an assertion is always welcome; removing or loosening one is a human decision, always.

## Allowed evolutions

- Refinamentos na usabilidade da interface web, tabelas interativas e filtros de ranking.
- Otimizações de performance no cálculo de pontuações e renderização para centenas de acessos simultâneos.
- Telas de simulação para que o participante possa projetar cenários futuros de placares e impacto no ranking.

## Definition of done

Every change the factory ships clears all three gates.

**Gate 1 -- static checks and tests pass.** `python -m compileall -q .` e `python -m pytest -q`.

**Gate 2 -- integridade das regras de pontuação.** Todo novo recurso ou correção deve preservar os cálculos de pontuação exata (7, 8, 10), empates, prorrogação e desempates oficiais.

**Gate 3 -- the end-to-end path passes as a real user.**
1. Iniciar o servidor web da aplicação.
2. Registrar participante e submeter palpites da fase respeitando a cota de 25%.
3. Bloquear a fase e cadastrar placares reais de partidas com diferentes cenários.
4. Consultar o ranking geral e confirmar que os pontos, critérios de desempate e ordem estão estritamente corretos.

## Open questions -- decisions nobody has made yet

These are undecided, not forbidden. **The factory may propose an answer to any of them**, build against it, and record what it assumed -- the merge is then held for a human, so nothing ships on a guess and nothing stops for one.

- **Q1 (Autenticação simples):** O login deve ser por email/senha tradicional ou por código de acesso/token gerado pelo organizador?
- **Q2 (Desconto de custos de infraestrutura):** O abatimento de eventuais custos do Google Cloud sobre o bolo de premiação será parametrizável no painel de administração?

**Except these, which do stop the factory** -- they are on the irreversible list (`FACTORY_RULES.md` §7.3) rather than open in the ordinary sense:
- Alteração na tabela de pontuações de placares (7, 8, 10, 5, 4, 3, 2, 1, 0) e campeão (10).
- Alteração na ordem dos 6 critérios de desempate e desempate por idade no geral / rateio em fase.

## What the factory does NOT own -- permanently human

- Decisões legais e interpretações finais do regulamento (foro eleito da Confraria do Café do Deinf).
- Confirmação financeira e conferência dos comprovantes de pagamento via PIX dos participantes.
- Moderação e envio de avisos de prazos no grupo oficial de WhatsApp.
