
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import PatientCharacter

from mi.patient_interview.schemas import (
    InitialEmotionalState,
    InterviewTurnRecord,
    InterviewSessionRecord,
    Agent3Output,
)


class InterviewStateManager:

    def __init__(
        self,
        patient: PatientProfile,
        character: PatientCharacter,
        patient_id: str,
        storage_dir: str = "data/interview_sessions",
    ):
        self.patient = patient
        self.character = character
        self.patient_id = patient_id

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = str(uuid4())

        initial_state = InitialEmotionalState.model_validate(
            character.initial_emotional_state.model_dump()
        )

        self.session = InterviewSessionRecord(
            session_id=self.session_id,
            patient_id=self.patient_id,  # Changed
            character_id=character.character_id,
            patient_profile=patient,
            selected_character=character,
            initial_state=initial_state,
            current_state=initial_state,
        )

        self._save_session()

    # ----------------------------------------------
    # Get current emotional state
    # ----------------------------------------------

    @property
    def current_state(self) -> InitialEmotionalState:
        return self.session.current_state

    # ----------------------------------------------
    # Record a completed interview turn
    # ----------------------------------------------

    def record_turn(
        self,
        trainee_transcript: str,
        agent_output: Agent3Output,
    ) -> InterviewTurnRecord:
        print("\n===== RECORDING INTERVIEW TURN =====")
        print("Trainee:", trainee_transcript)
        print("Patient:", agent_output.patient_response)
        state_before = self.current_state.model_copy(deep=True)

        state_after = agent_output.updated_emotional_state

        turn_number = len(self.session.turns) + 1

        turn = InterviewTurnRecord(
            turn_number=turn_number,
            trainee_transcript=trainee_transcript,
            patient_response=agent_output.patient_response,
            state_before=state_before,
            state_after=state_after,
            state_change_reason=agent_output.state_change_reason,
        )

        # Update session state
        self.session.current_state = state_after

        # Append turn to history
        self.session.turns.append(turn)

        # Persist changes
        self._save_session()

        return turn

    # ----------------------------------------------
    # Save complete session to JSON
    # ----------------------------------------------

    def _save_session(self):

        file_path = self.storage_dir / f"{self.session_id}.json"

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(
                self.session.model_dump(mode="json"),
                file,
                indent=4,
                ensure_ascii=False,
            )

    # ----------------------------------------------
    # End interview
    # ----------------------------------------------

    def end_session(self):

        self.session.ended_at = datetime.now(timezone.utc)

        self._save_session()

        return self.session
