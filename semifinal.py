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
START_INDEX = 31
MAX_LIMIT = 700  # or set to an integer like 50

# ---------- Chrome Options ----------
options = Options()
# options.add_argument('--headless=new')  # Uncomment for headless
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
with open('URLs.json', 'r') as file:
    all_urls = json.load(file)

all_urls = all_urls[START_INDEX:]

if MAX_LIMIT is not None:
    all_urls = all_urls[:MAX_LIMIT]

# ---------- Load existing results ----------
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

urls = [url for url in all_urls if url not in existing_urls]
print(f"🔁 Starting from index {START_INDEX}. Scraping up to {len(urls)} URLs.\n")

# ---------- Main Loop ----------
new_results = []

try:
    for index, url in enumerate(urls):
        global_index = START_INDEX + index
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
            new_results.append({
                "url": url,
                "title": "Timeout",
                "description": "Timeout",
                "company_name": "Timeout",
                "allParagraphs": [],
                "social_links": [],
                "company_links": []
            })
            continue

        try:
            title_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-title")))
            title = driver.execute_script("return arguments[0].innerText;", title_element).strip()

            description_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-tagline")))
            description = driver.execute_script("return arguments[0].innerText;", description_element).strip()

            founder_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "campaignOwnerName-tooltip")))
            company_name = founder_element.text.strip()

            # Hover over the founder element
            ActionChains(driver).move_to_element(founder_element).perform()
            time.sleep(1.5)  # Allow tooltip to appear

            social_links_set = set()
            company_links_set = set()

            try:
                tooltip_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tooltipHover-transition")))
                anchor_tags = tooltip_element.find_elements(By.TAG_NAME, "a")

                for a in anchor_tags:
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

            paragraph_elements = driver.find_elements(By.TAG_NAME, "p")
            all_paragraphs = [p.text.strip() for p in paragraph_elements if p.text.strip() != ""]

            new_results.append({
                "url": url,
                "title": title,
                "description": description,
                "company_name": company_name,
                "allParagraphs": all_paragraphs,
                "social_links": list(social_links_set),
                "company_links": list(company_links_set)
            })

            print(f"✅ Scraped: {title} | paragraphs: {len(all_paragraphs)} | social: {len(social_links_set)} | company: {len(company_links_set)}")

        except Exception as e:
            print(f"⚠️ Extraction error for {url}: {e}")
            new_results.append({
                "url": url,
                "title": "Failed",
                "description": "Failed",
                "company_name": "Failed",
                "allParagraphs": [],
                "social_links": [],
                "company_links": []
            })

except KeyboardInterrupt:
    print("\n🛑 Interrupted. Saving progress...")

except Exception as e:
    print(f"\n🔥 Unexpected error: {e}")

finally:
    combined_results = results + new_results
    with open('indiResults.json', 'w') as file:
        json.dump(combined_results, file, indent=4)
    driver.quit()
    print(f"\n✅ Appended {len(new_results)} new entries. Total: {len(combined_results)}. Saved to indiResults.json.")
