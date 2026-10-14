# Auteur : Noa Gaillard
import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

class YouTubeUploader:
    def __init__(self, client_secrets_file):
        # Le scope qui donne l'autorisation complète d'upload
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.client_secrets_file = client_secrets_file
        self.token_file = "token.pickle"

    def authenticate(self):
        """Gère l'authentification OAuth2 et sauvegarde la session pour les futurs uploads."""
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        credentials = None
        
        # 1. On cherche si on s'est déjà connecté auparavant
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                credentials = pickle.load(token)
        
        # 2. Si on n'est pas connecté ou que le token est périmé
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                # Ouvre le navigateur (UNE SEULE FOIS) pour accepter
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes)
                credentials = flow.run_local_server(port=0)
            
            # On sauvegarde le précieux sésame pour les prochaines exécutions
            with open(self.token_file, "wb") as token:
                pickle.dump(credentials, token)
                
        return credentials

    def upload(self, video_path, metadata):
        """Upload la vidéo avec le titre, la description et les tags SEO."""
        credentials = self.authenticate()
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
        
        request_body = {
            "snippet": {
                "categoryId": "24", # 24 = Entertainment / Divertissement
                "title": metadata["title"],
                "description": metadata["description"],
                "tags": metadata["tags"]
            },
            "status": {
                "privacyStatus": "public", # Met "private" si tu veux vérifier le résultat avant publication
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Le paramètre resumable=True permet de reprendre l'upload en cas de coupure internet
        media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )
        
        print(f"🚀 Upload vers YouTube en cours pour : '{metadata['title']}'...")
        response = request.execute()
        print(f"✅ Vidéo en ligne ! Lien : https://youtu.be/{response.get('id')}")
        return response