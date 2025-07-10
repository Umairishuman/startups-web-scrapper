import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# === Config ===
INPUT_FILE = "kickstarter_links.json"
OUTPUT_FILE = "kickstarter_project_data.json"
CHROME_DRIVER_PATH = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"
MAX_RETRIES = 2

# === Setup driver creator ===
def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Optional: run headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

# === Load input links ===
with open(INPUT_FILE, "r") as f:
    links = json.load(f)["links"]

# === Load previous progress ===
results = []
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r") as f:
        try:
            results = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Output file is corrupt. Starting fresh.")
            results = []

scraped_urls = {entry["url"] for entry in results}
start_index = next((i for i, link in enumerate(links) if link not in scraped_urls), len(links))

print(f"\n🔁 Resuming from index {start_index} (Total links: {len(links)})")

driver = create_driver()

def is_captcha_or_blocked():
    try:
        title_text = driver.title.lower()
        return any(bad in title_text for bad in ["cloudflare", "access denied", "attention required", "robot"])
    except:
        return True

try:
    i = start_index
    while i < len(links):
        link = links[i]
        print(f"\n🔗 [{i+1}/{len(links)}] Visiting: {link}")

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            driver.get(link)
            time.sleep(6)

            if is_captcha_or_blocked():
                print("⚠️ CAPTCHA or Cloudflare detected. Restarting browser...")
                driver.quit()
                time.sleep(10)
                driver = create_driver()
                continue

            project_data = {
                "url": link,
                "title": None,
                "social_links": [],
                "paragraphs": []
            }

            try:
                title_elem = driver.find_element(By.XPATH, '//h1[contains(@class, "project-name")]')
                project_data["title"] = title_elem.text.strip()
                print(f"📝 Title (main): {project_data['title']}")
            except:
                try:
                    alt_title_elem = driver.find_element(By.XPATH, '//h1[contains(@class, "project-profile__title")]//a[contains(@class, "hero__link")]')
                    project_data["title"] = alt_title_elem.text.strip()
                    print(f"📝 Title (fallback): {project_data['title']}")
                except:
                    print(f"❌ Attempt {attempt}: Title not found.")
                    time.sleep(5)
                    continue  # Retry

            if not project_data["title"]:
                continue

            # === Social links
            try:
                social_a_tags = driver.find_elements(By.CSS_SELECTOR,
                    'a[href*="twitter.com"], a[href*="facebook.com"], a[href*="bsky.app"], a[href^="mailto:"]')
                social_links = [a.get_attribute("href") for a in social_a_tags if a.get_attribute("href")]
                project_data["social_links"].extend(social_links)
                print(f"🔗 Social Links: {len(social_links)}")
            except Exception as e:
                print("⚠️ Failed to extract social links:", e)

            # === Paragraphs and List Items
            try:
                p_tags = driver.find_elements(By.TAG_NAME, "p")
                li_tags = driver.find_elements(By.TAG_NAME, "li")
                paragraphs = [p.text.strip() for p in p_tags if p.text.strip()]
                list_items = [li.text.strip() for li in li_tags if li.text.strip()]
                all_texts = paragraphs + list_items
                project_data["paragraphs"] = all_texts
                print(f"📄 Text Blocks: {len(all_texts)}")
            except:
                print("⚠️ <p> or <li> tags not found.")

            results.append(project_data)
            success = True
            break  # Success — exit retry loop

        if not success:
            print(f"⏭️ Skipping {link} after {MAX_RETRIES} failed attempts.")

        i += 1

        # Save progress after every link
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print("✅ Scraped and saved.")
        print("-" * 60)
        time.sleep(3)

except KeyboardInterrupt:
    print("\n🛑 Interrupted. Saving progress...")

except Exception as e:
    print(f"\n❌ Error: {e}. Saving progress...")

finally:
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\n✅ Final save complete. Scraped {len(results)} projects.")
    driver.quit()
