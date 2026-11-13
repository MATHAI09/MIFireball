
import json
from pathlib import Path

from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import CharacterCollection

from mi.patient_interview.schemas import (
    Agent3Output,
    PatientResponse,
    InitialEmotionalState,
)

from mi.patient_interview.state_manager import InterviewStateManager


# ----------------------------------------------
# 1. Load existing JSON files
# ----------------------------------------------

with open("data/patient_profile.json", encoding="utf-8") as f:
    patient = PatientProfile.model_validate(json.load(f))

with open("data/character_profiles.json", encoding="utf-8") as f:
    collection = CharacterCollection.model_validate(json.load(f))


# ----------------------------------------------
# 2. Select one character
# ----------------------------------------------

character = next(
    c for c in collection.characters
    if c.character_id == "arthur_01_defensive"
)


# ----------------------------------------------
# 3. Initialize interview session
# ----------------------------------------------

manager = InterviewStateManager(
    patient=patient,
    character=character,
    patient_id=collection.patient_id,  # Added
)

print("Session created:", manager.session_id)
print("Initial state:", manager.current_state.model_dump())


# ----------------------------------------------
# 4. Simulate Agent 3 output
# ----------------------------------------------

agent_output = Agent3Output(
    state_update=InitialEmotionalState(
        frustration=5,
        anxiety=3,
        trust=4,
        motivation=2,
        confidence=2,
        willingness_to_discuss=5,
        willingness_to_change=2,
    ),
    patient_response=PatientResponse(
        text="Well, I suppose you can explain what you mean.",
        emotion="cautious",
        tone="guarded",
    ),
    state_change_reason="The trainee demonstrated empathy, "
                        "making Arthur slightly more willing to talk.",
)


# ----------------------------------------------
# 5. Record the turn
# ----------------------------------------------

manager.record_turn(
    trainee_transcript="I understand this is difficult for you.",
    agent_output=agent_output,
)

print("\nUpdated state:")
print(manager.current_state.model_dump())


# ----------------------------------------------
# 6. End session
# ----------------------------------------------

session = manager.end_session()

print("\nSession ended:", session.session_id)
print("Total turns:", len(session.turns))


# ----------------------------------------------
# 7. Verify saved JSON
# ----------------------------------------------

file_path = Path("data/interview_sessions") / f"{manager.session_id}.json"

with open(file_path, encoding="utf-8") as f:
    saved_data = json.load(f)

print("\nSaved JSON successfully!")
print("Recorded turns:", len(saved_data["turns"]))
print("Current trust:", saved_data["current_state"]["trust"])
