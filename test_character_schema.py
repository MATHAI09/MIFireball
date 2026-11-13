
from mi.character_creation.schemas import (
    PatientCharacter,
    CharacterCollection,
    InitialEmotionalState
)


state = InitialEmotionalState(
    frustration=7,
    anxiety=5,
    trust=2,
    motivation=3,
    confidence=3,
    willingness_to_discuss=3,
    willingness_to_change=3
)


character = PatientCharacter(
    character_id="CHAR_001",
    character_name="Defensive Arun",
    character_type="Defensive",
    description="An independent and initially resistant patient.",

    personality_traits=[
        "Independent",
        "Strong-willed"
    ],

    initial_emotional_state=state,

    initial_state_explanation=(
        "Initially reluctant to discuss smoking."
    )
)


collection = CharacterCollection(
    patient_id="PAT_001",
    patient_name="Arun Kumar",
    characters=[character]
)


print(collection.model_dump_json(indent=4))
