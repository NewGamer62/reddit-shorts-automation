# Auteur : Noa Gaillard
import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

class TTSEngine:
    def __init__(self, preferred_engine="auto"):
        """
        preferred_engine: 'auto', 'edge-tts', or 'elevenlabs'
        In 'auto' mode: uses ElevenLabs if ELEVENLABS_API_KEY is present and valid,
        otherwise falls back seamlessly to edge-tts (free, no API key required).
        """
        self.preferred_engine = preferred_engine
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # ElevenLabs Voice IDs
        self.eleven_voices = {
            "M": "pNInz6obpgDQGcFmaJgB", # Adam (Standard Male)
            "F": "21m00Tcm4TlvDq8ikWAM"  # Rachel (Standard Female)
        }
        
        # Edge-TTS Free Neural Voices
        self.edge_voices = {
            "M": "en-US-ChristopherNeural",
            "F": "en-US-JennyNeural"
        }

    async def _edge_tts_convert(self, text, voice, output_path):
        import edge_tts
        import aiohttp
        import socket
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
        communicate = edge_tts.Communicate(text, voice, connector=connector)
        await communicate.save(output_path)

    def _generate_edge_tts(self, text, gender, output_path, voice=None):
        selected_voice = voice or self.edge_voices.get(str(gender).upper(), self.edge_voices["M"])
        print(f"🎤 [Edge-TTS Free] Génération avec la voix : {selected_voice} ({'Homme' if str(gender).upper() == 'M' else 'Femme'})")
        
        last_error = None
        for attempt in range(1, 4):
            try:
                try:
                    asyncio.run(self._edge_tts_convert(text, selected_voice, output_path))
                except RuntimeError:
                    # Dans le cas où une boucle asyncio existe déjà dans le thread courant
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self._edge_tts_convert(text, selected_voice, output_path))

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"✅ Audio généré avec succès : {output_path}")
                    return output_path
            except Exception as e:
                last_error = e
                if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                    try:
                        os.remove(output_path)
                    except OSError:
                        pass
                if attempt < 3:
                    print(f"⚠️ Échec temporaire Edge-TTS (tentative {attempt}/3: {e}). Nouvelle tentative dans 1s...")
                    time.sleep(1.0 * attempt)
        
        print(f"❌ Erreur Edge-TTS après 3 tentatives : {last_error}")
        raise last_error

    def _generate_elevenlabs(self, text, gender, output_path, voice_id=None):
        if not self.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY non définie.")
        
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=self.elevenlabs_api_key)
        selected_voice = voice_id or self.eleven_voices.get(str(gender).upper(), self.eleven_voices["M"])
        
        print(f"🎤 [ElevenLabs] Génération avec la voix : {'Homme' if str(gender).upper() == 'M' else 'Femme'}")
        audio_iterator = client.text_to_speech.convert(
            voice_id=selected_voice,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            optimize_streaming_latency=0
        )
        with open(output_path, "wb") as f:
            for chunk in audio_iterator:
                if chunk:
                    f.write(chunk)
        print(f"✅ Audio généré avec succès : {output_path}")
        return output_path

    def generate_audio(self, text, gender="M", output_path="voiceover.mp3", voice=None):
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Force Edge-TTS if requested or if in auto mode without ElevenLabs key configured
        if self.preferred_engine == "edge-tts" or (self.preferred_engine == "auto" and not self.elevenlabs_api_key):
            return self._generate_edge_tts(text, gender, output_path, voice=voice)
        
        # In 'auto' or 'elevenlabs' mode, attempt ElevenLabs first
        try:
            return self._generate_elevenlabs(text, gender, output_path, voice_id=voice)
        except Exception as e:
            if self.preferred_engine == "auto":
                print(f"⚠️ ElevenLabs indisponible ({e}). Bascule automatique sur Edge-TTS gratuit...")
                return self._generate_edge_tts(text, gender, output_path, voice=voice)
            raise
