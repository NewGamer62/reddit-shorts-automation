# Auteur : Noa Gaillard
import requests
import re
import html

class ScriptGenerator:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0"}
        self.BLACKLIST = [
            "trump", "biden", "kamala", "election", "democrat", "republican", 
            "doj", "prince andrew", "epstein", "politics", "war", "israel", 
            "palestine", "ukraine", "russia", "murder", "suicide", "rape", 
            "assault", "pedophile", "nazi", "sex", "porn", "nsfw", "dick", 
            "pussy", "fuck", "masturbate", "stripper", "onlyfans", "incest", 
            "slut", "whore", "hooker"
        ]

    def is_safe(self, text):
        text_lower = text.lower()
        return not any(bad_word in text_lower for bad_word in self.BLACKLIST)

    def clean_text(self, text):
        if not text: 
            return ""
        text = html.unescape(text)
        text = re.sub(r'(?i)\n?Edit:.*', '', text, flags=re.DOTALL)
        text = re.sub(r'(?i)\n?Update:.*', '', text, flags=re.DOTALL)
        text = re.sub(r'http\S+', '', text)
        return text.strip()

    def get_top_comments_for_monetization(self, post_id):
        url = f"https://www.reddit.com/comments/{post_id}.json?sort=top"
        try:
            resp = requests.get(url, headers=self.headers)
            comments = resp.json()[1]["data"]["children"]
            
            combined_text = ""
            for comment in comments:
                body = comment["data"].get("body", "")
                if body and body not in ["[deleted]", "[removed]"]:
                    combined_text += body + " \n\n "
                
                if len(combined_text) >= 900:
                    break
                    
            return combined_text
        except:
            return ""

    def generate(self, target_subreddit):
        print(f"Connexion a r/{target_subreddit}...")
        url = f"https://www.reddit.com/r/{target_subreddit}/top.json?t=day&limit=30"

        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200: 
                return None

            posts = response.json()["data"]["children"]
            selected_post = None
            story_text = ""

            for post_data in posts:
                post = post_data["data"]
                
                if not self.is_safe(post["title"]): 
                    continue

                if target_subreddit.lower() == "askreddit":
                    if not post["stickied"]:
                        comments_text = self.get_top_comments_for_monetization(post["id"])
                        if len(comments_text) > 700 and self.is_safe(comments_text):
                            selected_post = post
                            story_text = f"{post['title']}. \n\n {comments_text}"
                            break
                
                else:
                    text_len = len(post.get("selftext", ""))
                    if not post["stickied"] and 800 < text_len < 2000:
                        if self.is_safe(post["selftext"]):
                            selected_post = post
                            story_text = post["selftext"]
                            break
            
            if not selected_post: 
                print(f"Aucun post valide trouve sur r/{target_subreddit}.")
                return None

            clean_story = self.clean_text(story_text)
            
            if len(clean_story) > 1300:
                last_dot = clean_story[:1300].rfind('.')
                if last_dot != -1: 
                    clean_story = clean_story[:last_dot+1]
                else:
                    clean_story = clean_story[:1300]

            return {
                "title": selected_post["title"],
                "text": clean_story,
                "gender": "M",
                "author": f"u/{selected_post['author']}",
                "subreddit": f"r/{target_subreddit}"
            }

        except Exception as e:
            print(f"Erreur ScriptGen: {e}")
            return None