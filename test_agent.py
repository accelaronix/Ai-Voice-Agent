import subprocess

import sounddevice as sd
from scipy.io.wavfile import write

from app.agent.engine import VoiceAgent
from app.voice.stt import transcribe_audio
from app.voice.tts import generate_speech


SAMPLE_RATE = 16000
RECORD_SECONDS = 5


def speak(text: str):
    print("")
    print("AI:", text)

    audio_file = generate_speech(
        text=text,
        output_file="agent_reply.wav"
    )

    subprocess.run(
        ["aplay", audio_file],
        check=False
    )


def listen():
    print("")
    print("Listening... Speak now.")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    file_name = "customer_voice.wav"

    write(
        file_name,
        SAMPLE_RATE,
        audio
    )

    print("Processing your voice...")

    transcript = transcribe_audio(
        file_name
    )

    print("You:", transcript)

    return transcript


def main():
    print("")
    print("====================================")
    print("LOCAL AI VOICE AGENT")
    print("====================================")

    agent = VoiceAgent("Priyanshu")

    # AI starts conversation
    first_message = agent.start()

    speak(first_message)

    while True:

        customer_text = listen()

        if not customer_text:
            print("I could not understand you.")
            continue

        response = agent.process(
            customer_text
        )

        speak(response)

        if agent.state == "closed":
            print("")
            print("====================================")
            print("CALL ENDED")
            print("====================================")
            break


if __name__ == "__main__":
    main()