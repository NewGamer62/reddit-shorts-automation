# Auteur : Noa Gaillard
import os
from playwright.sync_api import sync_playwright

class CardGenerator:
    def generate(self, topic, author="u/StoryTeller", output_path="assets/audio/reddit_card.png"):
        # Style Reddit 2026 moderne et compact
        html_content = f"""
        <html>
        <head>
            <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body {{ background: transparent; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: 'IBM Plex Sans', sans-serif; }}
                .card {{ background: #1A1A1B; color: #D7DADC; width: 750px; border: 1px solid #343536; border-radius: 8px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
                .meta {{ color: #818384; font-size: 14px; margin-bottom: 12px; font-weight: 400; }}
                .title {{ font-size: 26px; font-weight: 600; line-height: 1.3; color: #FFFFFF; }}
                .footer {{ margin-top: 15px; display: flex; gap: 15px; color: #818384; font-size: 13px; font-weight: 600; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="meta">r/AskReddit • Posted by {author}</div>
                <div class="title">{topic}</div>
                <div class="footer"><span>▲ 14.2k Upvotes</span> <span>💬 2.4k Comments</span></div>
            </div>
        </body>
        </html>
        """

        with sync_playwright() as p:
            # On lance le navigateur en mode 'headless' (invisible)
            browser = p.chromium.launch()
            # Viewport vertical pour simuler un écran de téléphone si besoin
            page = browser.new_page(viewport={'width': 1080, 'height': 1920})
            page.set_content(html_content)
            
            # Attente cruciale pour que les Google Fonts soient chargées
            page.wait_for_selector(".card")
            
            # On cible la carte et on prend un screenshot avec fond transparent
            card_element = page.locator(".card")
            card_element.screenshot(path=output_path, omit_background=True)
            
            browser.close()
        return output_path