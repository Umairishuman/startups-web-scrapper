import json
import re
import time
import random
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# === Configuration ===
INPUT_FILE = "indiResults.json"
OUTPUT_FILE = "email_scraped_after_200.json"
START_INDEX = 259                # Change this to resume from a specific index
NUM_TO_SCRAPE = None           # Set a limit (e.g., 100) or leave as None to scrape all from START_INDEX

chrome_driver_path = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"
service = Service(executable_path=chrome_driver_path)

# === Chrome Options ===
options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)

# === Hide navigator.webdriver ===
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

def perform_search_and_extract(query):
    query_url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    driver.get(query_url)
    time.sleep(random.uniform(2, 3))

    try:
        agree = driver.find_element(By.XPATH, "//button[contains(text(),'I agree') or contains(text(),'Accept all')]")
        agree.click()
        time.sleep(1)
    except:
        pass

    if "sorry/index" in driver.current_url or "captcha" in driver.page_source.lower():
        print("🛑 CAPTCHA detected. Solve it manually.")
        input("✅ Press Enter when done...")

    time.sleep(random.uniform(2, 3))

    snippets = driver.find_elements(By.CSS_SELECTOR, "div.VwiC3b")
    emails_found = set()
    for snippet in snippets:
        text = snippet.text
        emails = re.findall(email_regex, text)
        emails_found.update(emails)

    return list(emails_found)

# === Load input ===
with open(INPUT_FILE, "r") as f:
    projects = json.load(f)

# === Determine range ===
total_projects = len(projects)
end_index = total_projects if NUM_TO_SCRAPE is None else min(START_INDEX + NUM_TO_SCRAPE, total_projects)

try:
    for i in range(START_INDEX, end_index):
        project = projects[i]
        company_name = project.get("company_name", "").strip()
        if not company_name:
            project["emails"] = []
            continue

        try:
            query = f"{company_name} email OR contact"
            emails = perform_search_and_extract(query)
            project["emails"] = emails if emails else ["No email found"]

            # ✅ Log progress
            print(f"{'✅' if emails else '❌'} {i}/{total_projects} {company_name}: {emails}")

        except Exception as e:
            project["emails"] = [f"Error: {str(e)}"]
            print(f"🔥 {i}/{total_projects} {company_name}: Error: {str(e)}")

        if (i + 1) % 10 == 0:
            print("⏳ Cooling down...")
            time.sleep(5)

    # Fill the rest if any were skipped
    for i in range(total_projects):
        if "emails" not in projects[i]:
            projects[i]["emails"] = []

except KeyboardInterrupt:
    print("\n⛔️ Interrupted by user. Saving progress...")

finally:
    driver.quit()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(projects, f, indent=2)
    print(f"\n💾 Data saved to '{OUTPUT_FILE}'. Exiting.")
