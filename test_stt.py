import sounddevice as sd
from scipy.io.wavfile import write

from app.voice.stt import transcribe_audio


SAMPLE_RATE = 16000
DURATION = 5


def main():
    print("Speak now...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    file_name = "microphone_test.wav"

    write(
        file_name,
        SAMPLE_RATE,
        audio
    )

    print("Recording saved.")
    print("Sending to Sarvam STT...")

    transcript = transcribe_audio(
        file_name
    )

    print("")
    print("Transcript:")
    print(transcript)


if __name__ == "__main__":
    main()