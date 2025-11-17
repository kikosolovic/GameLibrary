from django.core.management.base import BaseCommand
from main.models import Game
from main.views import fetch_steamstore
import requests

class Command(BaseCommand):
    help = "Fix only broken Steam images by testing the URL before replacing"

    def image_is_broken(self, url):
        """
        Returns True if image does NOT load (403, 404, 0 bytes, or errors)
        """
        if not url:
            return True

        try:
            r = requests.get(url, timeout=4, stream=True)

            # A valid image MUST return OK + have content
            if r.status_code != 200:
                return True

            # Steam broken images often return less than ~1000 bytes
            size = int(r.headers.get("Content-Length", "0"))
            if size < 5000:
                return True

            return False

        except:
            return True

    def handle(self, *args, **kwargs):
        games = Game.objects.all()
        fixed = 0
        skipped = 0

        for g in games:
            url = g.image

            # Skip if image is OK
            if not self.image_is_broken(url):
                skipped += 1
                continue

            # Fetch fresh data from Steam Store
            store = fetch_steamstore(g.appid)
            if not store:
                continue

            new_img = store.get("header_image")
            if new_img:
                g.image = new_img
                g.save()
                fixed += 1
                self.stdout.write(f"✔ Updated: {g.name}")
            else:
                self.stdout.write(f"✖ No header_image for {g.name}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Fixed: {fixed}, Skipped OK: {skipped}"
        ))
