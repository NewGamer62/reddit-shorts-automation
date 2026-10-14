# Auteur : Noa Gaillard
import os
import random
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, TextClip
from moviepy.video.fx.all import resize, crop
from moviepy.config import change_settings

# VÉRIFIE BIEN TON CHEMIN IMAGEMAGICK ICI
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

class VideoEngine:
    def __init__(self, gameplay_folder, music_folder, font_path):
        self.gameplay_files = [os.path.join(gameplay_folder, f) for f in os.listdir(gameplay_folder) if f.endswith('.mp4')]
        self.music_files = [os.path.join(music_folder, f) for f in os.listdir(music_folder) if f.endswith('.mp3')]
        self.font_path = font_path
        print("⏳ Chargement Whisper...")
        self.model = whisper.load_model("base")

    def assemble(self, audio_path, card_path, output_path):
        voice = AudioFileClip(audio_path)
        duration = voice.duration
        
        # 1. AUDIO
        if self.music_files:
            music = AudioFileClip(random.choice(self.music_files)).volumex(0.1)
            music = music.loop(duration=duration) if music.duration < duration else music.subclip(0, duration)
            final_audio = CompositeAudioClip([voice, music])
        else:
            final_audio = voice

        # 2. GAMEPLAY (Correction du Zoom)
        bg_path = random.choice(self.gameplay_files)
        background = VideoFileClip(bg_path).without_audio()
        
        if background.duration > duration:
            start_t = random.uniform(0, background.duration - duration)
            background = background.subclip(start_t, start_t + duration)
            
        # On redimensionne intelligemment : on remplit la largeur OU la hauteur
        background = background.resize(width=1080)
        if background.h < 1920:
            background = background.resize(height=1920)
        
        # Crop central propre
        background = crop(background, width=1080, height=1920, x_center=background.w/2, y_center=background.h/2)

        # 3. REDDIT CARD
        card = ImageClip(card_path).set_duration(3).resize(width=900).set_position(('center', 450))

        # 4. SOUS-TITRES (Version simplifiée et robuste)
        print("📝 Transcription Whisper...")
        result = self.model.transcribe(audio_path, word_timestamps=True)
        subtitle_clips = []
        
        for segment in result['segments']:
            for word in segment['words']:
                w_text = word['word'].strip().upper()
                start = word['start']
                end = word['end']
                
                # Un seul clip avec un stroke modéré pour éviter les bugs de rendu
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
        print(f"🎬 Rendu final ({int(duration)}s)...")
        final = CompositeVideoClip([background, card] + subtitle_clips, size=(1080, 1920))
        final.audio = final_audio
        final.write_videofile(
            output_path, 
            fps=60, 
            codec='libx264', 
            audio_codec='aac', 
            bitrate="8000k", 
            preset='fast', 
            threads=4
        )