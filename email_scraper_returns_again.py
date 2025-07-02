import json
import re
import time
import random
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# === Configuration ===
INPUT_FILE = "indiResults.json"
OUTPUT_FILE = "email_scraped.json"
NUM_TO_SCRAPE = 700  # 🔧 Set how many top founders to scrape

# === ChromeDriver path ===
chrome_driver_path = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"
service = Service(executable_path=chrome_driver_path)

# === Anti-detection Chrome options ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)

# === Hide navigator.webdriver ===
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

# === Email Regex ===
email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

# === Function to search and extract emails ===
def perform_search_and_extract(query):
    driver.get("https://www.google.com")
    time.sleep(random.uniform(2, 4))

    try:
        agree = driver.find_element(By.XPATH, "//button[contains(text(),'I agree') or contains(text(),'Accept all')]")
        agree.click()
        time.sleep(1)
    except:
        pass

    if "sorry/index" in driver.current_url or "captcha" in driver.page_source.lower():
        print("🛑 CAPTCHA detected. Solve it manually.")
        input("✅ Press Enter when done...")

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(random.uniform(3, 5))

    snippets = driver.find_elements(By.CSS_SELECTOR, "div.VwiC3b")
    emails_found = set()
    for snippet in snippets:
        text = snippet.text
        emails = re.findall(email_regex, text)
        emails_found.update(emails)

    return list(emails_found)


# === Load input JSON ===
with open(INPUT_FILE, "r") as f:
    projects = json.load(f)

try:
    # === Process founders and update entries ===
    for i, project in enumerate(projects[:NUM_TO_SCRAPE]):
        founder = project.get("founder_name", "").strip()
        if not founder:
            project["emails"] = []
            continue

        print(f"🔍 Searching email for: {founder}")
        try:
            company_query = f"{founder} founder email contact site:{founder.lower().replace(' ', '')}.com"
            emails = perform_search_and_extract(company_query)

            if not emails:
                print(f"🔁 No company email found for {founder}, retrying as person...")
                person_query = f"{founder} email contact gmail OR outlook"
                emails = perform_search_and_extract(person_query)

            project["emails"] = emails if emails else ["No email found"]

        except Exception as e:
            project["emails"] = [f"Error: {str(e)}"]

        if (i + 1) % 5 == 0:
            print("⏳ Cooling down...")
            time.sleep(10)

    # Fill in remaining entries without scraping
    for project in projects[NUM_TO_SCRAPE:]:
        project["emails"] = []

except KeyboardInterrupt:
    print("\n⛔️ Interrupted by user. Saving progress...")

finally:
    driver.quit()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(projects, f, indent=2)
    print(f"\n✅ Data saved to '{OUTPUT_FILE}'. Exiting.")
