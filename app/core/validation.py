from typing import Sequence

from app.models.schema import Guess, Phase, Score

QUOTA_LIMITED_PHASES: dict[Phase, int] = {
    Phase.GROUP_STAGE: 18,  # 72 partidas * 0.25
    Phase.ROUND_OF_32: 4,  # 16 partidas * 0.25
    Phase.ROUND_OF_16: 2,  # 8 partidas * 0.25
    Phase.QUARTER_FINALS: 1,  # 4 partidas * 0.25
}


class QuotaExceededError(ValueError):
    """Exceção levantada quando um participante excede a cota de 25% de palpites 2x1 / 1x2."""

    pass


def _normalize_phase(phase: Phase | str) -> Phase:
    if isinstance(phase, Phase):
        return phase
    try:
        return Phase(phase)
    except ValueError:
        # Tenta casar por nome de atributo caso passe 'GROUP_STAGE' etc.
        try:
            return Phase[phase.upper()]
        except KeyError:
            raise ValueError(f"Fase inválida: {phase}")


def get_phase_quota_limit(phase: Phase | str, total_matches: int | None = None) -> int | None:
    """Retorna o número máximo permitido de palpites 2x1 e 1x2 para uma fase.

    Retorna None se a fase não tiver restrição de cota (ex: semis, final).
    """
    normalized_phase = _normalize_phase(phase)
    if normalized_phase not in QUOTA_LIMITED_PHASES:
        return None

    if total_matches is not None:
        return int(total_matches * 0.25)

    return QUOTA_LIMITED_PHASES[normalized_phase]


def _is_2x1_or_1x2(score: Score | tuple[int, int] | Guess) -> bool:
    if isinstance(score, Guess):
        h, a = score.score.home, score.score.away
    elif isinstance(score, Score):
        h, a = score.home, score.away
    elif isinstance(score, tuple) and len(score) == 2:
        h, a = score[0], score[1]
    else:
        raise ValueError(f"Formato de palpite não suportado: {score}")
    return (h, a) in ((2, 1), (1, 2))


def validate_phase_quota_25(
    guesses: Sequence[Score | tuple[int, int] | Guess],
    phase: Phase | str,
    total_matches: int | None = None,
) -> None:
    """Valida se a lista de palpites de uma fase respeita a cota máxima de 25% para 2x1 e 1x2.

    Levanta QuotaExceededError se a cota for excedida.
    """
    limit = get_phase_quota_limit(phase, total_matches=total_matches)
    if limit is None:
        return

    count_2x1 = sum(1 for g in guesses if _is_2x1_or_1x2(g))
    if count_2x1 > limit:
        raise QuotaExceededError(
            f"Limite de cota de 25% excedido: {count_2x1} palpites 2x1/1x2 (máximo permitido: {limit})"
        )


def apply_default_omission_guesses(
    all_match_ids: Sequence[str],
    existing_guesses: dict[str, Score],
) -> dict[str, Score]:
    """Preenche partidas sem palpites com o palpite de omissão padrão (0 x 0)."""
    result: dict[str, Score] = dict(existing_guesses)
    for match_id in all_match_ids:
        if match_id not in result:
            result[match_id] = Score(home=0, away=0)
    return result
