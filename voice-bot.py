import os
os.environ["PATH"] += os.pathsep + r"C:\mpv"

import assemblyai as aai
from elevenlabs import generate, stream
import httpx
import json
import time
import sys

class AI_Assistant:
    def __init__(self):
        aai.settings.api_key = "fd8e0b5e64df45be9e09aaa066933b23"
        self.openrouter_api_key = "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"
        self.elevenlabs_api_key = "sk_774aa0bdb22ff59d6c47ac425256526c9d3825b6b47116d2"

        self.transcriber = None
        self.language = "english"

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

###### Step 2: Generate AI Response with Language Switching ######

    def generate_ai_response(self, transcript):
        self.stop_transcription()

        user_input = transcript.text.strip()
        user_input_lower = user_input.lower()
        print(f"\n👤 User: {user_input}\n")

        # Exit check
        if user_input_lower in ["exit", "stop", "quit"]:
            print("👋 Exiting voice assistant.")
            self.generate_audio("Thank you for chatting. Goodbye!")
            time.sleep(2)
            self.stop_audio()
            sys.exit(0)

        # Language switch checks
        if "japanese" in user_input_lower or "日本語" in user_input_lower:
            self.language = "japanese"
            self.full_transcript.append({"role": "user", "content": user_input})
            self.generate_audio("わかりました。これからは日本語でお話しします。")
            self.start_transcription()
            return

        if "english" in user_input_lower or "英語" in user_input_lower:
            self.language = "english"
            self.full_transcript.append({"role": "user", "content": user_input})
            self.generate_audio("Alright, I'll continue in English.")
            self.start_transcription()
            return

        self.full_transcript.append({"role": "user", "content": user_input})

        # Append language reminder
        if self.language == "japanese":
            self.full_transcript.append({
                "role": "system",
                "content": "From now on, reply only in Japanese using friendly tone and speech-control tags."
            })
        else:
            self.full_transcript.append({
                "role": "system",
                "content": "Continue speaking in English using friendly tone and speech-control tags."
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
            with httpx.stream("POST", "https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60.0) as response:
                full_reply = ""
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
                                full_reply += delta
                        except Exception as e:
                            print("Parsing error:", e)

                if not full_reply.strip():
                    full_reply = "I'm sorry, I didn't catch that. Could you say it again?"

                self.full_transcript.append({"role": "assistant", "content": full_reply})
                self.generate_audio(full_reply)

        except Exception as e:
            print(" OpenRouter Error:", e)
            self.generate_audio("Sorry, I had a problem understanding. Please try again.")

        time.sleep(0.5)
        self.start_transcription()

###### Step 3: ElevenLabs TTS ######

    def generate_audio(self, text):
        print(f"\n🤖 Assistant: {text}")
        try:
            audio_stream = generate(
                api_key=self.elevenlabs_api_key,
                text=text,
                voice="Alice",  # You can also use "Bella" or "Josh"
                stream=True
            )
            stream(audio_stream)
        except Exception as e:
            print("❌ TTS Error:", e)

###### Step 4: Run Assistant ######

if __name__ == "__main__":
    greeting = "<pitch level='high'>Hello!</pitch> <break> I'm your AI voice assistant. <rate level='slow'>What would you like to talk about today?</rate>"
    ai_assistant = AI_Assistant()
    ai_assistant.generate_audio(greeting)
    ai_assistant.start_transcription()
