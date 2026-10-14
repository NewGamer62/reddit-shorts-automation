# Auteur : Noa Gaillard
import os
import time
from dotenv import load_dotenv

from script_gen import ScriptGenerator
from tts_engine import TTSEngine
from card_gen_pro import CardGenerator
from video_engine import VideoEngine
from metadata_gen import MetadataGenerator
from discord_sender import DiscordSender
from youtube_uploader import YouTubeUploader

load_dotenv()

def run_batch_pipeline():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    output_dir = os.path.join(project_root, "output")
    assets_dir = os.path.join(project_root, "assets")
    gameplay_dir = os.path.join(assets_dir, "gameplay")
    music_dir = os.path.join(assets_dir, "music")
    fonts_dir = os.path.join(assets_dir, "fonts")
    audio_temp_dir = os.path.join(assets_dir, "audio")
    client_secrets = os.path.join(project_root, "client_secrets.json")

    font_path_subtitles = os.path.join(fonts_dir, "Komika Axis.ttf")

    for folder in [output_dir, audio_temp_dir]:
        os.makedirs(folder, exist_ok=True)

    subreddits_config = [
        {"name": "AITAH", "music": "drama.mp3"},
        {"name": "AskReddit", "music": "lofi.mp3"},
        {"name": "TrueOffMyChest", "music": "confession.mp3"}
    ]

    gen = ScriptGenerator()
    tts = TTSEngine()
    card_gen = CardGenerator()
    meta_gen = MetadataGenerator()
    discord_bot = DiscordSender()
    yt_uploader = YouTubeUploader(client_secrets)

    for sub_config in subreddits_config:
        sub_name = sub_config["name"]
        music_file = sub_config["music"]
        
        data = gen.generate(sub_name)
        if not data:
            continue
            
        text = data.get("text")
        gender = data.get("gender", "M")
        card_title = data.get("title")
        card_author = data.get("author")
        
        audio_path = os.path.join(audio_temp_dir, f"voiceover_{sub_name}.mp3")
        card_path = os.path.join(audio_temp_dir, f"reddit_card_{sub_name}.png")
        final_video_path = os.path.join(output_dir, f"final_video_{sub_name}.mp4")
        metadata_path = os.path.join(output_dir, f"metadata_{sub_name}.json")
        specific_music_path = os.path.join(music_dir, music_file)

        if not os.path.exists(specific_music_path):
            continue

        try:
            tts.generate_audio(text, gender, audio_path)
            card_gen.generate(card_title, author=card_author, output_path=card_path)
            
            video = VideoEngine(gameplay_dir, music_dir, font_path_subtitles)
            video.music_files = [specific_music_path]
            video.assemble(audio_path, card_path, final_video_path)
            
            metadata = meta_gen.generate(card_title, sub_name, metadata_path)
            
            youtube_url = None
            if os.path.exists(client_secrets):
                response = yt_uploader.upload(final_video_path, metadata)
                if response and 'id' in response:
                    youtube_url = f"https://youtube.com/shorts/{response['id']}"
            
            if youtube_url:
                discord_bot.send_notification(youtube_url, metadata)
            else:
                print(f"Upload YouTube echoue pour r/{sub_name}, pas d'envoi Discord.")
            
        except Exception as e:
            print(f"Erreur d'execution sur r/{sub_name} : {e}")

if __name__ == "__main__":
    run_batch_pipeline()