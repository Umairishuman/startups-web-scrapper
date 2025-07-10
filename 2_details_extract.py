from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import os

# ---------- Configurable ----------
CHROMEDRIVER_PATH = '/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver'
MAX_LIMIT = None  # or set to None for no limit
DATA_FILE = 'indiResults2.json'
URLS_FILE = 'URLs.json'

# ---------- Chrome Options ----------
options = Options()
# options.add_argument('--headless=new')  # Uncomment to run headless
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

def launch_browser():
    service = Service(CHROMEDRIVER_PATH)
    browser = webdriver.Chrome(service=service, options=options)
    browser.set_page_load_timeout(30)
    return browser

driver = launch_browser()
wait = WebDriverWait(driver, 10)

# ---------- Load All URLs ----------
with open(URLS_FILE, 'r') as file:
    all_urls = json.load(file)

# ---------- Load Existing Results ----------
results = []
existing_urls = set()
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as file:
        try:
            results = json.load(file)
            existing_urls = set(item['url'] for item in results)
            print(f"✅ Loaded {len(results)} existing entries from '{DATA_FILE}'")
        except json.JSONDecodeError:
            print("⚠️ Warning: Data file is corrupted or empty. Starting fresh.")

# ---------- Filter Remaining URLs ----------
urls_to_scrape = [url for url in all_urls if url not in existing_urls]
if MAX_LIMIT:
    urls_to_scrape = urls_to_scrape[:MAX_LIMIT]

print(f"🔁 Resuming scraping from index {len(existing_urls)}. Remaining: {len(urls_to_scrape)} URLs\n")

# ---------- Main Loop ----------
new_results = []

try:
    for index, url in enumerate(urls_to_scrape):
        global_index = len(existing_urls) + index
        print(f"\n[{global_index}] Loading: {url}")

        if index > 0 and index % 15 == 0:
            print("⏳ Sleeping for 10 seconds...")
            time.sleep(10)

        if index > 0 and index % 10 == 0:
            print("🧹 Clearing cookies...")
            driver.delete_all_cookies()

        if index > 0 and index % 30 == 0:
            print("🔄 Restarting browser...")
            driver.quit()
            driver = launch_browser()
            wait = WebDriverWait(driver, 10)

        try:
            driver.get(url)
        except Exception as e:
            print(f"❌ Error loading URL: {e}")
            data = {
                "url": url,
                "title": "Timeout",
                "description": "Timeout",
                "company_name": "Timeout",
                "allParagraphs": [],
                "social_links": [],
                "company_links": []
            }
            results.append(data)
            continue  # Move to next URL

        try:
            title_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-title")))
            title = driver.execute_script("return arguments[0].innerText;", title_element).strip()

            description_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-tagline")))
            description = driver.execute_script("return arguments[0].innerText;", description_element).strip()
            founder = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "campaignOwnerName-tooltip"))).text.strip()

            ActionChains(driver).move_to_element(
                driver.find_element(By.CLASS_NAME, "campaignOwnerName-tooltip")
            ).perform()
            time.sleep(1.5)

            social_links_set = set()
            company_links_set = set()

            try:
                tooltip = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tooltipHover-transition")))
                anchors = tooltip.find_elements(By.TAG_NAME, "a")

                for a in anchors:
                    href = a.get_attribute("href")
                    if not href:
                        continue
                    href_lower = href.lower()
                    if any(social in href_lower for social in ["facebook.com", "instagram.com", "youtube.com", "twitter.com", "linkedin.com", "x.com"]):
                        social_links_set.add(href)
                    else:
                        company_links_set.add(href)

            except Exception as tooltip_err:
                print(f"⚠️ Tooltip scraping failed: {tooltip_err}")

            paragraphs = [p.text.strip() for p in driver.find_elements(By.TAG_NAME, "p") if p.text.strip()]
            data = {
                "url": url,
                "title": title,
                "description": description,
                "company_name": founder,
                "allParagraphs": paragraphs,
                "social_links": list(social_links_set),
                "company_links": list(company_links_set)
            }

            print(f"✅ Scraped: {title} | paragraphs: {len(paragraphs)} | social: {len(social_links_set)} | company: {len(company_links_set)}")

        except Exception as e:
            print(f"⚠️ Extraction error: {e}")
            data = {
                "url": url,
                "title": "Failed",
                "description": "Failed",
                "company_name": "Failed",
                "allParagraphs": [],
                "social_links": [],
                "company_links": []
            }

        results.append(data)

        # 🧷 Save after every URL
        with open(DATA_FILE, 'w') as f:
            json.dump(results, f, indent=4)

except KeyboardInterrupt:
    print("\n🛑 Interrupted. Saving progress...")

except Exception as e:
    print(f"\n🔥 Unexpected error: {e}")

finally:
    driver.quit()
    print(f"\n✅ Scraping complete. Total saved: {len(results)} → {DATA_FILE}")
