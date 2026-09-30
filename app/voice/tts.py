import os

from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save


load_dotenv()


SARVAM_API_KEY = os.getenv(
    "SARVAM_API_KEY"
)


if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is missing from .env"
    )


client = SarvamAI(
    api_subscription_key=SARVAM_API_KEY
)


def generate_speech(
    text: str,
    output_file: str = "output.wav"
):

    print(
        "TTS text:",
        text
    )

    try:

        audio = client.text_to_speech.convert(
            text=text,
            language_code="hi-IN",
            model="bulbul:v3",
            speaker="shubh"
        )

        save(
            audio,
            output_file
        )

        print(
            "Hindi TTS generated successfully."
        )

        return output_file

    except Exception as e:

        print(
            "Hindi TTS ERROR:",
            type(e).__name__,
            repr(e)
        )

        raise