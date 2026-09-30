import os
import requests

from dotenv import load_dotenv


load_dotenv()


SARVAM_API_KEY = os.getenv(
    "SARVAM_API_KEY"
)


if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is missing from .env"
    )


def transcribe_audio(
    file_path: str
) -> str:

    url = (
        "https://api.sarvam.ai/"
        "speech-to-text"
    )

    headers = {
        "api-subscription-key":
            SARVAM_API_KEY
    }

    with open(
        file_path,
        "rb"
    ) as audio_file:

        files = {
            "file": (
                "audio.wav",
                audio_file,
                "audio/wav"
            )
        }

        data = {
            "model":
                "saarika:v2.5",

            "language_code":
                "hi-IN"
        }

        response = requests.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

    print(
        "STT status:",
        response.status_code
    )

    if not response.ok:

        print(
            "STT response:",
            response.text
        )

    response.raise_for_status()

    result = response.json()

    return result.get(
        "transcript",
        ""
    )