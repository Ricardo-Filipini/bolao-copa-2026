import pytest

from app.core.scoring import calculate_match_score, classify_score
from app.models.schema import ScoreRarity


class TestClassifyScore:
    @pytest.mark.parametrize(
        "home,away",
        [
            (1, 0),
            (0, 1),
            (2, 0),
            (0, 2),
            (2, 1),
            (1, 2),
            (1, 1),
        ],
    )
    def test_ordinary_scores(self, home: int, away: int):
        assert classify_score(home, away) == ScoreRarity.ORDINARY

    @pytest.mark.parametrize(
        "home,away",
        [
            (3, 0),
            (0, 3),
            (3, 1),
            (1, 3),
            (3, 2),
            (2, 3),
            (0, 0),
            (2, 2),
        ],
    )
    def test_uncommon_scores(self, home: int, away: int):
        assert classify_score(home, away) == ScoreRarity.UNCOMMON

    @pytest.mark.parametrize(
        "home,away",
        [
            (4, 0),
            (0, 4),
            (4, 1),
            (1, 4),
            (4, 2),
            (2, 4),
            (4, 3),
            (3, 4),
            (3, 3),
            (4, 4),
            (5, 0),
            (0, 5),
            (5, 1),
            (5, 2),
            (6, 1),
            (7, 1),
        ],
    )
    def test_rare_scores(self, home: int, away: int):
        assert classify_score(home, away) == ScoreRarity.RARE


class TestCalculateMatchScore:
    # 1. Placares Exatos
    @pytest.mark.parametrize(
        "score",
        [(1, 0), (0, 1), (2, 0), (0, 2), (2, 1), (1, 2), (1, 1)],
    )
    def test_exact_ordinary_scores_award_7_points(self, score: tuple[int, int]):
        assert calculate_match_score(score[0], score[1], score[0], score[1]) == 7

    @pytest.mark.parametrize(
        "score",
        [(3, 0), (0, 3), (3, 1), (1, 3), (3, 2), (2, 3), (0, 0), (2, 2)],
    )
    def test_exact_uncommon_scores_award_8_points(self, score: tuple[int, int]):
        assert calculate_match_score(score[0], score[1], score[0], score[1]) == 8

    @pytest.mark.parametrize(
        "score",
        [(4, 0), (0, 4), (4, 1), (3, 3), (4, 3), (4, 4), (5, 0), (7, 1)],
    )
    def test_exact_rare_scores_award_10_points(self, score: tuple[int, int]):
        assert calculate_match_score(score[0], score[1], score[0], score[1]) == 10

    # 2. Acerto apenas do vencedor / resultado seco (3 pontos)
    def test_outcome_only_home_win(self):
        # Palpite 2x0, Real 3x1 -> Vencedor mandante (3 pts), sem acerto de gols
        assert calculate_match_score(2, 0, 3, 1) == 3

    def test_outcome_only_away_win(self):
        # Palpite 0x2, Real 1x3 -> Vencedor visitante (3 pts), sem acerto de gols
        assert calculate_match_score(0, 2, 1, 3) == 3

    def test_outcome_only_draw(self):
        # Palpite 1x1, Real 2x2 -> Empate (3 pts), sem acerto de gols
        assert calculate_match_score(1, 1, 2, 2) == 3

    # 3. Vencedor + Gols <= 2 (3 + 1 = 4 pontos)
    def test_winner_plus_home_goals_le_2(self):
        # Palpite 2x0, Real 2x1 -> Vencedor (3) + Mandante 2 gols (1) = 4 pts
        assert calculate_match_score(2, 0, 2, 1) == 4

    def test_winner_plus_away_goals_le_2(self):
        # Palpite 3x1, Real 4x1 -> Vencedor (3) + Visitante 1 gol (1) = 4 pts
        assert calculate_match_score(3, 1, 4, 1) == 4

    # 4. Vencedor + Gols >= 3 (3 + 2 = 5 pontos)
    def test_winner_plus_home_goals_ge_3(self):
        # Palpite 4x1, Real 4x2 -> Vencedor (3) + Mandante 4 gols (2) = 5 pts
        assert calculate_match_score(4, 1, 4, 2) == 5

    def test_winner_plus_away_goals_ge_3(self):
        # Palpite 1x3, Real 2x3 -> Vencedor (3) + Visitante 3 gols (2) = 5 pts
        assert calculate_match_score(1, 3, 2, 3) == 5

    # 5. Acerto isolado de gols sem acerto de vencedor (1 ou 2 pontos)
    def test_isolated_goals_le_2_awards_1_point(self):
        # Palpite 0x1, Real 3x1 -> Errou resultado (visitante vs mandante), acertou visitante 1 gol (1 pt)
        assert calculate_match_score(0, 1, 3, 1) == 1

        # Palpite 2x0, Real 2x3 -> Errou resultado, acertou mandante 2 gols (1 pt)
        assert calculate_match_score(2, 0, 2, 3) == 1

        # Palpite 1x1, Real 1x2 -> Errou resultado (empate vs visitante), acertou mandante 1 gol (1 pt)
        assert calculate_match_score(1, 1, 1, 2) == 1

    def test_isolated_goals_ge_3_awards_2_points(self):
        # Palpite 3x0, Real 3x4 -> Errou resultado, acertou mandante 3 gols (2 pts)
        assert calculate_match_score(3, 0, 3, 4) == 2

        # Palpite 1x4, Real 4x4 -> Errou resultado (visitante vs empate), acertou visitante 4 gols (2 pts)
        assert calculate_match_score(1, 4, 4, 4) == 2

    # 6. Erro Total (0 pontos)
    def test_complete_miss_awards_0_points(self):
        # Palpite 2x0, Real 0x1
        assert calculate_match_score(2, 0, 0, 1) == 0
        # Palpite 3x0, Real 1x2
        assert calculate_match_score(3, 0, 1, 2) == 0
        # Palpite 0x0, Real 2x1
        assert calculate_match_score(0, 0, 2, 1) == 0

    # 7. Regras Especiais: W.O. e cancelamentos
    def test_walkover_always_returns_zero(self):
        # Mesmo com palpite correspondente, W.O. anula pontos
        assert calculate_match_score(2, 1, 2, 1, is_walkover=True) == 0
        assert calculate_match_score(3, 0, 3, 0, is_walkover=True) == 0
        assert calculate_match_score(0, 0, 0, 0, is_walkover=True) == 0
        assert calculate_match_score(1, 0, 3, 0, is_walkover=True) == 0

    # 8. Prorrogação e Pênaltis
    def test_score_after_extra_time_considered_penalties_ignored(self):
        # Se após 120min o jogo terminou 1x1 e nos pênaltis deu 4x3:
        # O placar oficial apurado é 1x1.
        # Palpite 1x1 deve pontuar como exato ordinário (7 pts).
        assert calculate_match_score(1, 1, 1, 1) == 7

        # Palpite 2x2 no jogo que foi 1x1 (com decisão por pênaltis):
        # Acertou o empate não-exato -> 3 pts.
        assert calculate_match_score(2, 2, 1, 1) == 3
