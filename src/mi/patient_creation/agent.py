
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .schemas import PatientCreationTurn
from .prompts import PATIENT_CREATION_SYSTEM_PROMPT


# Load environment variables
load_dotenv()


class PatientCreationAgent:

    def __init__(self):

        # Read configuration
        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.1-flash-lite"
        )

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from .env"
            )

        # Initialize Gemini client
        self.client = genai.Client(
            api_key=self.api_key
        )

        # Configure structured output
        config = types.GenerateContentConfig(

            system_instruction=PATIENT_CREATION_SYSTEM_PROMPT,

            response_mime_type="application/json",

            response_schema=PatientCreationTurn,

            temperature=0.3
        )

        # Create a persistent chat session
        self.chat = self.client.chats.create(
            model=self.model,
            config=config
        )

    def _send_message(self, message: str) -> PatientCreationTurn:

        response = self.chat.send_message(message)

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # Convert Gemini's JSON response into a Pydantic object
        result = PatientCreationTurn.model_validate_json(
            response.text
        )

        return result

    def start(self) -> PatientCreationTurn:

        initial_message = """
        You are a MI patient creation agent. 

        Greet the trainee briefly and ask the opening
        question specified in your instructions.

        The patient profile is currently empty.
        """

        return self._send_message(initial_message)

    def respond(self, user_message: str) -> PatientCreationTurn:

        if not user_message.strip():
            raise ValueError("Message cannot be empty.")

        return self._send_message(user_message)
