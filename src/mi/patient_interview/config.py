
from livekit.agents import inference


STT_MODEL = "deepgram/flux-general"
LLM_MODEL = "google/gemma-4-31b-it"
TTS_MODEL = "fishaudio/s2.1-pro"
TTS_VOICE = "fa4c9eb3dccc4806b382b40d61c6b10a"


# Turn detection
def create_turn_detector():
    return inference.TurnDetector()
