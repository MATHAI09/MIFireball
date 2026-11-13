
import json
import os

from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

from .schemas import CharacterCreationTurn
from .prompts import CHARACTER_CREATION_SYSTEM_PROMPT

load_dotenv()


class CharacterCreationAgent:

    def __init__(
        self,
        patient_profile_path="data/patient_profile.json"
    ):

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.1-flash-lite"
        )

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from .env"
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        self.patient_profile = self._load_patient_profile(
            patient_profile_path
        )

        self.trainee_confirmed = False

        self.confirmation_pending = False

        self.config = types.GenerateContentConfig(
            system_instruction=CHARACTER_CREATION_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=CharacterCreationTurn,
            temperature=0.7
        )

        self.chat = self.client.chats.create(
            model=self.model,
            config=self.config
        )

    # =========================================
    # 1. Load Patient Profile
    # =========================================

    def _load_patient_profile(self, path):

        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Patient profile not found: {file_path}"
            )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            profile = json.load(file)

        if not isinstance(profile, dict):
            raise ValueError(
                "Patient profile must be a JSON object."
            )

        basic_info = profile.get(
            "basic_information", {}
        )

        if not basic_info.get("name"):
            raise ValueError(
                "Patient name is missing from patient_profile.json."
            )

        if not profile.get("patient_id"):
            raise ValueError(
                "patient_id is missing from patient_profile.json."
            )

        return profile

    # =========================================
    # 2. Send Message to Gemini
    # =========================================

    def _send_message(
        self,
        message: str
    ) -> CharacterCreationTurn:

        response = self.chat.send_message(message)
        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        turn = CharacterCreationTurn.model_validate_json(
            response.text
        )
        turn = CharacterCreationTurn.model_validate_json(response.text)

        self._validate_turn(turn)

        return turn

    # =========================================
    # 3. Validate Character Collection
    # =========================================

    def _validate_turn(
        self,
        turn: CharacterCreationTurn
    ):

        collection = turn.character_collection

        expected_patient_id = self.patient_profile["patient_id"]

        expected_patient_name = (
            self.patient_profile["basic_information"]["name"]
        )

        if collection.patient_id != expected_patient_id:
            raise ValueError(
                "Incorrect patient ID in character collection."
            )

        if collection.patient_name != expected_patient_name:
            raise ValueError(
                "Incorrect patient name in character collection."
            )

        # Check unique character IDs

        character_ids = [
            character.character_id
            for character in collection.characters
        ]

        if len(character_ids) != len(set(character_ids)):
            raise ValueError(
                "Duplicate character IDs detected."
            )

        # Check unique character names

        character_names = [
            character.character_name.lower()
            for character in collection.characters
        ]

        if len(character_names) != len(set(character_names)):
            raise ValueError(
                "Duplicate character names detected."
            )

        # Check trainee-provided behaviour

        supplied_behaviours = {
            item["behaviour"]
            for item in self.patient_profile.get(
                "trainee_provided_behaviour", []
            )
            if item.get("behaviour")
        }

        for character in collection.characters:

            character_behaviours = set(
                character.behavioural_characteristics.trainee_provided
            )

            if not supplied_behaviours.issubset(
                character_behaviours
            ):
                raise ValueError(
                    f"Character {character.character_id} "
                    "is missing trainee-provided behaviour."
                )

        # Initial generation must contain exactly three characters

        if (
            turn.action == "present_characters"
            and len(collection.characters) != 3
        ):
            raise ValueError(
                "Initial generation must contain exactly three characters."
            )

        # Validate collection confirmation status

        if collection.status == "confirmed":
            if turn.action != "confirm_collection":
                raise ValueError(
                    "Confirmed collection must use confirm_collection action."
                )

            if not self.confirmation_pending:
                raise ValueError(
                    "Unexpected collection confirmation."
                )

        elif turn.action == "confirm_collection":
            if collection.status != "awaiting_confirmation":
                raise ValueError(
                    "Collection must await confirmation before approval."
                )

    # =========================================
    # 4. Start Character Generation
    # =========================================

    def start(self) -> CharacterCreationTurn:

        patient_json = json.dumps(
            self.patient_profile,
            indent=4,
            ensure_ascii=False
        )
        
        initial_message = f"""
        Start character creation for this patient.

        PATIENT PROFILE:

        {patient_json}

        Generate exactly THREE distinct character variations.

        Each character must:

        - Represent the same patient.
        - Have a unique character ID.
        - Have a descriptive character name.
        - Preserve all trainee-provided behavioural information.
        - Have a distinct personality.
        - Have a distinct communication style.
        - Have independent emotional tendencies.
        - Have an independent initial emotional state.

        Present all three characters to the trainee.

        Ask whether the trainee wants to:
        1. Use the generated characters.
        2. Modify an existing character.
        3. Create an additional character.

        Do not finalize the collection yet.
        """

        return self._send_message(initial_message)

    # =========================================
    # 5. Continue Refinement
    # =========================================

    def respond(
        self,
        user_message: str
    ) -> CharacterCreationTurn:

        if not user_message.strip():
            raise ValueError(
                "Message cannot be empty."
            )

        # If the trainee explicitly requests confirmation,
        # mark that we are expecting a confirmation response.

        if self._is_confirmation_request(user_message):
            self.confirmation_pending = True

        else:
            self.confirmation_pending = False

        turn = self._send_message(user_message)

        return turn

    # =========================================
    # 6. Detect Explicit Confirmation Request
    # =========================================

    @staticmethod
    def _is_confirmation_request(message: str) -> bool:

        normalized = message.strip().lower()

        confirmation_phrases = [
            "i confirm",
            "i explicitly confirm",
            "i approve",
            "i am satisfied",
            "yes, confirm",
            "yes confirm",
            "confirm and save",
            "approve the collection",
            "i accept the characters"
        ]

        return any(
            phrase in normalized
            for phrase in confirmation_phrases
        )

    # =========================================
    # 7. Save Confirmed Collection
    # =========================================

    def save_collection(
        self,
        turn: CharacterCreationTurn,
        output_path="data/character_profiles.json"
    ):

        if not self.trainee_confirmed:
            raise ValueError(
                "Trainee confirmation is required before saving."
            )

        if turn.character_collection.status != "confirmed":
            raise ValueError(
                "Character collection is not confirmed."
            )

        self._validate_turn(turn)

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                turn.character_collection.model_dump(),
                file,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"\nCharacter collection saved: {output_file}"
        )