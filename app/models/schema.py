from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class ScoreRarity(str, Enum):
    ORDINARY = "ordinario"
    UNCOMMON = "incomum"
    RARE = "raro"


class Phase(str, Enum):
    GROUP_STAGE = "grupos"
    ROUND_OF_32 = "round_of_32"
    ROUND_OF_16 = "oitavas"
    QUARTER_FINALS = "quartas"
    SEMI_FINALS = "semis"
    FINAL = "final"


class Score(BaseModel):
    model_config = ConfigDict(frozen=True)

    home: int = Field(..., ge=0, description="Gols da equipe mandante")
    away: int = Field(..., ge=0, description="Gols da equipe visitante")


class Participant(BaseModel):
    id: str = Field(..., min_length=1, description="Identificador único")
    name: str = Field(..., min_length=1, description="Nome completo")
    birth_date: str | None = Field(default=None, description="Data de nascimento")
    champion: str | None = Field(default=None, description="Palpite de campeão")


class Guess(BaseModel):
    id: str | None = Field(default=None, description="Identificador do palpite")
    participant_id: str = Field(..., min_length=1, description="Identificador do participante")
    match_id: str = Field(..., min_length=1, description="Identificador da partida")
    score: Score = Field(..., description="Placar palpitado")


class Match(BaseModel):
    id: str = Field(..., min_length=1, description="Identificador da partida")
    phase: Phase = Field(..., description="Fase da Copa")
    team_home: str = Field(..., min_length=1, description="Equipe mandante")
    team_away: str = Field(..., min_length=1, description="Equipe visitante")
    official_score: Score | None = Field(default=None, description="Placar oficial final")
    is_walkover: bool = Field(default=False, description="Indica se a partida foi W.O. ou cancelada")
