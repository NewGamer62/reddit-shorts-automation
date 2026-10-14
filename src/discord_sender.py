# Auteur : Noa Gaillard
import os
import requests

class DiscordSender:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    def send_notification(self, youtube_url, metadata):
        if not self.webhook_url:
            return

        content = (
            f"<@627354816129138699>\n"
            f"Video publiee sur YouTube.\n"
            f"Lien : {youtube_url}\n\n"
            f"Description :\n```text\n{metadata.get('description')}\n```"
        )

        data = {'content': content}

        try:
            requests.post(self.webhook_url, data=data)
        except Exception as e:
            print(f"Erreur Discord : {e}")