# Auteur : Noa Gaillard
import json
import os

class MetadataGenerator:
    def __init__(self):
        self.tags_map = {
            "AITAH": ["reddit", "redditstories", "aita", "storytime", "drama", "redditreadings"],
            "AskReddit": ["askreddit", "reddit", "redditstories", "storytime", "viral", "facts"],
            "TrueOffMyChest": ["trueoffmychest", "confession", "reddit", "storytime", "drama", "secret"]
        }

    def generate(self, title, subreddit, output_path):
        sub_clean = subreddit.replace("r/", "")
        base_tags = self.tags_map.get(sub_clean, ["reddit", "storytime", "viral"])
        
        seo_title = f"{title[:80]} #shorts"
        
        description_lines = [
            title,
            "",
            "What do you think? Let me know in the comments!",
            "",
            "Subscribe for daily Reddit stories!",
            "",
            " ".join([f"#{t}" for t in base_tags])
        ]
        
        metadata = {
            "title": seo_title,
            "description": "\n".join(description_lines),
            "tags": base_tags
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
            
        return metadata