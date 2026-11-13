
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# Reuse existing schemas
from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import (
    PatientCharacter,
    InitialEmotionalState,
)


# ==================================================
# 1. PATIENT RESPONSE
# ==================================================

class PatientResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    emotion: str
    tone: str


# ==================================================
# 2. AGENT 3 STRUCTURED OUTPUT
# ==================================================

class Agent3Output(BaseModel):
    """
    Complete output from Agent 3's single LLM call.
    """

    model_config = ConfigDict(extra="forbid")

    updated_emotional_state: InitialEmotionalState
    patient_response: str
    state_change_reason: str


# ==================================================
# 3. INDIVIDUAL INTERVIEW TURN
# ==================================================

class InterviewTurnRecord(BaseModel):
    """
    Stores everything that happened during one turn.
    """

    turn_number: int

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    trainee_transcript: str

    patient_response: str

    state_before: InitialEmotionalState

    state_after: InitialEmotionalState

    state_change_reason: str


# ==================================================
# 4. COMPLETE INTERVIEW SESSION
# ==================================================

class InterviewSessionRecord(BaseModel):
    """
    Stores the complete interview, including
    patient context, character and conversation history.
    """

    model_config = ConfigDict(extra="forbid")

    session_id: str

    patient_id: str
    character_id: str

    # Preserve the selected patient and character
    # for future evaluation by Agent 4.
    patient_profile: PatientProfile
    selected_character: PatientCharacter

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    ended_at: Optional[datetime] = None

    initial_state: InitialEmotionalState

    current_state: InitialEmotionalState

    turns: list[InterviewTurnRecord] = Field(
        default_factory=list
    )
