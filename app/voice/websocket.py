import asyncio
import base64
import os
import time
import uuid
import wave

import numpy as np
import webrtcvad

from scipy.signal import resample_poly

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect
)

from app.voice.stt import transcribe_audio
from app.voice.tts import generate_speech
from app.agent.engine import VoiceAgent


router = APIRouter()


# =========================================================
# AUDIO CONFIGURATION
# =========================================================

EXOTEL_SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
CHANNELS = 1

FRAME_DURATION_MS = 20

FRAME_SIZE_BYTES = int(
    EXOTEL_SAMPLE_RATE
    * (FRAME_DURATION_MS / 1000)
    * SAMPLE_WIDTH
)


# =========================================================
# VAD
# =========================================================

vad = webrtcvad.Vad(2)


# Previously:
# END_SILENCE_MS = 700
#
# Reduced for faster conversation response.
END_SILENCE_MS = 350


END_SILENCE_FRAMES = int(
    END_SILENCE_MS
    / FRAME_DURATION_MS
)


# Previously:
# MIN_SPEECH_MS = 300
#
# Reduced so short answers like:
# "हाँ"
# "जी"
# "एक लाख"
# are accepted quickly.
MIN_SPEECH_MS = 160


MIN_SPEECH_FRAMES = int(
    MIN_SPEECH_MS
    / FRAME_DURATION_MS
)


# =========================================================
# SAVE CUSTOMER AUDIO
# =========================================================

def save_audio(
    audio_bytes: bytes,
    file_name: str
):

    with wave.open(
        file_name,
        "wb"
    ) as wav_file:

        wav_file.setnchannels(
            CHANNELS
        )

        wav_file.setsampwidth(
            SAMPLE_WIDTH
        )

        wav_file.setframerate(
            EXOTEL_SAMPLE_RATE
        )

        wav_file.writeframes(
            audio_bytes
        )


# =========================================================
# SEND AI AUDIO TO EXOTEL
# =========================================================

async def send_ai_audio(
    websocket: WebSocket,
    stream_sid: str,
    text: str,
    outgoing_state: dict,
    mark_events: dict,
    ai_speaking: asyncio.Event
):

    if not stream_sid:

        print(
            "Cannot send AI audio: "
            "stream SID missing."
        )

        return

    file_name = (
        f"tts_{uuid.uuid4().hex}.wav"
    )

    mark_name = (
        f"tts-{uuid.uuid4().hex}"
    )

    mark_complete = (
        asyncio.Event()
    )

    mark_events[
        mark_name
    ] = mark_complete

    try:

        ai_speaking.set()

        # =================================================
        # GENERATE TTS
        # =================================================

        tts_start = time.perf_counter()

        print(
            "Generating TTS..."
        )

        await asyncio.to_thread(
            generate_speech,
            text,
            file_name
        )

        tts_elapsed = (
            time.perf_counter()
            - tts_start
        )

        print(
            f"TTS generated in "
            f"{tts_elapsed:.2f}s."
        )

        # =================================================
        # READ WAV
        # =================================================

        with wave.open(
            file_name,
            "rb"
        ) as wav_file:

            channels = (
                wav_file.getnchannels()
            )

            sample_width = (
                wav_file.getsampwidth()
            )

            source_rate = (
                wav_file.getframerate()
            )

            frame_count = (
                wav_file.getnframes()
            )

            raw_audio = (
                wav_file.readframes(
                    frame_count
                )
            )

        print(
            "TTS sample rate:",
            source_rate
        )

        print(
            "TTS channels:",
            channels
        )

        print(
            "TTS sample width:",
            sample_width
        )

        if channels != 1:

            raise ValueError(
                "Expected mono TTS audio."
            )

        if sample_width != 2:

            raise ValueError(
                "Expected 16-bit TTS audio."
            )

        # =================================================
        # CONVERT WAV DATA TO PCM
        # =================================================

        audio_array = np.frombuffer(
            raw_audio,
            dtype="<i2"
        )

        # =================================================
        # RESAMPLE SARVAM AUDIO
        #
        # Sarvam currently gives us 22050 Hz.
        # Exotel expects 16000 Hz.
        # =================================================

        if (
            source_rate
            != EXOTEL_SAMPLE_RATE
        ):

            print(
                f"Resampling "
                f"{source_rate} Hz "
                f"-> "
                f"{EXOTEL_SAMPLE_RATE} Hz"
            )

            audio_array = (
                resample_poly(
                    audio_array,
                    EXOTEL_SAMPLE_RATE,
                    source_rate
                )
            )

            audio_array = np.clip(
                audio_array,
                -32768,
                32767
            ).astype(
                "<i2"
            )

        pcm_audio = (
            audio_array.tobytes()
        )

        # =================================================
        # SEND AUDIO TO EXOTEL
        # =================================================

        print(
            "Sending AI audio to Exotel..."
        )

        # 16 kHz
        # 16-bit mono
        #
        # 3200 bytes =
        # 1600 samples =
        # 100 ms of audio
        chunk_size = 3200

        for position in range(
            0,
            len(pcm_audio),
            chunk_size
        ):

            chunk = pcm_audio[
                position:
                position + chunk_size
            ]

            # Pad last packet if required.
            if len(chunk) < chunk_size:

                chunk += (
                    b"\x00"
                    * (
                        chunk_size
                        - len(chunk)
                    )
                )

            encoded_audio = (
                base64.b64encode(
                    chunk
                ).decode(
                    "utf-8"
                )
            )

            sequence_number = (
                outgoing_state[
                    "sequence"
                ]
            )

            chunk_number = (
                outgoing_state[
                    "chunk"
                ]
            )

            timestamp = int(
                outgoing_state[
                    "audio_ms"
                ]
            )

            await websocket.send_json({
                "event":
                    "media",

                "stream_sid":
                    str(
                        stream_sid
                    ),

                "sequence_number":
                    str(
                        sequence_number
                    ),

                "media": {
                    "chunk":
                        str(
                            chunk_number
                        ),

                    "timestamp":
                        str(
                            timestamp
                        ),

                    "payload":
                        encoded_audio
                }
            })

            outgoing_state[
                "sequence"
            ] += 1

            outgoing_state[
                "chunk"
            ] += 1

            outgoing_state[
                "audio_ms"
            ] += 100

            # Real-time pacing.
            await asyncio.sleep(
                0.1
            )

        print(
            "AI audio packets sent."
        )

        # =================================================
        # PLAYBACK MARK
        #
        # This tells us when Exotel has actually finished
        # playing the AI sentence to the customer.
        # =================================================

        sequence_number = (
            outgoing_state[
                "sequence"
            ]
        )

        await websocket.send_json({
            "event":
                "mark",

            "stream_sid":
                str(
                    stream_sid
                ),

            "sequence_number":
                str(
                    sequence_number
                ),

            "mark": {
                "name":
                    mark_name
            }
        })

        outgoing_state[
            "sequence"
        ] += 1

        print(
            "Waiting for playback mark..."
        )

        try:

            await asyncio.wait_for(
                mark_complete.wait(),
                timeout=15
            )

            print(
                "AI audio playback completed."
            )

        except asyncio.TimeoutError:

            print(
                "Warning: playback mark timed out."
            )

    except asyncio.CancelledError:

        print(
            "TTS task cancelled because "
            "the call/WebSocket ended."
        )

        raise

    except Exception as e:

        print(
            "TTS/Exotel error:",
            type(e).__name__,
            repr(e)
        )

    finally:

        ai_speaking.clear()

        mark_events.pop(
            mark_name,
            None
        )

        if os.path.exists(
            file_name
        ):

            os.remove(
                file_name
            )


# =========================================================
# CONVERSATION WORKER
# =========================================================

async def conversation_worker(
    utterance_queue: asyncio.Queue,
    call_sid: str,
    agent: VoiceAgent,
    websocket: WebSocket,
    stream_sid: str,
    outgoing_state: dict,
    mark_events: dict,
    ai_speaking: asyncio.Event
):

    utterance_number = 0

    while True:

        audio_bytes = (
            await utterance_queue.get()
        )

        if audio_bytes is None:

            utterance_queue.task_done()

            break

        utterance_number += 1

        file_name = (
            f"utterance_"
            f"{call_sid}_"
            f"{utterance_number}.wav"
        )

        try:

            save_audio(
                audio_bytes,
                file_name
            )

            # =================================================
            # STT
            # =================================================

            stt_start = (
                time.perf_counter()
            )

            transcript = (
                await asyncio.to_thread(
                    transcribe_audio,
                    file_name
                )
            )

            stt_elapsed = (
                time.perf_counter()
                - stt_start
            )

            print(
                f"STT completed in "
                f"{stt_elapsed:.2f}s."
            )

            if not transcript:

                continue

            transcript = (
                transcript.strip()
            )

            if not transcript:

                continue

            print(
                "Customer:",
                transcript
            )

            # =================================================
            # AGENT
            # =================================================

            agent_start = (
                time.perf_counter()
            )

            ai_response = (
                agent.process(
                    transcript
                )
            )

            agent_elapsed = (
                time.perf_counter()
                - agent_start
            )

            print(
                f"Agent processing: "
                f"{agent_elapsed:.3f}s"
            )

            print(
                "AI:",
                ai_response
            )

            # =================================================
            # TTS -> EXOTEL
            # =================================================

            await send_ai_audio(
                websocket,
                stream_sid,
                ai_response,
                outgoing_state,
                mark_events,
                ai_speaking
            )

            # =================================================
            # END CONVERSATION
            # =================================================

            if (
                agent.state
                == "closed"
            ):

                print("")
                print(
                    "========================================"
                )

                print(
                    "Conversation completed."
                )

                print(
                    "Final AI response "
                    "finished playing."
                )

                print(
                    "Waiting 2 seconds "
                    "before disconnect..."
                )

                print(
                    "========================================"
                )

                # send_ai_audio() has already received
                # Exotel's playback mark.
                #
                # Therefore the customer should already
                # have heard the complete final sentence.
                await asyncio.sleep(
                    2.0
                )

                print(
                    "Closing Exotel WebSocket..."
                )

                try:

                    await websocket.close(
                        code=1000
                    )

                    print(
                        "Call disconnected "
                        "automatically."
                    )

                except Exception as e:

                    print(
                        "WebSocket close error:",
                        type(e).__name__,
                        repr(e)
                    )

                return

        except asyncio.CancelledError:

            raise

        except Exception as e:

            print(
                "Conversation error:",
                type(e).__name__,
                repr(e)
            )

        finally:

            if os.path.exists(
                file_name
            ):

                os.remove(
                    file_name
                )

            utterance_queue.task_done()


# =========================================================
# EXOTEL WEBSOCKET
# =========================================================

@router.websocket(
    "/voice/media"
)
async def voice_media(
    websocket: WebSocket
):

    await websocket.accept()

    call_start_time = None

    call_sid = None
    stream_sid = None

    frame_buffer = (
        bytearray()
    )

    utterance_buffer = (
        bytearray()
    )

    speech_frame_count = 0
    silence_frame_count = 0

    is_speaking = False

    utterance_queue = (
        asyncio.Queue()
    )

    conversation_task = None
    opening_tts_task = None

    agent = None

    ai_speaking = (
        asyncio.Event()
    )

    mark_events = {}

    outgoing_state = {
        "sequence": 1,
        "chunk": 1,
        "audio_ms": 0
    }

    try:

        while True:

            message = (
                await websocket.receive_json()
            )

            event = (
                message.get(
                    "event"
                )
            )

            # =================================================
            # CONNECTED
            # =================================================

            if event == "connected":

                print(
                    "EVENT: connected"
                )

            # =================================================
            # START
            # =================================================

            elif event == "start":

                print(
                    "EVENT: start"
                )

                call_start_time = (
                    time.time()
                )

                start_data = (
                    message.get(
                        "start",
                        {}
                    )
                )

                call_sid = (
                    start_data.get(
                        "call_sid",
                        "unknown"
                    )
                )

                stream_sid = (
                    message.get(
                        "stream_sid"
                    )
                    or
                    start_data.get(
                        "stream_sid"
                    )
                )

                print(
                    "Call SID:",
                    call_sid
                )

                print(
                    "Stream SID:",
                    stream_sid
                )

                agent = VoiceAgent(
                    "शुभम"
                )

                # =============================================
                # START CUSTOMER RESPONSE WORKER
                # =============================================

                conversation_task = (
                    asyncio.create_task(
                        conversation_worker(
                            utterance_queue,
                            call_sid,
                            agent,
                            websocket,
                            stream_sid,
                            outgoing_state,
                            mark_events,
                            ai_speaking
                        )
                    )
                )

                # =============================================
                # OPENING MESSAGE
                # =============================================

                opening_message = (
                    agent.start()
                )

                print(
                    "AI:",
                    opening_message
                )

                opening_tts_task = (
                    asyncio.create_task(
                        send_ai_audio(
                            websocket,
                            stream_sid,
                            opening_message,
                            outgoing_state,
                            mark_events,
                            ai_speaking
                        )
                    )
                )

            # =================================================
            # PLAYBACK MARK
            # =================================================

            elif event == "mark":

                mark_data = (
                    message.get(
                        "mark",
                        {}
                    )
                )

                mark_name = (
                    mark_data.get(
                        "name"
                    )
                )

                if (
                    mark_name
                    in mark_events
                ):

                    mark_events[
                        mark_name
                    ].set()

            # =================================================
            # MEDIA
            # =================================================

            elif event == "media":

                # =============================================
                # IGNORE CUSTOMER AUDIO WHILE AI IS SPEAKING
                #
                # Prevents AI's own phone audio from being
                # recognised as customer speech.
                # =============================================

                if ai_speaking.is_set():

                    frame_buffer.clear()

                    utterance_buffer.clear()

                    speech_frame_count = 0
                    silence_frame_count = 0

                    is_speaking = False

                    continue

                # Conversation finished.
                if (
                    agent
                    and
                    agent.state
                    == "closed"
                ):

                    continue

                media = (
                    message.get(
                        "media",
                        {}
                    )
                )

                payload = (
                    media.get(
                        "payload"
                    )
                )

                if not payload:

                    continue

                try:

                    audio_bytes = (
                        base64.b64decode(
                            payload
                        )
                    )

                    frame_buffer.extend(
                        audio_bytes
                    )

                except Exception as e:

                    print(
                        "Audio decode error:",
                        type(e).__name__,
                        repr(e)
                    )

                    continue

                # =============================================
                # VAD
                # =============================================

                while (
                    len(
                        frame_buffer
                    )
                    >= FRAME_SIZE_BYTES
                ):

                    frame = bytes(
                        frame_buffer[
                            :FRAME_SIZE_BYTES
                        ]
                    )

                    del frame_buffer[
                        :FRAME_SIZE_BYTES
                    ]

                    try:

                        speech_detected = (
                            vad.is_speech(
                                frame,
                                EXOTEL_SAMPLE_RATE
                            )
                        )

                    except Exception as e:

                        print(
                            "VAD error:",
                            type(e).__name__,
                            repr(e)
                        )

                        continue

                    # =========================================
                    # SPEECH
                    # =========================================

                    if speech_detected:

                        if not is_speaking:

                            is_speaking = True

                            speech_frame_count = 0
                            silence_frame_count = 0

                            utterance_buffer.clear()

                        utterance_buffer.extend(
                            frame
                        )

                        speech_frame_count += 1

                        silence_frame_count = 0

                    # =========================================
                    # SILENCE
                    # =========================================

                    else:

                        if is_speaking:

                            utterance_buffer.extend(
                                frame
                            )

                            silence_frame_count += 1

                            # Customer stopped talking.
                            if (
                                silence_frame_count
                                >= END_SILENCE_FRAMES
                            ):

                                if (
                                    speech_frame_count
                                    >= MIN_SPEECH_FRAMES
                                ):

                                    print(
                                        "Customer speech ended. "
                                        "Sending to STT..."
                                    )

                                    await (
                                        utterance_queue.put(
                                            bytes(
                                                utterance_buffer
                                            )
                                        )
                                    )

                                utterance_buffer.clear()

                                speech_frame_count = 0
                                silence_frame_count = 0

                                is_speaking = False

            # =================================================
            # STOP
            # =================================================

            elif event == "stop":

                print(
                    "STOP DATA:",
                    message
                )

                # If customer was still speaking when
                # the call ended, process final buffered
                # speech only if conversation wasn't closed.
                if (
                    agent
                    and
                    agent.state != "closed"
                    and
                    is_speaking
                    and
                    speech_frame_count
                    >= MIN_SPEECH_FRAMES
                ):

                    await utterance_queue.put(
                        bytes(
                            utterance_buffer
                        )
                    )

                if call_start_time:

                    duration = int(
                        time.time()
                        - call_start_time
                    )

                    print(
                        f"Call duration: "
                        f"{duration} seconds"
                    )

                print(
                    "EVENT: stop"
                )

                print(
                    "Call ended"
                )

                break

    # =====================================================
    # EXOTEL / CLIENT DISCONNECTED
    # =====================================================

    except WebSocketDisconnect:

        if call_start_time:

            duration = int(
                time.time()
                - call_start_time
            )

            print(
                f"Call duration: "
                f"{duration} seconds"
            )

        print(
            "WebSocket disconnected"
        )

        print(
            "Call ended"
        )

    # =====================================================
    # NORMAL CLOSE CAUSED BY OUR OWN websocket.close()
    # =====================================================

    except RuntimeError as e:

        # Starlette may raise a RuntimeError because the main
        # receive loop is still waiting when conversation_worker
        # closes the socket intentionally.

        if (
            agent
            and
            agent.state
            == "closed"
        ):

            print(
                "WebSocket closed after "
                "conversation completion."
            )

        else:

            print(
                "WebSocket RuntimeError:",
                repr(e)
            )

    # =====================================================
    # OTHER ERRORS
    # =====================================================

    except Exception as e:

        print(
            "WebSocket error:",
            type(e).__name__,
            repr(e)
        )

    # =====================================================
    # CLEANUP
    # =====================================================

    finally:

        # Stop opening TTS if call ends before it finishes.
        if (
            opening_tts_task
            and
            not opening_tts_task.done()
        ):

            opening_tts_task.cancel()

            try:

                await opening_tts_task

            except asyncio.CancelledError:

                pass

        # Don't cancel the current conversation worker
        # if it already finished normally.
        if (
            conversation_task
            and
            not conversation_task.done()
        ):

            conversation_task.cancel()

            try:

                await conversation_task

            except asyncio.CancelledError:

                pass