# Turbo Translate

Real-time multilingual speech translation with speaker diarization. Designed to help you follow conversations in foreign languages at family gatherings, with automatic translation and text-to-speech output.

## Features

- **Real-time Speech-to-Text**: Continuous listening with voice activity detection
- **Speaker Diarization**: Identify and color-code different speakers in the conversation
- **Bidirectional Translation**: Hungarian ↔ English (configurable for other languages)
- **Text-to-Speech**: Speak your translated words aloud for others to hear
- **Visual Transcript**: Full conversation history with speaker labels and colors
- **Blue Orb UI**: Animated waveform visualization showing listening state

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Computer                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Turbo Translate Client                      │   │
│  │  - Audio capture & VAD                                   │   │
│  │  - Blue orb visualization                                │   │
│  │  - Transcript panel with speaker colors                  │   │
│  │  - TTS audio playback                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ VPN Connection
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│           black-panther (192.168.1.89)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Whisper    │  │  Diarization │  │    Translation       │  │
│  │   :8000      │  │    :8001     │  │      :8002           │  │
│  │              │  │              │  │  (LibreTranslate)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐                                               │
│  │     TTS      │                                               │
│  │    :8003     │                                               │
│  │  (Coqui TTS) │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Client (Your Computer)

- Python 3.10+
- PortAudio (for audio capture)
- VPN connection to black-panther network

### Server (black-panther)

- Docker with nvidia-container-toolkit
- NVIDIA GPU with CUDA support
- HuggingFace account with access to pyannote models

## Installation

### Client Setup

1. **Install system dependencies (Linux)**:
   ```bash
   sudo apt install portaudio19-dev python3-dev
   ```

2. **Clone and install**:
   ```bash
   cd ~/GitHub/turbo-translate
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **Connect to VPN** to access black-panther

### Server Setup (on black-panther)

1. **Copy the docker folder to black-panther**:
   ```bash
   scp -r docker/ benw@192.168.1.89:~/turbo-translate-backend/
   ```

2. **SSH to black-panther and set up**:
   ```bash
   ssh benw@192.168.1.89
   cd ~/turbo-translate-backend

   # Create .env file with your HuggingFace token
   cp .env.example .env
   nano .env  # Add your HF token

   # Start services
   docker compose up -d
   ```

3. **Accept pyannote model licenses** at HuggingFace:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

## Usage

1. **Connect to VPN**

2. **Start the application**:
   ```bash
   turbo-translate
   ```

3. **Click "Start Listening"** or press `Alt+Space`

4. **The conversation will appear** in the transcript panel with:
   - Original text in the source language
   - Translated text below
   - Color-coded speaker labels

5. **When you speak in English**, it will be:
   - Transcribed and translated
   - Spoken aloud in Hungarian via TTS

## Configuration

Configuration is stored in `~/.config/turbo-translate/config.json`

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `server_host` | 192.168.1.89 | Backend server address |
| `source_language` | hu | Language being spoken (Hungarian) |
| `target_language` | en | Language to translate to (English) |
| `hotkey` | alt+space | Toggle listening hotkey |
| `tts_enabled` | true | Enable text-to-speech output |
| `voice_activity_timeout` | 2.0 | Seconds of silence before processing |

### Supported Languages

- Hungarian (hu)
- English (en)
- German (de)
- Spanish (es)

## Hotkeys

| Hotkey | Action |
|--------|--------|
| `Alt+Space` | Toggle listening |
| `Ctrl+Shift+E` | Enroll your voice (for speaker identification) |

## Troubleshooting

### No audio input
- Check microphone permissions
- Verify the correct input device is selected in Settings
- On Linux with PipeWire, install `pipewire-alsa`

### Cannot connect to backend
- Ensure VPN is connected
- Verify services are running: `docker compose ps`
- Check service health: `curl http://192.168.1.89:8000/health`

### Diarization not working
- Ensure HuggingFace token is set in `.env`
- Accept model licenses on HuggingFace
- Check diarization logs: `docker compose logs diarization`

### Translation errors
- LibreTranslate needs time to download language models on first run
- Check logs: `docker compose logs translation`

## License

MIT
