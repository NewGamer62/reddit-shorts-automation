# Auteur : Noa Gaillard
import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

class TTSEngine:
    def __init__(self):
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        
        # Dictionnaire des voix (ID officiels ElevenLabs)
        self.voices = {
            "M": "pNInz6obpgDQGcFmaJgB", # Adam (Voix homme standard)
            "F": "21m00Tcm4TlvDq8ikWAM"  # Rachel (Voix femme standard)
        }

    def generate_audio(self, text, gender, output_path):
        # Sélection de l'ID, par défaut "Adam" si inconnu
        voice_id = self.voices.get(gender, self.voices["M"])
        
        print(f"🎤 Génération avec la voix : {'Homme' if gender == 'M' else 'Femme'}")

        audio_iterator = self.client.text_to_speech.convert(
            voice_id=voice_id,
            output_format="mp3_44100_128",
            text=text,
            model_id="eleven_multilingual_v2",
            optimize_streaming_latency=0
        )
        
        with open(output_path, "wb") as f:
            for chunk in audio_iterator:
                if chunk:
                    f.write(chunk)