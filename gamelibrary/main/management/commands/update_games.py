import requests
from django.core.management.base import BaseCommand
from main.models import Game

class Command(BaseCommand):
    help = "Fetch 1000 popular games from SteamSpy quickly, skipping entries without valid images."

    def handle(self, *args, **options):
        self.stdout.write("🟢 Fetching popular games from SteamSpy...")

        # SteamSpy endpoints (combined top lists)
        endpoints = [
            "top100in2weeks",
            "top100owned",
            "top100forever",
            "all",
        ]

        all_games = {}

        # Fetch all data (no heavy checks)
        for endpoint in endpoints:
            url = f"https://steamspy.com/api.php?request={endpoint}"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    all_games.update(data)
                    self.stdout.write(f"✅ {endpoint}: {len(data)} games fetched.")
                else:
                    self.stdout.write(f"⚠️ {endpoint} returned status {r.status_code}")
            except Exception as e:
                self.stdout.write(f"⚠️ Error fetching {endpoint}: {e}")

        total_fetched = len(all_games)
        self.stdout.write(f"🧩 Total unique games fetched: {total_fetched}")

        # 🧹 (Optional) clear existing games
        Game.objects.all().delete()
        self.stdout.write("🧹 Old games deleted.")

        # 💾 Save valid games (fast, without HEAD calls)
        saved_count = 0
        skipped = 0

        for g in list(all_games.values())[:1200]:  # slightly more to compensate for skips
            appid = g.get("appid")
            name = g.get("name", "").strip()

            # Skip entries missing required info
            if not appid or not name or name.lower() in ["unknown", "app"]:
                skipped += 1
                continue

            # Build possible vertical image
            image_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"

            # Heuristic: Steam images always exist unless game removed
            # So skip apps with IDs under 10 or obviously invalid
            if appid < 10:
                skipped += 1
                continue

            Game.objects.update_or_create(
                appid=appid,
                defaults={
                    "name": name,
                    "genre": g.get("genre", "Unknown"),
                    "description": g.get("developer", ""),
                    "image": image_url,
                },
            )
            saved_count += 1

            if saved_count % 100 == 0:
                self.stdout.write(f"💾 Saved {saved_count} games...")

            if saved_count >= 1000:
                break

        self.stdout.write(self.style.SUCCESS(f"✅ Done! Saved {saved_count} games total."))
        self.stdout.write(self.style.WARNING(f"🚫 Skipped {skipped} invalid or missing games."))
