from app.models.schema import ScoreRarity

ORDINARY_SCORES: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 0),
        (0, 1),
        (2, 0),
        (0, 2),
        (2, 1),
        (1, 2),
        (1, 1),
    }
)

UNCOMMON_SCORES: frozenset[tuple[int, int]] = frozenset(
    {
        (3, 0),
        (0, 3),
        (3, 1),
        (1, 3),
        (3, 2),
        (2, 3),
        (0, 0),
        (2, 2),
    }
)


def classify_score(home: int, away: int) -> ScoreRarity:
    """Classifica um placar em Ordinário (7 pts), Incomum (8 pts) ou Raro (10 pts)."""
    score_tuple = (home, away)
    if score_tuple in ORDINARY_SCORES:
        return ScoreRarity.ORDINARY
    if score_tuple in UNCOMMON_SCORES:
        return ScoreRarity.UNCOMMON
    return ScoreRarity.RARE


def calculate_match_score(
    guess_home: int,
    guess_away: int,
    actual_home: int,
    actual_away: int,
    is_walkover: bool = False,
) -> int:
    """Calcula os pontos obtidos por um palpite em relação ao resultado oficial da partida.

    Regras:
    - Se a partida foi W.O. ou cancelada: 0 pontos.
    - Placar exato:
      - Raro: 10 pontos
      - Incomum: 8 pontos
      - Ordinário: 7 pontos
    - Placar não exato:
      - Acerto de resultado (vencedor ou empate não-exato): 3 pontos
      - Acerto de gols de uma equipe:
        - 1 ponto se a equipe marcou <= 2 gols e o palpite acertou o número exato
        - 2 pontos se a equipe marcou >= 3 gols e o palpite indicou faixa >= 3 gols
      - Pontuação máxima de placar não exato: 5 pontos (3 + 2).
    """
    if is_walkover:
        return 0

    # Placar Exato
    if guess_home == actual_home and guess_away == actual_away:
        rarity = classify_score(actual_home, actual_away)
        if rarity == ScoreRarity.RARE:
            return 10
        if rarity == ScoreRarity.UNCOMMON:
            return 8
        return 7

    # Placar Não Exato
    points = 0

    # 1. Acerto do vencedor ou empate não-exato
    guessed_home_win = guess_home > guess_away
    actual_home_win = actual_home > actual_away
    guessed_away_win = guess_home < guess_away
    actual_away_win = actual_home < actual_away
    guessed_draw = guess_home == guess_away
    actual_draw = actual_home == actual_away

    if (
        (guessed_home_win and actual_home_win)
        or (guessed_away_win and actual_away_win)
        or (guessed_draw and actual_draw)
    ):
        points += 3

    # 2. Acerto de gols:
    # - Faixa de 3 ou mais gols: se equipe marcou >= 3 e palpite foi >= 3 -> +2 pontos
    # - Acerto exato de gols (1 ou 2 gols): se equipe marcou > 0 e palpite == actual -> +1 ponto
    if actual_home >= 3 and guess_home >= 3:
        points += 2
    elif actual_home > 0 and guess_home == actual_home:
        points += 1

    if actual_away >= 3 and guess_away >= 3:
        points += 2
    elif actual_away > 0 and guess_away == actual_away:
        points += 1

    # Empate não-exato onde ambas as equipes marcaram <= 2 gols
    if (
        guessed_draw
        and actual_draw
        and points == 3
        and actual_home <= 2
        and guess_home <= 2
    ):
        points += 1

    return min(points, 5)
