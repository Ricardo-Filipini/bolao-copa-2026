# Bolão Copa 2026 - Convenções do Código (AGENTS.md)

Este documento estabelece as convenções de desenvolvimento para os agentes da fábrica e desenvolvedores humanos no repositório `bolao-copa-2026`.

## Stack e Ferramentas
- **Linguagem:** Python 3.11+
- **Framework Web:** FastAPI com Uvicorn
- **Validação de Dados:** Pydantic v2
- **Testes:** Pytest (`python -m pytest -q`)
- **Verificação Estática:** `python -m compileall -q .`

## Estrutura do Projeto
- `app/core/`: Regras de negócio determinísticas e puras (cálculo de pontuação, limites de 25%, critérios de desempate).
- `app/models/`: Modelos de dados e schemas Pydantic (participantes, partidas, palpites, ranking).
- `app/api/`: Rotas HTTP e endpoints da API FastAPI.
- `app/storage/`: Camada de persistência (JSON / SQLite com integridade referencial).
- `tests/`: Testes unitários cobrindo todos os casos limítrofes do regulamento.

## Regras e Invariantes
1. **Puro e Determinístico:** Toda lógica de cálculo em `app/core/` deve ser desacoplada de I/O para testes unitários instantâneos.
2. **Sem pênaltis:** O placar do jogo é sempre apurado no tempo normal ou após prorrogação.
3. **Cota de 25%:** A trava para placares `2 x 1` e `1 x 2` nas 4 primeiras fases é inviolável.
4. **Respeito às Políticas da Fábrica:** PRs devem alterar no máximo 500 linhas de código de produção e passar em todos os gates.
