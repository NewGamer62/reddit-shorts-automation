# Auteur : Noa Gaillard
import os
import time
import glob
import shutil
import random
from PIL import Image

# MoviePy 1.0.3 compatibility shim for Pillow 10+ (restores removed Image.ANTIALIAS)
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = getattr(Image, "Resampling", Image).LANCZOS

import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, TextClip, ColorClip
from moviepy.video.fx.all import resize, crop
from moviepy.config import change_settings

def configure_imagemagick():
    """Détecte et configure dynamiquement le binaire ImageMagick."""
    # 1. Variable d'environnement personnalisée
    custom_path = os.getenv("IMAGEMAGICK_BINARY")
    if custom_path and os.path.exists(custom_path):
        change_settings({"IMAGEMAGICK_BINARY": custom_path})
        return custom_path
    
    # 2. Détection via PATH
    which_magick = shutil.which("magick") or shutil.which("convert")
    if which_magick and os.path.exists(which_magick):
        change_settings({"IMAGEMAGICK_BINARY": which_magick})
        return which_magick
        
    # 3. Répertoires standards Windows et chemin par défaut
    win_default = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
    if os.path.exists(win_default):
        change_settings({"IMAGEMAGICK_BINARY": win_default})
        return win_default

    candidates = glob.glob(r"C:\Program Files\ImageMagick*\magick.exe")
    candidates += glob.glob(r"C:\Program Files (x86)\ImageMagick*\magick.exe")
    for cand in candidates:
        if os.path.exists(cand):
            change_settings({"IMAGEMAGICK_BINARY": cand})
            return cand

    # 4. Chemins standards Unix / macOS
    unix_paths = ["/usr/bin/magick", "/usr/local/bin/magick", "/opt/homebrew/bin/magick"]
    for up in unix_paths:
        if os.path.exists(up):
            change_settings({"IMAGEMAGICK_BINARY": up})
            return up

    return None

configure_imagemagick()

class VideoEngine:
    def __init__(self, gameplay_folder, music_folder, font_path):
        self.gameplay_files = []
        if gameplay_folder and os.path.exists(gameplay_folder):
            self.gameplay_files = [os.path.join(gameplay_folder, f) for f in os.listdir(gameplay_folder) if f.endswith('.mp4')]
        
        self.music_files = []
        if music_folder and os.path.exists(music_folder):
            self.music_files = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith('.mp3')]
        
        # Vérification défensive de la police
        self.font_path = font_path
        if not self.font_path or not os.path.exists(self.font_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fallback_font = os.path.join(base_dir, "assets", "fonts", "LEMONMILK-Bold.otf")
            if os.path.exists(fallback_font):
                self.font_path = fallback_font
            elif self.font_path and os.path.exists(os.path.join(os.path.dirname(self.font_path), "LEMONMILK-Bold.otf")):
                self.font_path = os.path.join(os.path.dirname(self.font_path), "LEMONMILK-Bold.otf")

        print("⏳ Chargement Whisper...")
        self.model = whisper.load_model("base")

    def assemble(self, audio_path, card_path, output_path, fps=30):
        out_dir = os.path.dirname(os.path.abspath(output_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        voice = AudioFileClip(audio_path)
        duration = voice.duration
        
        # 1. AUDIO MIXING
        music_clip = None
        if self.music_files and os.path.exists(self.music_files[0]):
            music_clip = AudioFileClip(random.choice(self.music_files)).volumex(0.1)
            music_clip = music_clip.loop(duration=duration) if music_clip.duration < duration else music_clip.subclip(0, duration)
            final_audio = CompositeAudioClip([voice, music_clip])
        else:
            final_audio = voice

        # 2. GAMEPLAY BACKGROUND (avec fallback robuste)
        if self.gameplay_files:
            bg_path = random.choice(self.gameplay_files)
            background = VideoFileClip(bg_path).without_audio()
            if background.duration > duration:
                start_t = random.uniform(0, background.duration - duration)
                background = background.subclip(start_t, start_t + duration)
            background = background.resize(width=1080)
            if background.h < 1920:
                background = background.resize(height=1920)
            background = crop(background, width=1080, height=1920, x_center=background.w/2, y_center=background.h/2)
        else:
            print("⚠️ Aucun fichier gameplay MP4 trouvé. Génération d'un fond de synthèse sombre (1080x1920)...")
            background = ColorClip(size=(1080, 1920), color=(18, 22, 30), duration=duration)

        # 3. REDDIT CARD
        card_duration = min(3.0, duration) if duration > 0 else 3.0
        card = ImageClip(card_path).set_duration(card_duration).resize(width=900).set_position(('center', 450))

        # 4. SOUS-TITRES SYNCHRONISÉS (Whisper)
        print("📝 Transcription Whisper et calcul des sous-titres mot-à-mot...")
        result = self.model.transcribe(audio_path, word_timestamps=True)
        subtitle_clips = []
        
        for segment in result.get('segments', []):
            for word in segment.get('words', []):
                w_text = word['word'].strip().upper()
                start = word['start']
                end = word['end']
                
                if not w_text or end <= start:
                    continue

                t_clip = TextClip(
                    w_text,
                    fontsize=100,
                    font=self.font_path,
                    color='yellow',
                    stroke_color='black',
                    stroke_width=5,
                    method='caption',
                    size=(1000, None)
                ).set_start(start).set_end(end).set_position('center')
                
                subtitle_clips.append(t_clip)

        # 5. ASSEMBLAGE FINAL
        print(f"🎬 Rendu final ({int(duration)}s à {fps} FPS)...")
        final = CompositeVideoClip([background, card] + subtitle_clips, size=(1080, 1920))
        final.audio = final_audio
        
        # Gestion défensive de l'audio temporaire sur Windows pour éviter WinError 32
        temp_audio_file = os.path.join(out_dir, f"temp_audio_{os.path.basename(output_path)}.m4a")
        
        final.write_videofile(
            output_path, 
            fps=fps, 
            codec='libx264', 
            audio_codec='aac', 
            bitrate="8000k", 
            preset='fast', 
            threads=4,
            temp_audiofile=temp_audio_file,
            remove_temp=False
        )

        # Nettoyage systématique des ressources MoviePy
        final.close()
        voice.close()
        if music_clip:
            music_clip.close()
        if hasattr(background, 'close'):
            background.close()
        if hasattr(card, 'close'):
            card.close()
        for sub in subtitle_clips:
            if hasattr(sub, 'close'):
                sub.close()

        # Suppression différée sécurisée du fichier temporaire sur Windows
        if os.path.exists(temp_audio_file):
            for _ in range(5):
                try:
                    os.remove(temp_audio_file)
                    break
                except OSError:
                    time.sleep(0.2)

        print(f"✅ Vidéo générée avec succès : {output_path}")
        return output_path
