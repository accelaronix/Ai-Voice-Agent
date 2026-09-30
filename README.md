# 🎙️ AI Voice Agent (Hindi / Hinglish Outbound Calling)

An end-to-end intelligent voice agent designed for automated outbound calls, lead qualification, and conversational interactions in Hindi and Hinglish. 

The system integrates **FastAPI**, **SQLite**, **APScheduler**, **Sarvam AI** (for Indian language STT & TTS), **WebRTC VAD** (Voice Activity Detection), and **Exotel Telephony** for real-time bidirectional audio streaming over WebSockets.

---

## 📑 Table of Contents

- [Features](#-features)
- [Architecture Overview](#-architecture-overview)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Local Setup & Installation](#-local-setup--installation)
- [Configuration (.env)](#-configuration-env)
- [Running Local Tests (Mic & Speaker)](#-running-local-tests-mic--speaker)
- [Running the Server](#-running-the-server)
- [Setting Up Exotel Telephony & Tunnels](#-setting-up-exotel-telephony--tunnels)
- [API Reference](#-api-reference)
- [Conversation State Machine](#-conversation-state-machine)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## ✨ Features

- **Real-Time Voice Streaming**: Bidirectional audio streaming over WebSockets (`16 kHz`, 16-bit PCM mono) compatible with Exotel's Audio Streaming API.
- **Indian Language Speech AI**:
  - **Speech-to-Text (STT)**: Powered by Sarvam AI (`saarika:v2.5`) with high accuracy for Hindi and code-switched Hinglish.
  - **Text-to-Speech (TTS)**: Natural Indian voice synthesis using Sarvam AI (`bulbul:v3`, speaker `shubh`) with automated audio resampling (22.05 kHz -> 16 kHz).
- **Voice Activity Detection & Barge-in**:
  - Real-time VAD via `webrtcvad` to detect speech start and end silence.
  - Fast interruption handling (barge-in): immediately cancels AI speech playback if the user starts speaking.
- **Intent Recognition Engine**: Rule-based multilingual intent parser recognizing affirmative, negative/opt-out, callback requests, and polite courtesy phrases across Devanagari, Hinglish, and English tokens.
- **Automated Scheduling**: Lead qualification queue with `APScheduler` and SQLite persistence.
- **Offline / Local Testing**: Includes standalone test scripts to verify microphone input, speech synthesis, and full voice loops without placing live phone calls.

---

## 🏗️ Architecture Overview

```
                          ┌─────────────────────────────┐
                          │     Exotel Telephony        │
                          └──────────────┬──────────────┘
                                         │ Bidirectional Audio (WSS)
                                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application (main.py)                                          │
│                                                                        │
│   ┌─────────────────────┐    ┌──────────────────┐    ┌───────────────┐ │
│   │ /voice/media (WS)   │◄──►│ WebRTC VAD Engine│◄──►│ State Machine │ │
│   └──────────┬──────────┘    └──────────────────┘    │ VoiceAgent    │ │
│              │                                       └───────┬───────┘ │
│              ▼                                               │         │
│   ┌─────────────────────┐                           ┌────────▼───────┐ │
│   │ Sarvam AI (STT/TTS) │                           │ SQLite Database│ │
│   │ - Saarika v2.5      │                           │ - Leads Queue  │ │
│   │ - Bulbul v3         │                           └────────────────┘ │
│   └─────────────────────┘                                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
ai-voice-agent/
├── app/
│   ├── agent/
│   │   ├── engine.py          # Conversational state machine & dialogue manager
│   │   └── intents.py         # Regex & token-based intent detection (Hindi/Eng/Hinglish)
│   ├── api/
│   │   ├── calls.py           # Outbound test call triggers
│   │   └── leads.py           # Lead ingestion & scheduler endpoints
│   ├── database/
│   │   ├── db.py              # SQLite connection & session maker
│   │   └── models.py          # SQLAlchemy Lead model
│   ├── scheduler/
│   │   └── call_scheduler.py  # APScheduler background worker for scheduled calls
│   ├── telephony/
│   │   └── exotel.py          # Exotel REST API client (Call connect, active legs, hangup)
│   └── voice/
│       ├── stt.py             # Sarvam AI STT integration
│       ├── tts.py             # Sarvam AI TTS integration
│       └── websocket.py       # Exotel WebSocket audio handler (VAD, resampling, streaming)
├── main.py                    # FastAPI application entrypoint
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── test_agent.py              # Local voice loop test (Mic -> STT -> Agent -> TTS -> Speaker)
├── test_stt.py                # Local microphone recording & STT test
├── test_tts.py                # Local TTS audio generation test
└── README.md                  # Project documentation
```

---

## ⚙️ Prerequisites

1. **Python**: Python 3.10, 3.11, or 3.12.
2. **System Audio Packages** (Required for local audio recording, playback, and VAD compilation):
   - **Ubuntu / Debian**:
     ```bash
     sudo apt-get update
     sudo apt-get install -y portaudio19-dev libasound2-dev alsa-utils python3-dev build-essential
     ```
   - **macOS** (Homebrew):
     ```bash
     brew install portaudio
     ```
3. **API Keys**:
   - [Sarvam AI](https://www.sarvam.ai/) API Key (subscription key for STT and TTS).
   - [Exotel](https://exotel.com/) Account (Account SID, API Key, API Token, Virtual Caller ID) *only required for phone calls*.
4. **Public Tunnel Tool** (for Exotel webhook/streaming delivery):
   - [Cloudflare Tunnel (`cloudflared`)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or [ngrok](https://ngrok.com/).

---

## 🚀 Local Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/accelaronix/Ai-Voice-Agent.git
cd Ai-Voice-Agent
```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

*(On Windows PowerShell: `.\venv\Scripts\Activate.ps1`)*

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
# Sarvam AI Credentials (Required for voice processing)
SARVAM_API_KEY=your_actual_sarvam_api_key

# Exotel Telephony Credentials (Required for real outbound phone calls)
EXOTEL_ACCOUNT_SID=your_exotel_account_sid
EXOTEL_API_KEY=your_exotel_api_key
EXOTEL_API_TOKEN=your_exotel_api_token
EXOTEL_CALLER_ID=your_exotel_virtual_caller_id
```

---

## 🧪 Running Local Tests (Mic & Speaker)

You can test the entire voice agent on your local machine using your computer's microphone and speakers before wiring up Exotel.

### Test 1: Speech Synthesis (TTS)
Verifies Sarvam AI TTS generation and local playback:
```bash
python test_tts.py
# Play the generated audio file:
aplay output.wav    # On Linux
# or open output.wav on macOS / Windows
```

### Test 2: Speech Recognition (STT)
Records 5 seconds of audio from your microphone and prints the transcript from Sarvam AI:
```bash
python test_stt.py
```

### Test 3: Full Local Conversational Loop
Runs the complete interactive voice loop locally. The agent will speak the initial greeting through your speaker, listen for your voice via microphone, transcribe it, classify your intent, and respond:
```bash
python test_agent.py
```

---

## 💻 Running the Server

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Server Health Check**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📞 Setting Up Exotel Telephony & Tunnels

Exotel needs to establish a WebSocket connection with your local server to stream bidirectional audio.

### 1. Expose Local Server via Cloudflare Tunnel or Ngrok

**Using Cloudflare Tunnel:**
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```
This gives you a public HTTPS URL like:
`https://your-tunnel-subdomain.trycloudflare.com`

**Using Ngrok:**
```bash
ngrok http 8000
```
This gives you a public URL like:
`https://your-subdomain.ngrok-free.app`

### 2. Update the Stream URL

In [app/api/calls.py](file:///home/accelaronix-priyanshu/ai-voice-agent/app/api/calls.py), update `stream_url` to match your tunnel domain using the WebSocket protocol (`wss://`):

```python
stream_url = (
    "wss://your-tunnel-subdomain.trycloudflare.com/voice/media?sample-rate=16000"
)
```

### 3. Initiate an Outbound Call

Make a POST request to trigger a real call to your test phone number:

```bash
curl -X POST "http://127.0.0.1:8000/calls/test" \
     -H "Content-Type: application/json" \
     -d '{"phone": "+91XXXXXXXXXX"}'
```

When you answer the call, Exotel connects to `/voice/media`, and the AI agent begins speaking with low latency.

---

## 📡 API Reference

### 1. Health Check
`GET /`
- Response: `{"message": "AI Voice Agent is running"}`

### 2. Ingest & Schedule Lead
`POST /leads`
- Automatically stores lead and schedules an outbound call.
- **Request Body**:
  ```json
  {
    "name": "Rohan Sharma",
    "phone": "+919876543210",
    "source": "facebook_ads"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Rohan Sharma",
    "phone": "+919876543210",
    "source": "facebook_ads",
    "status": "scheduled",
    "call_at": "2026-09-30T10:30:10Z"
  }
  ```

### 3. Direct Outbound Test Call
`POST /calls/test`
- Triggers an instant outbound phone call via Exotel.
- **Request Body**:
  ```json
  {
    "phone": "+919876543210"
  }
  ```

### 4. Voice Streaming WebSocket
`WSS /voice/media?sample-rate=16000`
- Exotel streaming endpoint handling bidirectional PCM packets, audio buffering, VAD, and barge-in.

---

## 🧠 Conversation State Machine

The conversation is managed through discrete states defined in [app/agent/engine.py](file:///home/accelaronix-priyanshu/ai-voice-agent/app/agent/engine.py):

| Current State | User Intent | Next State | AI Response Summary |
|---|---|---|---|
| `permission` (Initial) | `YES` ("हाँ", "जी", "yes") | `course` | Asks which course the user is interested in. |
| `permission` | `CALLBACK` ("बाद में कॉल करना", "busy") | `callback` | Asks for a preferred callback time. |
| `permission` | `NOT_INTERESTED` ("नहीं", "no thanks") | `closed` | Cordially closes the call and triggers auto-hangup. |
| `permission` | `COURTESY` ("thanks", "शुक्रिया") | `permission` | Welcomes user and re-prompts for permission. |
| `course` | Any course enquiry response | `closed` | Informs that an advisor will get in touch shortly. |
| `callback` | Any preferred time response | `closed` | Confirms scheduled callback time. |
| `closed` | Any | `closed` | Final parting greeting. |

---

## 🛠️ Troubleshooting & FAQs

### 1. `ImportError` or `sounddevice.PortAudioError`
- **Cause**: Missing PortAudio development libraries on your system.
- **Fix**: Run `sudo apt-get install -y portaudio19-dev libasound2-dev alsa-utils` (Linux) or `brew install portaudio` (macOS).

### 2. `RuntimeError: SARVAM_API_KEY is missing from .env`
- **Cause**: `.env` file does not exist or does not contain `SARVAM_API_KEY`.
- **Fix**: Ensure your `.env` file exists in the root folder with a valid `SARVAM_API_KEY`.

### 3. `aplay: command not found`
- **Cause**: ALSA audio utilities are not installed on your Linux machine.
- **Fix**: Install via `sudo apt-get install -y alsa-utils`. Alternatively on macOS, replace `aplay` with `afplay` in `test_agent.py` and `test_tts.py`.

### 4. Exotel Call Hangs Up Immediately or Stream Fails
- Ensure your tunnel (Cloudflare or ngrok) is actively running.
- Verify that `stream_url` in [app/api/calls.py](file:///home/accelaronix-priyanshu/ai-voice-agent/app/api/calls.py) uses `wss://` and points to your current tunnel URL.
- Verify your Exotel credentials and ensure your Exotel account has active balance and outbound call permissions.

---

## 📄 License

This project is licensed under the MIT License.
