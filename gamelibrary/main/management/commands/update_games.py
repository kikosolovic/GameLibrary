import requests
from django.core.management.base import BaseCommand
from main.models import Game


class Command(BaseCommand):
    help = "Enhanced update: fetch SteamSpy + SteamStore data, including scores and prices."

    def fetch_steamstore(self, appid):
        """Fetch detailed game info from Steam Store API."""
        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english&cc=us"
        try:
            r = requests.get(url, timeout=10)
            data = r.json()

            if not data.get(str(appid), {}).get("success"):
                return None

            return data[str(appid)]["data"]
        except:
            return None

    def fetch_steamspy(self, appid):
        """Fetch basic numeric stats from SteamSpy appdetails."""
        url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
        try:
            r = requests.get(url, timeout=10)
            return r.json()
        except:
            return None

    def handle(self, *args, **options):
        self.stdout.write("🟢 ENHANCED UPDATE: SteamSpy lists...")

        endpoints = [
            "top100in2weeks",
            "top100owned",
            "top100forever",
            "all",
        ]

        all_games = {}

        # Fetch basic lists from SteamSpy
        for endpoint in endpoints:
            url = f"https://steamspy.com/api.php?request={endpoint}"
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    all_games.update(data)
                    self.stdout.write(f"✅ {endpoint}: {len(data)} games")
                else:
                    self.stdout.write(f"⚠️ Error loading {endpoint}")
            except Exception as e:
                self.stdout.write(f"⚠️ Failed {endpoint}: {e}")

        # Clear DB
        Game.objects.all().delete()
        self.stdout.write("🧹 Old games removed.")

        saved = 0

        for g in list(all_games.values())[:1200]:
            appid = g.get("appid")
            name = g.get("name", "").strip()
            if not appid or not name:
                continue

            # -------------------------------------------------------
            # 1. SteamSpy appdetails (positive/negative)
            # -------------------------------------------------------
            steamspy = self.fetch_steamspy(appid)
            positive = steamspy.get("positive", 0) if steamspy else 0
            negative = steamspy.get("negative", 0) if steamspy else 0

            # score calculation
            if positive + negative > 0:
                score = round((positive * 100) / (positive + negative), 2)
            else:
                score = 0.0

            # -------------------------------------------------------
            # 2. SteamStore info (real genres + price)
            # -------------------------------------------------------
            store = self.fetch_steamstore(appid)

            # genre
            if store and store.get("genres"):
                genre = ", ".join(g["description"] for g in store["genres"])
            else:
                genre = "Unknown"

            # price
            price_info = store.get("price_overview") if store else None
            if price_info:
                price = f"{price_info['final']/100:.2f} {price_info['currency']}"
            else:
                price = "Free" if store and store.get("is_free") else "Unavailable"

            # images
            cover = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/library_600x900_2x.jpg"
            fallback_cover = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"

            # Save to DB
            Game.objects.update_or_create(
                appid=appid,
                defaults={
                    "name": name,
                    "genre": genre,
                    "image": cover,
                    "fallback_image": fallback_cover,
                    "price": price,
                    "positive": positive,
                    "negative": negative,
                    "score": score,
                }
            )

            saved += 1
            if saved % 100 == 0:
                self.stdout.write(f"💾 Saved {saved} games...")

            if saved >= 1000:
                break

        self.stdout.write(self.style.SUCCESS(f"✅ ENHANCED UPDATE COMPLETE — {saved} games saved."))
