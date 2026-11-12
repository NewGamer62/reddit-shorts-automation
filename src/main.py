# Auteur : Noa Gaillard
import os
import sys
import glob
import time
import argparse
from dotenv import load_dotenv
from PIL import Image

# MoviePy 1.0.3 compatibility shim for Pillow 10+ (restores removed Image.ANTIALIAS)
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = getattr(Image, "Resampling", Image).LANCZOS

from script_gen import ScriptGenerator
from tts_engine import TTSEngine
from card_gen_pro import CardGenerator
from video_engine import VideoEngine
from metadata_gen import MetadataGenerator
from discord_sender import DiscordSender
from youtube_uploader import YouTubeUploader

load_dotenv()

# Histoires locales de secours pour exécution hors-ligne ou contournement Reddit 403
SAMPLE_STORIES = {
    "AskReddit": {
        "title": "What's a fact that sounds completely fake but is actually 100% true?",
        "text": "Take out and delivery now account for 75 percent of all restaurant orders worldwide. In 2019 it was less than 20 percent.",
        "gender": "M",
        "author": "u/CuriousMind",
        "subreddit": "r/AskReddit",
        "music": "lofi.mp3"
    },
    "AITAH": {
        "title": "AITAH for keeping everything my Grandfather left me?",
        "text": "My grandfather recently passed away and left me his entire workshop and vintage car collection. My family is furious because they wanted to sell it all.",
        "gender": "M",
        "author": "u/HeritageKeeper",
        "subreddit": "r/AITAH",
        "music": "drama.mp3"
    },
    "TrueOffMyChest": {
        "title": "I finally stood up for myself at work today",
        "text": "After three years of taking on extra shifts without credit, I finally had an honest conversation with my manager and set clear boundaries.",
        "gender": "M",
        "author": "u/SilentWorker",
        "subreddit": "r/TrueOffMyChest",
        "music": "confession.mp3"
    }
}

SUBREDDIT_MUSIC = {
    "AITAH": "drama.mp3",
    "AskReddit": "lofi.mp3",
    "TrueOffMyChest": "confession.mp3"
}

def process_single_video(
    project_root,
    sub_name="AskReddit",
    title=None,
    text=None,
    author="u/StoryTeller",
    input_audio_path=None,
    tts_engine_name="auto",
    voice_name=None,
    gender="M",
    music_file=None,
    do_upload=False,
    output_dir=None,
    fps=30
):
    """Génère un Short complet de bout en bout."""
    assets_dir = os.path.join(project_root, "assets")
    gameplay_dir = os.path.join(assets_dir, "gameplay")
    music_dir = os.path.join(assets_dir, "music")
    fonts_dir = os.path.join(assets_dir, "fonts")
    audio_temp_dir = os.path.join(assets_dir, "audio")
    client_secrets = os.path.join(project_root, "client_secrets.json")

    if not output_dir:
        output_dir = os.path.join(project_root, "output")

    for folder in [output_dir, audio_temp_dir]:
        os.makedirs(folder, exist_ok=True)

    # Résolution défensive de la police
    font_path_subtitles = os.path.join(fonts_dir, "LEMONMILK-Bold.otf")
    if not os.path.exists(font_path_subtitles):
        alt_font = os.path.join(fonts_dir, "Komika Axis.ttf")
        if os.path.exists(alt_font):
            font_path_subtitles = alt_font

    final_video_path = os.path.join(output_dir, f"final_video_{sub_name}.mp4")
    metadata_path = os.path.join(output_dir, f"metadata_{sub_name}.json")
    card_path = os.path.join(audio_temp_dir, f"reddit_card_{sub_name}.png")

    # 1. Gestion de la source Audio (Injection directe ou synthèse TTS)
    if input_audio_path:
        if not os.path.exists(input_audio_path):
            raise FileNotFoundError(f"Fichier audio introuvable : {input_audio_path}")
        audio_path = input_audio_path
        print(f"🎵 [Direct Audio] Utilisation du fichier audio direct : {audio_path}")
    else:
        if not text:
            raise ValueError("Texte requis pour la synthèse TTS lorsque aucun audio n'est fourni.")
        audio_path = os.path.join(audio_temp_dir, f"voiceover_{sub_name}.mp3")
        tts = TTSEngine(preferred_engine=tts_engine_name)
        try:
            tts.generate_audio(text, gender=gender, output_path=audio_path, voice=voice_name)
        except Exception as e:
            print(f"⚠️ Échec TTS ({e}). Recherche d'un audio pré-enregistré de secours...")
            candidates = [
                os.path.join(audio_temp_dir, f"voiceover_{sub_name}.mp3"),
                os.path.join(audio_temp_dir, "voiceover_todayilearned.mp3"),
                os.path.join(audio_temp_dir, "voiceover_AskReddit.mp3"),
            ] + glob.glob(os.path.join(audio_temp_dir, "voiceover_*.mp3"))
            
            fallback_found = False
            for cand in candidates:
                if os.path.exists(cand) and os.path.getsize(cand) > 1000:
                    audio_path = cand
                    fallback_found = True
                    print(f"ℹ️ Audio de secours utilisé : {audio_path}")
                    break
            if not fallback_found:
                raise

    # 2. Génération de la Reddit Card
    card_title = title or f"Top story from r/{sub_name}"
    card_gen = CardGenerator()
    try:
        card_gen.generate(card_title, author=author, output_path=card_path)
    except Exception as e:
        print(f"⚠️ Erreur CardGenerator ({e}). Recherche d'une carte pré-rendue...")
        premade = os.path.join(audio_temp_dir, f"reddit_card_{sub_name}.png")
        if os.path.exists(premade):
            card_path = premade
            print(f"ℹ️ Carte pré-rendue utilisée : {card_path}")
        else:
            cards = glob.glob(os.path.join(audio_temp_dir, "reddit_card_*.png"))
            if cards:
                card_path = cards[0]
                print(f"ℹ️ Carte alternative utilisée : {card_path}")
            else:
                raise

    # 3. Assemblage Vidéo
    video = VideoEngine(gameplay_dir, music_dir, font_path_subtitles)
    
    # Résolution de la piste musicale
    selected_music = music_file or SUBREDDIT_MUSIC.get(sub_name, "lofi.mp3")
    music_path = os.path.join(music_dir, selected_music)
    if os.path.exists(music_path):
        video.music_files = [music_path]
    elif video.music_files:
        video.music_files = [video.music_files[0]]
    else:
        video.music_files = []

    video.assemble(audio_path, card_path, final_video_path, fps=fps)

    # 4. Génération des Métadonnées SEO
    meta_gen = MetadataGenerator()
    metadata = meta_gen.generate(card_title, sub_name, metadata_path)

    # 5. Upload YouTube et Alerte Discord (conditionnels et sécurisés)
    if do_upload:
        if os.path.exists(client_secrets):
            print("🚀 Début de la procédure d'upload YouTube...")
            yt_uploader = YouTubeUploader(client_secrets)
            response = yt_uploader.upload(final_video_path, metadata)
            if response and 'id' in response:
                youtube_url = f"https://youtube.com/shorts/{response['id']}"
                discord_bot = DiscordSender()
                discord_bot.send_notification(youtube_url, metadata)
            else:
                print(f"Upload YouTube échoué pour r/{sub_name}, pas d'envoi Discord.")
        else:
            print(f"⚠️ client_secrets.json introuvable ({client_secrets}). Upload ignoré.")
    else:
        print("ℹ️ Mode local / sans upload : Publication YouTube et Discord ignorées (activer avec --upload).")

    print(f"🎉 Pipeline terminé avec succès pour r/{sub_name} -> {final_video_path}")
    return final_video_path

def run_batch_pipeline(project_root, tts_engine="auto", do_upload=False, output_dir=None, fps=30):
    """Exécute le pipeline en mode batch sur les subreddits configurés."""
    subreddits_config = [
        {"name": "AskReddit", "music": "lofi.mp3"},
        {"name": "AITAH", "music": "drama.mp3"},
        {"name": "TrueOffMyChest", "music": "confession.mp3"}
    ]

    gen = ScriptGenerator()

    for sub_config in subreddits_config:
        sub_name = sub_config["name"]
        music_file = sub_config["music"]

        # Tentative de scraping Reddit avec repli automatique sur histoires locales
        data = gen.generate(sub_name)
        if not data:
            print(f"⚠️ Scraping Reddit indisponible pour r/{sub_name} (HTTP 403 / hors-ligne). Bascule sur l'histoire locale de secours...")
            data = SAMPLE_STORIES.get(sub_name)
            if not data:
                print(f"Aucune donnée pour r/{sub_name}, passage au suivant.")
                continue

        text = data.get("text")
        gender = data.get("gender", "M")
        card_title = data.get("title")
        card_author = data.get("author", "u/StoryTeller")

        try:
            process_single_video(
                project_root=project_root,
                sub_name=sub_name,
                title=card_title,
                text=text,
                author=card_author,
                tts_engine_name=tts_engine,
                gender=gender,
                music_file=music_file,
                do_upload=do_upload,
                output_dir=output_dir,
                fps=fps
            )
        except Exception as e:
            print(f"❌ Erreur d'exécution sur r/{sub_name} : {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Zero-Friction Reddit Shorts Automation Pipeline"
    )
    parser.add_argument(
        "--local", "--test",
        dest="local",
        action="store_true",
        help="Run in zero-secret local test mode with Edge-TTS and offline sample story"
    )
    parser.add_argument(
        "--audio",
        dest="audio",
        type=str,
        default=None,
        help="Path to pre-existing audio file (bypasses Reddit scraping and TTS)"
    )
    parser.add_argument(
        "--text",
        dest="text",
        type=str,
        default=None,
        help="Custom story text (bypasses Reddit scraping)"
    )
    parser.add_argument(
        "--title",
        dest="title",
        type=str,
        default=None,
        help="Custom title for the Reddit card"
    )
    parser.add_argument(
        "--subreddit",
        dest="subreddit",
        type=str,
        default=None,
        help="Target subreddit (e.g. AskReddit, AITAH, TrueOffMyChest)"
    )
    parser.add_argument(
        "--tts-engine", "--tts",
        dest="tts_engine",
        choices=["auto", "edge-tts", "elevenlabs"],
        default=None,
        help="TTS engine to use (default: 'auto', or 'edge-tts' in --local mode)"
    )
    parser.add_argument(
        "--voice",
        dest="voice",
        type=str,
        default=None,
        help="Voice override for TTS engine"
    )
    parser.add_argument(
        "--upload",
        dest="upload",
        action="store_true",
        default=False,
        help="Enable YouTube upload and Discord notification (requires client_secrets.json)"
    )
    parser.add_argument(
        "--output",
        dest="output",
        type=str,
        default=None,
        help="Output directory for generated videos and metadata"
    )
    parser.add_argument(
        "--fps",
        dest="fps",
        type=int,
        default=30,
        help="Video framerate (default: 30 fps)"
    )

    args = parser.parse_args()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    # 1. Cas : Injection directe d'un fichier audio
    if args.audio:
        sub_name = args.subreddit.replace("r/", "") if args.subreddit else "AskReddit"
        derived_title = args.title or os.path.splitext(os.path.basename(args.audio))[0].replace("_", " ").title()
        
        process_single_video(
            project_root=project_root,
            sub_name=sub_name,
            title=derived_title,
            input_audio_path=args.audio,
            do_upload=args.upload,
            output_dir=args.output,
            fps=args.fps
        )
        return

    # 2. Cas : Mode local ou arguments ciblés (--local, --text, ou --subreddit sans batch)
    if args.local or args.text or args.subreddit:
        sub_name = args.subreddit.replace("r/", "") if args.subreddit else "AskReddit"
        engine = args.tts_engine or ("edge-tts" if args.local else "auto")
        
        # Données de l'histoire
        if args.text:
            story_text = args.text
            story_title = args.title or SAMPLE_STORIES.get(sub_name, {}).get("title", f"Story from r/{sub_name}")
            story_author = "u/StoryTeller"
            story_gender = "M"
        else:
            sample = SAMPLE_STORIES.get(sub_name, SAMPLE_STORIES["AskReddit"])
            story_title = args.title or sample["title"]
            story_text = sample["text"]
            story_author = sample["author"]
            story_gender = sample.get("gender", "M")

        process_single_video(
            project_root=project_root,
            sub_name=sub_name,
            title=story_title,
            text=story_text,
            author=story_author,
            tts_engine_name=engine,
            voice_name=args.voice,
            gender=story_gender,
            music_file=SUBREDDIT_MUSIC.get(sub_name, "lofi.mp3"),
            do_upload=args.upload,
            output_dir=args.output,
            fps=args.fps
        )
        return

    # 3. Cas par défaut : Exécution du batch complet
    engine = args.tts_engine or "auto"
    run_batch_pipeline(
        project_root=project_root,
        tts_engine=engine,
        do_upload=args.upload,
        output_dir=args.output,
        fps=args.fps
    )

if __name__ == "__main__":
    main()
