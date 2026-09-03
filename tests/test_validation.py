import pytest

from app.core.validation import (
    QuotaExceededError,
    apply_default_omission_guesses,
    get_phase_quota_limit,
    validate_phase_quota_25,
)
from app.models.schema import Guess, Phase, Score


class TestPhaseQuotaLimits:
    def test_quota_limits_per_phase(self):
        assert get_phase_quota_limit(Phase.GROUP_STAGE) == 18
        assert get_phase_quota_limit(Phase.ROUND_OF_32) == 4
        assert get_phase_quota_limit(Phase.ROUND_OF_16) == 2
        assert get_phase_quota_limit(Phase.QUARTER_FINALS) == 1
        assert get_phase_quota_limit(Phase.SEMI_FINALS) is None
        assert get_phase_quota_limit(Phase.FINAL) is None

    def test_quota_limits_with_string_inputs(self):
        assert get_phase_quota_limit("grupos") == 18
        assert get_phase_quota_limit("round_of_32") == 4
        assert get_phase_quota_limit("oitavas") == 2
        assert get_phase_quota_limit("quartas") == 1
        assert get_phase_quota_limit("semis") is None
        assert get_phase_quota_limit("final") is None

    def test_custom_total_matches(self):
        assert get_phase_quota_limit(Phase.GROUP_STAGE, total_matches=72) == 18
        assert get_phase_quota_limit(Phase.GROUP_STAGE, total_matches=80) == 20


class TestValidatePhaseQuota25:
    def test_group_stage_exact_limit_passes(self):
        # 18 palpites 2x1/1x2 de 72 jogos permitidos
        guesses = [(2, 1)] * 9 + [(1, 2)] * 9 + [(1, 0)] * 54
        validate_phase_quota_25(guesses, Phase.GROUP_STAGE)

    def test_group_stage_exceeding_limit_raises_error(self):
        # 19 palpites 2x1/1x2
        guesses = [(2, 1)] * 10 + [(1, 2)] * 9 + [(1, 0)] * 53
        with pytest.raises(QuotaExceededError, match="Limite de cota de 25% excedido"):
            validate_phase_quota_25(guesses, Phase.GROUP_STAGE)

    def test_round_of_32_quota(self):
        # Limite = 4
        guesses_ok = [(2, 1)] * 2 + [(1, 2)] * 2 + [(0, 0)] * 12
        validate_phase_quota_25(guesses_ok, Phase.ROUND_OF_32)

        guesses_bad = [(2, 1)] * 3 + [(1, 2)] * 2 + [(0, 0)] * 11
        with pytest.raises(QuotaExceededError):
            validate_phase_quota_25(guesses_bad, Phase.ROUND_OF_32)

    def test_round_of_16_quota(self):
        # Limite = 2
        guesses_ok = [(2, 1), (1, 2)] + [(3, 0)] * 6
        validate_phase_quota_25(guesses_ok, Phase.ROUND_OF_16)

        guesses_bad = [(2, 1), (1, 2), (2, 1)] + [(3, 0)] * 5
        with pytest.raises(QuotaExceededError):
            validate_phase_quota_25(guesses_bad, Phase.ROUND_OF_16)

    def test_quarter_finals_quota(self):
        # Limite = 1
        guesses_ok = [(2, 1)] + [(1, 0)] * 3
        validate_phase_quota_25(guesses_ok, Phase.QUARTER_FINALS)

        guesses_bad = [(2, 1), (1, 2)] + [(1, 0)] * 2
        with pytest.raises(QuotaExceededError):
            validate_phase_quota_25(guesses_bad, Phase.QUARTER_FINALS)

    def test_semis_and_final_unrestricted(self):
        # Semis (2 jogos) podem ter 2x1 nos dois jogos
        guesses_semis = [(2, 1), (1, 2)]
        validate_phase_quota_25(guesses_semis, Phase.SEMI_FINALS)

        # Final (1 jogo) pode ter 2x1
        guesses_final = [(2, 1)]
        validate_phase_quota_25(guesses_final, Phase.FINAL)

    def test_supports_score_and_guess_objects(self):
        guesses = [
            Score(home=2, away=1),
            Guess(participant_id="user1", match_id="m1", score=Score(home=1, away=2)),
            Score(home=3, away=0),
        ]
        # Para quartas de final, temos 2 placares 2x1/1x2 (limite 1) -> deve falhar
        with pytest.raises(QuotaExceededError):
            validate_phase_quota_25(guesses, Phase.QUARTER_FINALS)


class TestApplyDefaultOmissionGuesses:
    def test_fills_missing_matches_with_0x0(self):
        all_matches = ["m1", "m2", "m3", "m4"]
        existing = {
            "m1": Score(home=2, away=1),
            "m3": Score(home=1, away=0),
        }
        filled = apply_default_omission_guesses(all_matches, existing)

        assert len(filled) == 4
        assert filled["m1"] == Score(home=2, away=1)
        assert filled["m2"] == Score(home=0, away=0)
        assert filled["m3"] == Score(home=1, away=0)
        assert filled["m4"] == Score(home=0, away=0)

    def test_all_matches_already_present(self):
        all_matches = ["m1", "m2"]
        existing = {
            "m1": Score(home=3, away=0),
            "m2": Score(home=0, away=1),
        }
        filled = apply_default_omission_guesses(all_matches, existing)
        assert filled == existing

    def test_empty_existing_guesses(self):
        all_matches = ["m1", "m2", "m3"]
        filled = apply_default_omission_guesses(all_matches, {})
        assert len(filled) == 3
        for m in all_matches:
            assert filled[m] == Score(home=0, away=0)
