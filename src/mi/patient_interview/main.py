
import json
import logging
from pathlib import Path

from livekit import agents
from livekit.agents import (
    AgentServer,
    AgentSession,
    TurnHandlingOptions,
    inference,
)

from mi.patient_creation.schemas import PatientProfile
from mi.character_creation.schemas import CharacterCollection
from mi.patient_interview.agent import PatientInterviewAgent
from mi.patient_interview.state_manager import InterviewStateManager
from mi.patient_interview.config import (
    STT_MODEL,
    LLM_MODEL,
    TTS_MODEL,
    TTS_VOICE,
)
from dotenv import load_dotenv

load_dotenv(".env") 

# --------------------------------------------------
# Configuration
# --------------------------------------------------

logger = logging.getLogger("patient-interview")

ROOT_DIR = Path(__file__).resolve().parents[3]

PATIENT_FILE = ROOT_DIR / "data" / "patient_profile.json"
CHARACTER_FILE = ROOT_DIR / "data" / "character_profiles.json"

SELECTED_CHARACTER_ID = "arthur_03_friendly"  # Change this to the desired character ID

server = AgentServer()


# --------------------------------------------------
# Load patient and character data
# --------------------------------------------------

def load_interview_data():

    with open(PATIENT_FILE, "r", encoding="utf-8") as file:
        patient_data = json.load(file)

    with open(CHARACTER_FILE, "r", encoding="utf-8") as file:
        character_data = json.load(file)

    patient_id = character_data["patient_id"]

    patient = PatientProfile.model_validate(patient_data)

    character_collection = CharacterCollection.model_validate(
        character_data
    )

    selected_character = next(
        (
            character
            for character in character_collection.characters
            if character.character_id == SELECTED_CHARACTER_ID
        ),
        None,
    )

    if selected_character is None:
        raise ValueError(
            f"Character '{SELECTED_CHARACTER_ID}' was not found."
        )

    return patient, patient_id, selected_character


# --------------------------------------------------
# Agent entrypoint
# --------------------------------------------------

@server.rtc_session(
    agent_name="patient-interview",
)
async def entrypoint(ctx: agents.JobContext):

    # 1. Load patient and selected character

    patient, patient_id, selected_character = load_interview_data()

    logger.info(
        "Patient: %s",
        patient.basic_information.name,
    )

    logger.info(
        "Character: %s",
        selected_character.character_name,
    )

    # 2. Initialize interview state manager

    state_manager = InterviewStateManager(
        patient=patient,
        character=selected_character,
        patient_id=patient_id,
    )

    # 3. Finalize interview when the job shuts down

    async def finalize_interview():

        try:
            state_manager.end_session()

            logger.info(
                "Interview saved successfully. Session ID: %s",
                state_manager.session_id,
            )

        except Exception:
            logger.exception(
                "Failed to finalize interview."
            )

    ctx.add_shutdown_callback(finalize_interview)

    # 4. Initialize LLM once

    llm_model = inference.LLM(
        model=LLM_MODEL,
    )

    # 5. Initialize custom patient agent

    patient_agent = PatientInterviewAgent(
        state_manager=state_manager,
        llm_model=llm_model,
    )

    # 6. Configure voice pipeline

    session = AgentSession(
        stt=inference.STT(
            model=STT_MODEL,
            language="en",
        ),

        llm=llm_model,

        tts=inference.TTS(
            model=TTS_MODEL,
            voice=TTS_VOICE,
        ),

        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    # 7. Start session

    await session.start(
        room=ctx.room,
        agent=patient_agent,
    )

    logger.info(
        "Patient interview session started."
    )


# --------------------------------------------------
# Run server
# --------------------------------------------------

if __name__ == "__main__":
    agents.cli.run_app(server)
