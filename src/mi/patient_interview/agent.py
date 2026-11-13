import json
import logging
from typing import AsyncIterable

from livekit.agents import (
    Agent,
    ChatContext,
    ChatMessage,
    ModelSettings,
    llm,
)

from mi.patient_interview.schemas import Agent3Output
from mi.patient_interview.prompts import (
    build_agent_instructions,
    build_emotion_context,
)
from mi.patient_interview.state_manager import InterviewStateManager

logger = logging.getLogger("patient-interview")


def extract_json(raw: str) -> dict:
    """Parse JSON from model output, tolerating ```json fences and extra text."""

    text = raw.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: grab the outermost {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


class PatientInterviewAgent(Agent):

    def __init__(self, state_manager, llm_model):

        self.state_manager = state_manager
        self.pending_transcript = None

        patient = state_manager.patient
        character = state_manager.character

        instructions = build_agent_instructions(
            patient=patient,
            character=character,
        )

        super().__init__(
            instructions=instructions,
            llm=llm_model,
        )

    # ------------------------------------------------
    # 1. Opening turn + capture trainee's completed turn
    # ------------------------------------------------

    async def on_enter(self) -> None:
        """Make the patient initiate the interview."""

        logger.info("Patient is initiating the interview.")

        # An empty trainee transcript identifies this as the opening turn.
        self.pending_transcript = ""

        # Generate the patient's opening statement.
        await self.session.generate_reply(
            instructions=(
                "Start the interview as the patient. "
                "Introduce yourself naturally and briefly. "
                "Express how you are feeling about the situation "
                "and invite the trainee to continue the conversation. "
                "Stay completely in character. "
                "Do not mention that you are an AI or a simulation.\n\n"
                + build_emotion_context(self.state_manager.current_state)
            )
        )

    async def on_user_turn_completed(
        self,
        turn_ctx: ChatContext,
        new_message: ChatMessage,
    ) -> None:
        print("\n===== USER TURN COMPLETED =====")
        print("Transcript:", new_message.text_content)
        transcript = new_message.text_content

        if not transcript or not transcript.strip():
            logger.warning("Empty trainee transcript.")
            return

        self.pending_transcript = transcript

        logger.info("Trainee: %s", transcript)

        # Inject the latest emotional state for this turn.
        # This additional context is temporary.
        emotion_context = build_emotion_context(
            self.state_manager.current_state
        )

        turn_ctx.add_message(
            role="system",
            content=emotion_context,
        )

    # ------------------------------------------------
    # 2. Single LLM call
    # ------------------------------------------------

    async def llm_node(
        self,
        chat_ctx: ChatContext,
        tools: list,
        model_settings: ModelSettings,
    ) -> AsyncIterable[str]:

        logger.info("========== CUSTOM LLM NODE STARTED ==========")

        accumulated_output = ""

        try:
            async with self.llm.chat(
                chat_ctx=chat_ctx,
                tools=tools,
                tool_choice=(
                    model_settings.tool_choice
                    if model_settings else None
                ),
            ) as stream:

                async for chunk in stream:

                    # FIX: some chunks (usage/metadata) have no delta
                    if chunk.delta is None:
                        continue

                    content = chunk.delta.content

                    if isinstance(content, str):
                        accumulated_output += content

            logger.info(
                "RAW LLM OUTPUT:\n%s",
                accumulated_output,
            )

            # FIX: tolerate ```json fences / extra text around the JSON
            output_data = extract_json(accumulated_output)

            agent_output = Agent3Output.model_validate(output_data)

            logger.info(
                "VALIDATED AGENT OUTPUT:\n%s",
                agent_output.model_dump_json(indent=2),
            )

            if self.pending_transcript is None:
                raise RuntimeError("No pending trainee transcript.")

            self.state_manager.record_turn(
                trainee_transcript=self.pending_transcript,
                agent_output=agent_output,
            )

            self.pending_transcript = None

            logger.info("INTERVIEW TURN SAVED SUCCESSFULLY")

            yield agent_output.patient_response

        except Exception:
            logger.exception("AGENT 3 LLM NODE FAILED")
            raise