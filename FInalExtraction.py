from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time
import os

# ---------- Configurable ----------
CHROMEDRIVER_PATH = '/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver'
START_INDEX = 0  # Change this to resume from a specific log number
MAX_LIMIT = 10  # Set this to an integer to limit scraping (e.g., 50), or None to scrape all

# ---------- Chrome Options ----------
options = Options()
# options.add_argument('--headless')  # Uncomment if needed
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

# ---------- Load URL List ----------
with open('results2.json', 'r') as file:
    all_urls = json.load(file)

# Apply starting index offset
all_urls = all_urls[START_INDEX:]

# Apply scraping limit
if MAX_LIMIT is not None:
    all_urls = all_urls[:MAX_LIMIT]

# Load already scraped results (if exist)
results = []
existing_urls = set()
if os.path.exists('indiResults.json'):
    with open('indiResults.json', 'r') as file:
        try:
            results = json.load(file)
            existing_urls = set(item['url'] for item in results)
            print(f"Loaded {len(results)} existing logs.")
        except json.JSONDecodeError:
            print("⚠️ Warning: indiResults.json is corrupted or empty. Starting fresh.")

# Remove already scraped URLs
urls = [url for url in all_urls if url not in existing_urls]
print(f"🔁 Starting from index {START_INDEX}. Scraping up to {len(urls)} URLs.\n")

# ---------- Main Loop ----------
new_results = []

try:
    for index, url in enumerate(urls):
        global_index = START_INDEX + index
        print(f"\n[{global_index}] Loading: {url}")

        if index > 0 and index % 15 == 0:
            print("⏳ Rate limit buffer: Sleeping for 10 seconds...")
            time.sleep(10)

        if index > 0 and index % 10 == 0:
            print("🧹 Clearing cookies...")
            driver.delete_all_cookies()

        if index > 0 and index % 30 == 0:
            print("🔄 Restarting browser to reset memory/session...")
            driver.quit()
            driver = launch_browser()
            wait = WebDriverWait(driver, 10)

        try:
            driver.get(url)
        except Exception as e:
            print(f"❌ Error loading URL: {e}")
            new_results.append({
                "url": url,
                "title": "Timeout",
                "description": "Timeout",
                "founder_name": "Timeout",
                "allParagraphs": []
            })
            continue

        try:
            title_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-title")))
            title = driver.execute_script("return arguments[0].innerText;", title_element).strip()

            description_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-tagline")))
            description = driver.execute_script("return arguments[0].innerText;", description_element).strip()

            founder_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "campaignOwnerName-tooltip")))
            founder_name = founder_element.text.strip()

            paragraph_elements = driver.find_elements(By.TAG_NAME, "p")
            all_paragraphs = [p.text.strip() for p in paragraph_elements if p.text.strip() != ""]

            new_results.append({
                "url": url,
                "title": title,
                "description": description,
                "founder_name": founder_name,
                "allParagraphs": all_paragraphs
            })

            print(f"✅ Scraped: {title} | paragraphs: {len(all_paragraphs)}")

        except Exception as e:
            print(f"⚠️ Extraction error for {url}: {e}")
            new_results.append({
                "url": url,
                "title": "Failed",
                "description": "Failed",
                "founder_name": "Failed",
                "allParagraphs": []
            })

except KeyboardInterrupt:
    print("\n🛑 KeyboardInterrupt received. Saving progress...")

except Exception as e:
    print(f"\n🔥 Unexpected error: {e}")

finally:
    # Append new results and save
    combined_results = results + new_results
    with open('indiResults.json', 'w') as file:
        json.dump(combined_results, file, indent=4)
    driver.quit()
    print(f"\n✅ Appended {len(new_results)} new entries. Total: {len(combined_results)}. Saved to indiResults.json.")
