import os
os.environ["PATH"] += os.pathsep + r"C:\mpv"

import assemblyai as aai
import httpx
import json
import time
import sys
import threading
import asyncio
import tempfile
import simpleaudio as sa
from pydub import AudioSegment
from edge_tts import Communicate


class AI_Assistant:
    def __init__(self):
        aai.settings.api_key = "fd8e0b5e64df45be9e09aaa066933b23"
        self.openrouter_api_key = "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"
        self.transcriber = None
        self.language = "english"
        self.tts_voice = "en-US-JennyNeural"

        self.full_transcript = [
            {
                "role": "system",
                "content": """
You are a friendly, natural-sounding AI assistant for voice conversations.

Use these speech-control tags in your replies:
- <break> for pauses
- <rate level='slow'>...</rate> to speak slowly
- <pitch level='high'>...</pitch> to sound cheerful
- <emphasis level='strong'>...</emphasis> to highlight key parts

Always speak casually and naturally. Use contractions like "you're", "let's", and add <break> after greetings or long sentences.

If the user says to speak in Japanese, continue in Japanese using the same style. If they ask for English, switch back to English.
"""
            }
        ]

###### Step 1: Real-time Transcription ######

    def start_transcription(self):
        self.transcriber = aai.RealtimeTranscriber(
            sample_rate=16000,
            on_data=self.on_data,
            on_error=self.on_error,
            on_open=self.on_open,
            on_close=self.on_close,
            end_utterance_silence_threshold=1000
        )
        self.transcriber.connect()
        mic_stream = aai.extras.MicrophoneStream(sample_rate=16000)
        self.transcriber.stream(mic_stream)

    def stop_transcription(self):
        if self.transcriber:
            self.transcriber.close()
            self.transcriber = None

    def on_open(self, session_opened: aai.RealtimeSessionOpened):
        print(" Session ID:", session_opened.session_id)

    def on_data(self, transcript: aai.RealtimeTranscript):
        if not transcript.text:
            return
        if isinstance(transcript, aai.RealtimeFinalTranscript):
            self.generate_ai_response(transcript)
        else:
            print("", transcript.text, end="\r")

    def on_error(self, error: aai.RealtimeError):
        print(" Error occurred:", error)

    def on_close(self):
        print(" Transcription session closed.")

###### Step 2: Generate AI Response ######

    def generate_ai_response(self, transcript):
        self.stop_transcription()

        user_input = transcript.text.strip()
        user_input_lower = user_input.lower()
        print(f"\n👤 User: {user_input}\n")

        if user_input_lower in ["exit", "quit"]:
            print("👋 Exiting voice assistant.")
            self.generate_audio("Thank you for chatting. Goodbye!")
            time.sleep(2)
            sys.exit(0)

        if "japanese" in user_input_lower or "日本語" in user_input_lower:
            self.language = "japanese"
            self.tts_voice = "ja-JP-NanamiNeural"
            self.full_transcript.append({"role": "user", "content": user_input})
            self.generate_audio("わかりました。これからは日本語でお話しします。")
            self.start_transcription()
            return

        if "english" in user_input_lower or "英語" in user_input_lower:
            self.language = "english"
            self.tts_voice = "en-US-JennyNeural"
            self.full_transcript.append({"role": "user", "content": user_input})
            self.generate_audio("Alright, I'll continue in English.")
            self.start_transcription()
            return

        self.full_transcript.append({"role": "user", "content": user_input})

        self.full_transcript.append({
            "role": "system",
            "content": f"Continue speaking in {self.language} using friendly tone and speech-control tags."
        })

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Voice Chat Assistant"
        }

        payload = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": self.full_transcript,
            "stream": True
        }

        try:
            full_reply = ""
            buffer = ""
            speak_started = False

            def speak_async(text_chunk):
                threading.Thread(target=self.generate_audio, args=(text_chunk,), daemon=True).start()

            with httpx.stream("POST", "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0) as response:
                for line in response.iter_lines():
                    line_str = line.decode("utf-8").strip() if isinstance(line, bytes) else line.strip()
                    if line_str.startswith("data: "):
                        raw = line_str[6:]
                        if raw == "[DONE]":
                            break
                        try:
                            data = json.loads(raw)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                print(delta, end="", flush=True)
                                buffer += delta
                                full_reply += delta

                                if not speak_started and (len(buffer) > 40 or "." in buffer):
                                    speak_async(buffer.strip())
                                    speak_started = True
                        except Exception as e:
                            print(" Parsing error:", e)

            if not speak_started and full_reply:
                self.generate_audio(full_reply)

            self.full_transcript.append({"role": "assistant", "content": full_reply})

        except Exception as e:
            print(" OpenRouter Error:", e)
            self.generate_audio("Sorry, I had a problem understanding. Please try again.")

        time.sleep(0.5)
        self.start_transcription()

###### Step 3: Edge-TTS Integration ######

    def generate_audio(self, text):
        print(f"\n🤖 Assistant: {text} — starting TTS...")

        def run_tts():
            async def speak():
                try:
                    communicate = Communicate(text=text, voice=self.tts_voice)
                    async for chunk in communicate.stream():
                        if "audio" in chunk:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_tmp:
                                mp3_tmp.write(chunk["audio"])
                                mp3_tmp.flush()

                                try:
                                    audio = AudioSegment.from_file(mp3_tmp.name, format="mp3")
                                    wav_path = mp3_tmp.name.replace(".mp3", ".wav")
                                    audio.export(wav_path, format="wav")
                                    print(f"💾 Exported to WAV: {wav_path}")

                                    wave_obj = sa.WaveObject.from_wave_file(wav_path)
                                    print("🔊 Playing audio chunk...")
                                    play_obj = wave_obj.play()
                                    play_obj.wait_done()
                                except Exception as e:
                                    print(" Playback error:", e)
                except Exception as e:
                    print(" TTS Error:", e)

            try:
                asyncio.run(speak())
            except RuntimeError as e:
                print(" Event Loop Error:", e)

        threading.Thread(target=run_tts, daemon=True).start()

###### Step 4: Run Assistant ######

if __name__ == "__main__":
    greeting = "<pitch level='high'>Hello!</pitch> <break> I'm your AI voice assistant. <rate level='slow'>What would you like to talk about today?</rate>"
    ai_assistant = AI_Assistant()
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_transcription()
