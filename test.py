from pydub import AudioSegment
from pydub.utils import which
from edge_tts import Communicate
import asyncio
import tempfile
import simpleaudio as sa
import os

AudioSegment.converter = which("ffmpeg")  # Optional if already set in system

def test_audio_playback():
    print("🔊 Testing audio...")
    text = "This is a test of the voice system."

    async def test():
        communicate = Communicate(text=text, voice="en-US-JennyNeural")
        async for chunk in communicate.stream():
            if "audio" in chunk:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_tmp:
                    mp3_path = mp3_tmp.name
                    mp3_tmp.write(chunk["audio"])
                    mp3_tmp.flush()
                    print(f"💾 MP3 saved at: {mp3_path}")

                    try:
                        audio = AudioSegment.from_file(mp3_path, format="mp3")
                        wav_path = mp3_path.replace(".mp3", ".wav")
                        audio.export(wav_path, format="wav")
                        print(f"🎧 WAV exported at: {wav_path}")

                        wave_obj = sa.WaveObject.from_wave_file(wav_path)
                        play_obj = wave_obj.play()
                        print("🔊 Playing audio...")
                        play_obj.wait_done()
                        print("✅ Playback complete.")
                    except Exception as e:
                        print("❌ Error during playback:", e)

    asyncio.run(test())

# Run this
if __name__ == "__main__":
    test_audio_playback()
