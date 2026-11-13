
import json

from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import CharacterCollection

from mi.patient_interview.prompts import (
    build_agent_instructions,
    build_emotion_context,
)


# Load patient background
with open("data/patient_profile.json", encoding="utf-8") as f:
    patient = PatientProfile.model_validate(json.load(f))


# Load character collection
with open("data/character_profiles.json", encoding="utf-8") as f:
    collection = CharacterCollection.model_validate(json.load(f))


# Select Defensive Arthur
character = next(
    c for c in collection.characters
    if c.character_id == "arthur_01_defensive"
)


# Build static instructions
instructions = build_agent_instructions(
    patient=patient,
    character=character,
)


# Build initial emotion context
emotion_context = build_emotion_context(
    current_state=character.initial_emotional_state,
)


print("========== AGENT INSTRUCTIONS ==========")
print(instructions)

print("\n========== EMOTION CONTEXT ==========")
print(emotion_context)
