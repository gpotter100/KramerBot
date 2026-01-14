from playwright.sync_api import sync_playwright
import json
import datetime
import os

BASE_URL = "https://louieshades.football.cbssports.com"
STANDINGS_URL = f"{BASE_URL}/standings"

EMAIL = "gpotter100@gmail.com"
PASSWORD = "paradise"

# Toggle this to True when debugging manually
DEBUG_VISIBLE = False


def scrape_standings(page, season_label):
    """Scrape standings table rows from the current page."""
    standings = []
    rows = page.locator("table tr")

    for i in range(rows.count()):
        cells = rows.nth(i).locator("td")
        if cells.count() > 0:
            row_data = [cells.nth(j).inner_text().strip() for j in range(cells.count())]
            standings.append([season_label] + row_data)

    return standings


def run():
    with sync_playwright() as p:

        # Visible browser for debugging, headless for Task Scheduler
        if DEBUG_VISIBLE:
            browser = p.chromium.launch(headless=False, slow_mo=600)
        else:
            browser = p.chromium.launch(headless=True)

        # Load cookies if available
        try:
            context = browser.new_context(storage_state="cbs_storage.json")
            print("Loaded saved CBS session.")
        except Exception:
            context = browser.new_context()
            print("No saved session found. Logging in fresh.")

        page = context.new_page()

        # Go to standings page
        page.goto(STANDINGS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Login if redirected
        if "login" in page.url:
            print("Redirected to login, filling credentials...")
            page.fill('input[name="email"]', EMAIL)
            page.fill('input[name="password"]', PASSWORD)
            page.click('button[type="submit"]')

            # Wait for CBS to finish redirecting
            page.wait_for_timeout(8000)
            page.goto(STANDINGS_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

        # Find season dropdown
        options = page.locator("select").nth(0).locator("option")
        season_count = options.count()
        print(f"Found {season_count} seasons.")

        season_links = []
        for i in range(season_count):
            label = options.nth(i).inner_text().strip()
            value = options.nth(i).get_attribute("value")
            if value:
                season_links.append((label, BASE_URL + value))

        all_standings = []

        # Scrape each season
        for label, season_url in season_links:
            print(f"Scraping standings for {label} at {season_url}")
            page.goto(season_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            season_standings = scrape_standings(page, label)
            print(f"  Found {len(season_standings)} rows for {label}")
            all_standings.extend(season_standings)

        # Build JSON output
        output = {
            "last_updated": datetime.datetime.now().isoformat(),
            "standings": all_standings
        }

        # Save JSON
        with open("standings.json", "w") as f:
            json.dump(output, f, indent=2)

        print("Saved standings.json")

        # Save cookies/session
        storage = context.storage_state()
        with open("cbs_storage.json", "w") as f:
            f.write(json.dumps(storage))

        print("Saved session cookies to cbs_storage.json")

        if DEBUG_VISIBLE:
            input("Press Enter to close browser...")

        browser.close()


if __name__ == "__main__":
    run()
