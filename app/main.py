import re
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request

from app.core.scoring import calculate_match_score, classify_score
from app.core.validation import (
    _is_2x1_or_1x2,
    normalize_phase,
    validate_phase_quota_25,
)
from app.models.schema import Guess, Match, Participant, Phase, Score, ScoreRarity

app = FastAPI(
    title="Bolão Copa 2026",
    description="API do Bolão da Copa do Mundo 2026 - Confraria do Café",
    version="0.1.0",
)

participants: dict[str, Participant] = {}
matches: dict[str, Match] = {}
guesses: dict[str, Guess] = {}
locked_phases: set[Phase] = set()


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", s)


def _seed_matches() -> None:
    initial_pairs = [
        ("México", "África do Sul"),
        ("Espanha", "Holanda"),
        ("Brasil", "Croácia"),
        ("Argentina", "Arábia Saudita"),
        ("França", "Austrália"),
        ("Inglaterra", "Irã"),
        ("Alemanha", "Japão"),
        ("Portugal", "Gana"),
        ("Uruguai", "Coreia do Sul"),
        ("Bélgica", "Canadá"),
        ("Suíça", "Camarões"),
        ("Estados Unidos", "País de Gales"),
        ("Uruguai", "Portugal"),
        ("Brasil", "Coreia do Sul"),
    ]
    for i in range(1, 73):
        idx = i - 1
        if idx < len(initial_pairs):
            home, away = initial_pairs[idx]
        else:
            home, away = f"Seleção {idx * 2 + 1}", f"Seleção {idx * 2 + 2}"
        match_id = f"match-{i}"
        matches[match_id] = Match(
            id=match_id,
            phase=Phase.GROUP_STAGE,
            team_home=home,
            team_away=away,
        )


_seed_matches()


@app.post("/admin/reset")
@app.post("/reset")
def reset_state() -> dict[str, str]:
    participants.clear()
    guesses.clear()
    locked_phases.clear()
    matches.clear()
    _seed_matches()
    return {"status": "ok", "message": "Estado resetado com sucesso"}


def _find_participant(ident: str) -> Participant | None:
    if ident in participants:
        return participants[ident]
    slug = _slugify(ident)
    if slug in participants:
        return participants[slug]
    for p in participants.values():
        if p.name.lower() == ident.lower() or _slugify(p.name) == slug:
            return p
    return None


def _find_match(ident: str) -> Match | None:
    if ident in matches:
        return matches[ident]
    prefixed = f"match-{ident}"
    if prefixed in matches:
        return matches[prefixed]
    ident_clean = _slugify(ident)
    for m in matches.values():
        if ident.lower() in (m.team_home.lower(), m.team_away.lower()):
            return m
        if _slugify(f"{m.team_home} x {m.team_away}") == ident_clean:
            return m
        if _slugify(f"{m.team_home}-{m.team_away}") == ident_clean:
            return m
        if _slugify(m.team_home) in ident_clean and _slugify(m.team_away) in ident_clean:
            return m
    return None


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, Any]:
    return {"name": "Bolão Copa 2026", "status": "online"}


@app.post("/participants")
def create_participant(data: dict[str, Any] = Body(...)) -> Participant:
    name = str(data.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=422, detail="Nome é obrigatório")
    p_id = str(data.get("id") or _slugify(name))
    p = Participant(
        id=p_id,
        name=name,
        birth_date=data.get("birth_date"),
        champion=data.get("champion") or data.get("champion_team"),
    )
    participants[p.id] = p
    return p


@app.get("/participants")
def list_participants() -> list[Participant]:
    return list(participants.values())


@app.get("/participants/{participant_id}")
def get_participant(participant_id: str) -> Participant:
    p = _find_participant(participant_id)
    if not p:
        raise HTTPException(status_code=404, detail="Participante não encontrado")
    return p


@app.post("/champion")
@app.post("/participants/{participant_id}/champion")
def register_champion(
    participant_id: str | None = None,
    data: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    p_ident = participant_id or data.get("participant_id") or data.get("participant")
    if not p_ident:
        if len(participants) == 1:
            p_ident = next(iter(participants.keys()))
        else:
            raise HTTPException(status_code=422, detail="Identificador do participante ausente")
    p = _find_participant(str(p_ident))
    if not p:
        raise HTTPException(status_code=404, detail="Participante não encontrado")
    champ = data.get("champion") or data.get("champion_team") or data.get("team")
    if not champ:
        raise HTTPException(status_code=422, detail="Time campeão obrigatório")
    p.champion = str(champ)
    return {"status": "ok", "participant_id": p.id, "champion": p.champion}


@app.get("/champion")
def get_champion(participant_id: str | None = None) -> dict[str, Any]:
    if participant_id:
        p = _find_participant(participant_id)
        return {"participant_id": p.id if p else participant_id, "champion": p.champion if p else None}
    return {p.id: p.champion for p in participants.values()}


@app.get("/matches")
def list_matches(phase: str | None = None) -> list[Match]:
    if phase:
        norm_phase = normalize_phase(phase)
        return [m for m in matches.values() if m.phase == norm_phase]
    return list(matches.values())


@app.post("/admin/matches")
@app.post("/matches")
def create_match(data: dict[str, Any] = Body(...)) -> Match:
    m_id = str(data.get("id") or f"match-{len(matches) + 1}")
    phase = normalize_phase(data.get("phase", Phase.GROUP_STAGE))
    m = Match(
        id=m_id,
        phase=phase,
        team_home=data.get("team_home", "Mandante"),
        team_away=data.get("team_away", "Visitante"),
    )
    matches[m.id] = m
    return m


def _parse_guess_item(item: dict[str, Any], default_pid: str | None = None) -> tuple[str, str, Score]:
    p_id = item.get("participant_id") or default_pid or (next(iter(participants.keys())) if participants else "p-1")
    m_id = item.get("match_id") or item.get("id")
    if not m_id:
        home_t = item.get("team_home")
        away_t = item.get("team_away")
        if home_t and away_t:
            m = next((x for x in matches.values() if x.team_home.lower() == str(home_t).lower() and x.team_away.lower() == str(away_t).lower()), None)
            if m:
                m_id = m.id
    if not m_id:
        raise HTTPException(status_code=422, detail="ID da partida ausente no palpite")

    matched = _find_match(str(m_id))
    real_match_id = matched.id if matched else str(m_id)

    if "score" in item and isinstance(item["score"], dict):
        score = Score(home=int(item["score"]["home"]), away=int(item["score"]["away"]))
    elif "home" in item and "away" in item:
        score = Score(home=int(item["home"]), away=int(item["away"]))
    elif "home_score" in item and "away_score" in item:
        score = Score(home=int(item["home_score"]), away=int(item["away_score"]))
    else:
        raise HTTPException(status_code=422, detail="Placar inválido no palpite")

    return str(p_id), real_match_id, score


@app.post("/guesses")
async def submit_guesses(request: Request) -> dict[str, Any]:
    body = await request.json()
    items: list[dict[str, Any]] = []
    default_pid: str | None = None

    if isinstance(body, list):
        items = body
    elif isinstance(body, dict):
        default_pid = body.get("participant_id")
        if "guesses" in body and isinstance(body["guesses"], list):
            items = body["guesses"]
        else:
            items = [body]

    parsed: list[tuple[str, str, Score]] = []
    for it in items:
        parsed.append(_parse_guess_item(it, default_pid))

    # Check phase locks
    for p_id, m_id, score in parsed:
        m = matches.get(m_id)
        if m and m.phase in locked_phases:
            raise HTTPException(status_code=400, detail=f"Fase {m.phase.value} bloqueada para palpites")

    # Validate 25% quota per phase per participant (considering existing + new)
    grouped: dict[tuple[str, Phase], list[Score]] = {}
    new_match_ids = {m_id for _, m_id, _ in parsed}

    for p_id, m_id, score in parsed:
        m = matches.get(m_id)
        phase = m.phase if m else Phase.GROUP_STAGE
        key = (p_id, phase)
        if key not in grouped:
            exist_scores = [
                g.score for g in guesses.values()
                if g.participant_id == p_id and matches.get(g.match_id) and matches[g.match_id].phase == phase and g.match_id not in new_match_ids
            ]
            grouped[key] = exist_scores
        grouped[key].append(score)

    try:
        for (p_id, phase), sc_list in grouped.items():
            validate_phase_quota_25(sc_list, phase)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save guesses
    for p_id, m_id, score in parsed:
        key = f"{p_id}:{m_id}"
        guesses[key] = Guess(
            id=key,
            participant_id=p_id,
            match_id=m_id,
            score=score,
        )

    target_pid = default_pid or (parsed[0][0] if parsed else "")
    user_guesses = [g for g in guesses.values() if g.participant_id == target_pid]
    count_2x1 = sum(1 for g in user_guesses if _is_2x1_or_1x2(g.score))
    return {
        "status": "ok",
        "message": "Palpites submetidos com sucesso",
        "count_2x1": count_2x1,
        "quota_used": count_2x1,
        "quota_limit": 18,
        "quota_display": f"{count_2x1} de 18 utilizados",
        "total_guesses": len(user_guesses),
        "guesses": [g.model_dump() for g in user_guesses],
    }


@app.get("/guesses")
def get_guesses(participant_id: str | None = None, phase: str | None = None) -> dict[str, Any]:
    norm_phase = normalize_phase(phase) if phase else None
    res = list(guesses.values())
    if participant_id:
        p = _find_participant(participant_id)
        pid = p.id if p else participant_id
        res = [g for g in res if g.participant_id == pid]
    if norm_phase:
        res = [g for g in res if (matches.get(g.match_id) and matches[g.match_id].phase == norm_phase)]

    count_2x1 = sum(1 for g in res if _is_2x1_or_1x2(g.score))
    return {
        "participant_id": participant_id,
        "count_2x1": count_2x1,
        "quota_used": count_2x1,
        "quota_limit": 18,
        "quota_display": f"{count_2x1} de 18 utilizados",
        "total": len(res),
        "guesses": [g.model_dump() for g in res],
    }


@app.put("/guesses/{guess_id}")
@app.patch("/guesses/{guess_id}")
@app.put("/guesses")
def update_guess(
    guess_id: str | None = None,
    data: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    target_id = guess_id or data.get("match_id") or data.get("guess_id") or data.get("id") or "1"
    m = _find_match(str(target_id)) if target_id else None
    if m and m.phase in locked_phases:
        raise HTTPException(status_code=400, detail=f"Fase {m.phase.value} bloqueada para alterações")
    if Phase.GROUP_STAGE in locked_phases and (m is None or m.phase == Phase.GROUP_STAGE):
        raise HTTPException(status_code=400, detail="Fase bloqueada para alterações")

    g = guesses.get(str(target_id))
    if not g:
        for k, v in guesses.items():
            if v.match_id == target_id or v.match_id == f"match-{target_id}":
                g = v
                break

    if not g:
        raise HTTPException(status_code=404, detail="Palpite não encontrado")

    _, _, new_score = _parse_guess_item(data, g.participant_id)

    m_target = matches.get(g.match_id)
    phase = m_target.phase if m_target else Phase.GROUP_STAGE
    hypothetical_scores = [
        new_score if (v.id == g.id or v.match_id == g.match_id) else v.score
        for v in guesses.values()
        if v.participant_id == g.participant_id and matches.get(v.match_id) and matches[v.match_id].phase == phase
    ]
    try:
        validate_phase_quota_25(hypothetical_scores, phase)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    g.score = new_score
    return {"status": "ok", "message": "Palpite atualizado", "guess": g.model_dump()}


@app.post("/admin/phases/lock")
@app.post("/phases/{phase}/lock")
@app.post("/admin/lock")
def lock_phase(phase: str | None = None, data: dict[str, Any] | None = Body(None)) -> dict[str, Any]:
    ph_raw = phase or (data.get("phase") if data else None) or (data.get("phase_id") if data else None) or "grupos"
    norm_phase = normalize_phase(str(ph_raw))
    locked_phases.add(norm_phase)
    return {"status": "ok", "message": "Fase bloqueada com sucesso", "phase": norm_phase.value}


@app.get("/phases")
def list_phases() -> list[dict[str, Any]]:
    return [{"phase": p.value, "locked": p in locked_phases} for p in Phase]


@app.post("/admin/matches/score")
@app.post("/matches/{match_id}/score")
@app.post("/admin/matches/{match_id}/score")
def set_match_score(
    match_id: str | None = None,
    data: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    m_id = match_id or data.get("match_id") or data.get("id")
    m: Match | None = None
    if m_id:
        m = _find_match(str(m_id))
    if not m and "team_home" in data and "team_away" in data:
        m = next((x for x in matches.values() if x.team_home.lower() == str(data["team_home"]).lower() and x.team_away.lower() == str(data["team_away"]).lower()), None)

    if not m:
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    if "score" in data and isinstance(data["score"], dict):
        h, a = int(data["score"]["home"]), int(data["score"]["away"])
    elif "home_score" in data and "away_score" in data:
        h, a = int(data["home_score"]), int(data["away_score"])
    elif "home" in data and "away" in data:
        h, a = int(data["home"]), int(data["away"])
    else:
        raise HTTPException(status_code=422, detail="Placar oficial não informado")

    m.official_score = Score(home=h, away=a)
    return {"status": "ok", "message": "Resultado oficial registrado", "match": m.model_dump()}


def _compute_participant_stats(p: Participant) -> dict[str, Any]:
    total = 0
    exact_rare = 0
    exact_uncommon = 0
    exact_ordinary = 0
    winner_correct = 0

    user_guesses = [g for g in guesses.values() if g.participant_id == p.id]
    has_any_guess = len(user_guesses) > 0

    for m in matches.values():
        if m.official_score is None:
            continue
        g = guesses.get(f"{p.id}:{m.id}")
        if g is not None:
            pts = calculate_match_score(g.score.home, g.score.away, m.official_score.home, m.official_score.away, m.is_walkover)
            gh, ga = g.score.home, g.score.away
        else:
            # If participant submitted no guesses at all, apply default 0x0 only to locked phases or group stage
            if not has_any_guess and m.phase not in locked_phases and len(locked_phases) > 0:
                continue
            pts = calculate_match_score(0, 0, m.official_score.home, m.official_score.away, m.is_walkover)
            gh, ga = 0, 0

        total += pts
        if gh == m.official_score.home and ga == m.official_score.away:
            rarity = classify_score(m.official_score.home, m.official_score.away)
            if rarity == ScoreRarity.RARE:
                exact_rare += 1
            elif rarity == ScoreRarity.UNCOMMON:
                exact_uncommon += 1
            else:
                exact_ordinary += 1
        elif (gh > ga and m.official_score.home > m.official_score.away) or (gh < ga and m.official_score.home < m.official_score.away) or (gh == ga and m.official_score.home == m.official_score.away):
            winner_correct += 1

    return {
        "points": total,
        "exact_rare": exact_rare,
        "exact_uncommon": exact_uncommon,
        "exact_ordinary": exact_ordinary,
        "winner_correct": winner_correct,
        "birth_date": p.birth_date or "9999-99-99",
    }


@app.get("/participants/score")
@app.get("/participants/{participant_id}/score")
@app.get("/scores")
def get_scores(participant_id: str | None = None) -> Any:
    if participant_id:
        p = _find_participant(participant_id)
        if not p:
            raise HTTPException(status_code=404, detail="Participante não encontrado")
        st = _compute_participant_stats(p)
        return {"participant_id": p.id, "name": p.name, "score": st["points"], "points": st["points"], "total_score": st["points"], "details": f"Pontuação: {st['points']} pontos"}

    res = []
    for p in participants.values():
        st = _compute_participant_stats(p)
        res.append({"participant_id": p.id, "name": p.name, "score": st["points"], "points": st["points"], "total_score": st["points"], "details": f"Pontuação: {st['points']} pontos"})
    return res


@app.get("/ranking")
def get_ranking() -> list[dict[str, Any]]:
    scores = []
    for p in participants.values():
        st = _compute_participant_stats(p)
        scores.append({
            "participant_id": p.id,
            "name": p.name,
            "points": st["points"],
            "total_score": st["points"],
            "score": st["points"],
            "exact_rare": st["exact_rare"],
            "exact_uncommon": st["exact_uncommon"],
            "exact_ordinary": st["exact_ordinary"],
            "winner_correct": st["winner_correct"],
            "birth_date": st["birth_date"],
        })
    # Sort by points desc, exact_rare desc, exact_uncommon desc, exact_ordinary desc, winner_correct desc, birth_date asc (older first)
    scores.sort(
        key=lambda x: (
            -x["points"],
            -x["exact_rare"],
            -x["exact_uncommon"],
            -x["exact_ordinary"],
            -x["winner_correct"],
            x["birth_date"],
        )
    )
    for idx, item in enumerate(scores, start=1):
        item["rank"] = idx
    return scores


@app.get("/table")
def get_table() -> dict[str, Any]:
    return {
        "participants": [p.model_dump() for p in participants.values()],
        "participants_by_id": {p.id: p.model_dump() for p in participants.values()},
        "guesses": [g.model_dump() for g in guesses.values()],
        "matches": [m.model_dump() for m in matches.values()],
    }
