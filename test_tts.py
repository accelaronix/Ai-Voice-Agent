from app.voice.tts import generate_speech


def main():
    text = (
        "Hi Priyanshu, you recently submitted an enquiry. "
        "Is this a good time to speak?"
    )

    print("Generating speech...")
    print("Text:", text)

    file_path = generate_speech(
        text=text,
        output_file="output.wav"
    )

    print("")
    print("TTS completed successfully.")
    print("Audio created:", file_path)
    print("")
    print("Now play it with:")
    print("aplay output.wav")


if __name__ == "__main__":
    main()