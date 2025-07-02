from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time
import random

# Optional: Use headless mode to reduce resource usage
options = Options()
# options.add_argument('--headless')  # Uncomment if you want no GUI
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Set up WebDriver
service = Service('/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver')
driver = webdriver.Chrome(service=service, options=options)
driver.set_page_load_timeout(30)  # Limit page load time to 30 seconds

# Load URLs from results2.json
with open('results2.json', 'r') as file:
    urls = json.load(file)

results = []
wait = WebDriverWait(driver, 10)

try:
    for index, url in enumerate(urls):
        if index > 0 and index % 15 == 0:
            print("Rate limit buffer: Sleeping for 10 seconds...")
            time.sleep(10)

        print(f"Loading URL {index+1}/{len(urls)}: {url}")

        # Catch page load timeout or other loading errors
        try:
            driver.get(url)
        except Exception as e:
            print(f"Error loading URL {url}: {e}")
            results.append({
                "url": url,
                "title": "Timeout",
                "description": "Timeout",
                "founder_name": "Timeout",
                "allParagraphs": []
            })
            continue

        try:
            title_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-title"))
            )
            title = driver.execute_script("return arguments[0].innerText;", title_element).strip()

            description_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "basicsSection-tagline"))
            )
            description = driver.execute_script("return arguments[0].innerText;", description_element).strip()

            founder_element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "campaignOwnerName-tooltip"))
            )
            founder_name = founder_element.text.strip()

            paragraph_elements = driver.find_elements(By.TAG_NAME, "p")
            all_paragraphs = [p.text.strip() for p in paragraph_elements if p.text.strip() != ""]

            results.append({
                "url": url,
                "title": title,
                "description": description,
                "founder_name": founder_name,
                "allParagraphs": all_paragraphs
            })

            print(f"✔ Logged: {url} | paragraphs: {len(all_paragraphs)}")

        except Exception as e:
            print(f"⚠️ Failed to extract data from {url}: {e}")
            results.append({
                "url": url,
                "title": "Failed",
                "description": "Failed",
                "founder_name": "Failed",
                "allParagraphs": []
            })

        time.sleep(random.uniform(1, 2.5))  # optional small delay between requests

except KeyboardInterrupt:
    print("\n⏹️ KeyboardInterrupt detected. Saving fetched data before exiting...")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")
finally:
    with open('indiResults.json', 'w') as file:
        json.dump(results, file, indent=4)
    driver.quit()
    print(f"\n✅ Saved {len(results)} results to indiResults.json. Exiting.")
