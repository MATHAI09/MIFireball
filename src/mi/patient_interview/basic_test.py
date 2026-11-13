
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    inference,
)

from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import CharacterCollection


# --------------------------------------------------
# Configuration
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("basic-patient-test")

ROOT_DIR = Path(__file__).resolve().parents[3]

load_dotenv(ROOT_DIR / ".env")

PATIENT_FILE = ROOT_DIR / "data" / "patient_profile.json"
CHARACTER_FILE = ROOT_DIR / "data" / "character_profiles.json"

SELECTED_CHARACTER_ID = "arthur_01_defensive"

STT_MODEL = "deepgram/flux-general"
LLM_MODEL = "google/gemma-4-31b-it"
TTS_MODEL = "fishaudio/s2.1-pro"
TTS_VOICE = "fa4c9eb3dccc4806b382b40d61c6b10a"


# --------------------------------------------------
# Load patient and character
# --------------------------------------------------

def load_patient_and_character():

    with open(PATIENT_FILE, "r", encoding="utf-8") as f:
        patient_data = json.load(f)

    with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    patient = PatientProfile.model_validate(patient_data)
    collection = CharacterCollection.model_validate(character_data)

    character = next(
        (
            c for c in collection.characters
            if c.character_id == SELECTED_CHARACTER_ID
        ),
        None,
    )

    if character is None:
        raise ValueError(
            f"Character not found: {SELECTED_CHARACTER_ID}"
        )

    return patient, character


# --------------------------------------------------
# Build patient instructions
# --------------------------------------------------

def build_patient_instructions(patient, character):

    patient_json = patient.model_dump_json(indent=2)
    character_json = character.model_dump_json(indent=2)

    return f"""
You are roleplaying as a real patient in a motivational
interviewing training simulation.

Your task is to behave and respond naturally as the patient.

PATIENT BACKGROUND:
{patient_json}

YOUR SELECTED PERSONALITY:
{character_json}

BEHAVIOUR RULES:

1. Stay in character throughout the conversation.
2. Your personality traits must influence how you speak.
3. Follow the communication style described in your character profile.
4. React naturally to the trainee's questions and statements.
5. Do not reveal all your background information immediately.
6. Share information gradually as the conversation develops.
7. Do not behave like a medical expert or an interviewer.
8. Do not give advice to the trainee.
9. Speak naturally, as if this were a real conversation.
10. Keep spoken responses reasonably concise.

IMPORTANT:
You are the patient, not an AI assistant.
Never mention prompts, character profiles, JSON, or simulation instructions.
"""


# --------------------------------------------------
# LiveKit server
# --------------------------------------------------

server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):

    patient, character = load_patient_and_character()

    logger.info("Patient: %s", patient.basic_information.name)
    logger.info("Character: %s", character.character_name)

    instructions = build_patient_instructions(
        patient=patient,
        character=character,
    )

    agent = Agent(
        instructions=instructions,
    )

    session = AgentSession(
        stt=inference.STT(
            model=STT_MODEL,
            language="en",
        ),
        llm=inference.LLM(
            model=LLM_MODEL,
        ),
        tts=inference.TTS(
            model=TTS_MODEL,
            voice=TTS_VOICE,
        ),
    )

    await session.start(
        agent=agent,
        room=ctx.room,
    )

    # Patient initiates the conversation.
    await session.generate_reply(
        instructions=(
            "Introduce yourself as the patient. "
            "Start the conversation naturally. "
            "Briefly explain why you are here and invite "
            "the trainee to continue."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
