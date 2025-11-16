import requests
from django.core.management.base import BaseCommand
from main.models import Game

class Command(BaseCommand):
    help = "Fast update: fetch 1000 popular Steam games WITHOUT Steam Store API slow calls."

    def handle(self, *args, **options):
        self.stdout.write("🟢 FAST FETCH: SteamSpy lists...")

        endpoints = [
            "top100in2weeks",
            "top100owned",
            "top100forever",
            "all",
        ]

        all_games = {}

        # Fetch 4 lists (very fast)
        for endpoint in endpoints:
            url = f"https://steamspy.com/api.php?request={endpoint}"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    all_games.update(data)
                    self.stdout.write(f"✅ {endpoint}: {len(data)} games")
                else:
                    self.stdout.write(f"⚠️ Error {r.status_code} loading {endpoint}")
            except Exception as e:
                self.stdout.write(f"⚠️ Failed {endpoint}: {e}")

        self.stdout.write(f"🧩 Total unique SteamSpy games: {len(all_games)}")

        # Clear old DB
        Game.objects.all().delete()
        self.stdout.write("🧹 Old games removed.")

        saved = 0
        skipped = 0

        # Loop games (no API calls → super fast)
        for g in list(all_games.values())[:1200]:
            appid = g.get("appid")
            name = g.get("name", "").strip()

            if not appid or not name:
                skipped += 1
                continue

            # Primary tall library cover
            cover = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900_2x.jpg"

            # Always-available fallback (the header)
            fallback_cover = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"

            Game.objects.update_or_create(
                appid=appid,
                defaults={
                    "name": name,
                    "genre": g.get("genre", "Unknown"),
                    "image": cover,
                    "fallback_image": fallback_cover,
                }
            )

            saved += 1
            if saved % 100 == 0:
                self.stdout.write(f"💾 Saved {saved} games...")

            if saved >= 1000:
                break

        self.stdout.write(self.style.SUCCESS(f"✅ FAST UPDATE COMPLETE — {saved} games saved."))
        self.stdout.write(self.style.WARNING(f"🚫 Skipped: {skipped} invalid items."))
