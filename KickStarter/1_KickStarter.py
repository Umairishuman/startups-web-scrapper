import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# === Configuration ===
BASE_URL = "https://www.kickstarter.com/discover/advanced"
CATEGORY_ID = 16
MAX_PAGES = 150  # Total pages to scrape
OUTPUT_FILE = "kickstarter_links.json"
CHROME_DRIVER_PATH = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"

# === Set to hold unique links ===
all_links = set()
current_page = 1

# === Save collected links to file ===
def save_links():
    with open(OUTPUT_FILE, "w") as f:
        json.dump({"links": list(all_links)}, f, indent=4)
    print(f"💾 Saved {len(all_links)} unique links to {OUTPUT_FILE}")

# === Initialize Selenium Driver ===
def create_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Uncomment for headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

driver = create_driver()

try:
    while current_page <= MAX_PAGES:
        print(f"\n🔍 Scraping page {current_page}...")

        url = f"{BASE_URL}?category_id={CATEGORY_ID}&woe_id=0&sort=magic&seed=2919644&page={current_page}"
        driver.get(url)
        # time.sleep(5)

        anchors = driver.find_elements(By.CSS_SELECTOR, "a.project-card__title.soft-black.hover-soft-black.keyboard-focusable.focus-invisible")
        page_links = {a.get_attribute('href') for a in anchors if a.get_attribute('href')}

        # CAPTCHA detection: if no links found, assume CAPTCHA or block
        if len(page_links) == 0:
            print("⚠️ Possible CAPTCHA detected or no links found. Restarting browser after cooldown...")
            driver.quit()
            # time.sleep(5)  # Longer cooldown before restarting
            driver = create_driver()
            continue  # Retry current_page again

        print(f"✅ Found {len(page_links)} links on page {current_page}")
        all_links.update(page_links)

        current_page += 1

        # Cool-down between pages to avoid detection
        # cooldown = random.uniform(4, 9)
        # print(f"🕓 Cooling down for {cooldown:.2f} seconds...")
        # time.sleep(cooldown)

except KeyboardInterrupt:
    print("\n🛑 Interrupted by user (Ctrl+C). Saving collected links...")
    save_links()

except Exception as e:
    print(f"\n❌ Error occurred: {e}. Saving collected links and exiting...")
    save_links()

else:
    print("\n✅ Finished scraping all pages.")
    save_links()

finally:
    driver.quit()
