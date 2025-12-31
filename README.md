# Voice-Based Conversational Assistant

A real-time AI voice assistant that can hear user input, process it intelligently, and reply instantly through synthesized speech. It is built using:

-  OpenRouter with Gemma / Mistral large language models
-  AssemblyAI for live speech-to-text (STT) transcription
-  ElevenLabs for natural-sounding text-to-speech (TTS)
-  Dynamic language switching between English 🇺🇸 and Japanese 🇯🇵

## Interaction Flow

1. User speaks → Audio is captured through the microphone
2. AssemblyAI converts spoken audio into text in real time
3. The transcribed text is forwarded to the OpenRouter LLM for a streaming response
4. The complete response is sent to ElevenLabs to generate speech audio
5. The assistant replies aloud using `<pitch>`, `<rate>`, and `<break>` speech tags
6. The assistant switches to Japanese when the user requests a language change
   
## Tech Stack

| Component | Tool |
|----------|------|
| STT | AssemblyAI (RealtimeTranscriber) |
| LLM | OpenRouter API (Gemma/Mistral with streaming) |
| TTS | ElevenLabs (doesn't support streaming) |
| Platform | Python |

#  Language Switching

- Say "**Japanese**" or "**日本語**" → switches to Japanese
- Say "**English**" or "**英語**" → switches to English

  ##  Limitations

- ElevenLabs requires full text before speaking (no streaming TTS)
- FishSpeech and Coqui TTS failed to install (C++/build errors)
- I tried edge tts which allows streaming audio is not working for edge tts the reason is my system is not compatable

  ## ⚖️ Tech Tradeoffs

| Feature | Attempted | Result |
|--------|-----------|--------|
| Streaming TTS | `edge-tts`, `FishSpeech`, `Coqui TTS` | Build errors / incompatible with Windows |
| Stable TTS | `ElevenLabs` | Fast and clear, but requires full text (non-streaming) |


### Setup Instructions

1. clone the repository
```bash
git clone https://github.com/your-username/voice-chat-assistant.git
cd voice-chat-assistant

2. Setup the python environment
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

3. install the dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

4. Setup environment variables
ASSEMBLYAI_API_KEY=your_assemblyai_key
OPENROUTER_API_KEY=your_openrouter_key
ELEVENLABS_API_KEY=your_elevenlabs_key

5.(Windows Only) Add MPV to System PATH
Download MPV 
Extract and place the folder in C:\mpv
import os
os.environ["PATH"] += os.pathsep + r"C:\mpv"

6. Run the Assistant
python assistant.py
