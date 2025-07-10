import json
import re
import time
import random
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# === Configuration ===
INPUT_FILE = "indiResults2.json"
OUTPUT_FILE = "email_scraped_after_2_8.json"
START_INDEX = 1152
NUM_TO_SCRAPE = None
chrome_driver_path = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"

email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

# === Load input ===
with open(INPUT_FILE, "r") as f:
    projects = json.load(f)

total_projects = len(projects)
end_index = total_projects if NUM_TO_SCRAPE is None else min(START_INDEX + NUM_TO_SCRAPE, total_projects)

processed_projects = []
captcha_retry_counter = {}

# === Chrome Setup Function ===
def launch_driver():
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Uncomment to run headless
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# === Scraper Logic ===
def perform_search_and_extract(driver, query):
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
        raise Exception("Captcha Detected")

    time.sleep(random.uniform(2, 3))

    snippets = driver.find_elements(By.CSS_SELECTOR, "div.VwiC3b")
    emails_found = set()
    for snippet in snippets:
        text = snippet.text
        emails = re.findall(email_regex, text)
        emails_found.update(emails)

    return list(emails_found)

# === Main Execution Loop ===
current_index = START_INDEX
driver = launch_driver()

try:
    while current_index < end_index:
        project = projects[current_index]
        company_name = project.get("company_name", "").strip()

        if not company_name:
            project["emails"] = []
            processed_projects.append(project)
            current_index += 1
            continue

        try:
            query = f"{company_name} email OR contact"
            emails = perform_search_and_extract(driver, query)
            project["emails"] = emails if emails else ["No email found"]
            print(f"{'✅' if emails else '❌'} {current_index}/{total_projects} {company_name}: {emails}")
            processed_projects.append(project)
            current_index += 1

            if (current_index + 1) % 10 == 0:
                print("⏳ Cooling down...")
                time.sleep(2)

        except Exception as e:
            if "Captcha Detected" in str(e):
                captcha_retry_counter[current_index] = captcha_retry_counter.get(current_index, 0) + 1
                if captcha_retry_counter[current_index] >= 3:
                    print(f"❌ Skipping index {current_index} after 3 CAPTCHA attempts.")
                    project["emails"] = ["Error: CAPTCHA detected 3 times"]
                    processed_projects.append(project)
                    current_index += 1
                    continue
                print(f"🛑 CAPTCHA detected at index {current_index} (Attempt {captcha_retry_counter[current_index]}). Restarting driver...")
                driver.quit()
                # time.sleep(random.randint(5, 10))
                driver = launch_driver()
                continue
            else:
                project["emails"] = [f"Error: {str(e)}"]
                print(f"🔥 {current_index}/{total_projects} {company_name}: Error: {str(e)}")
                processed_projects.append(project)
                current_index += 1

except KeyboardInterrupt:
    print("\n⛔️ Interrupted by user. Saving progress...")

finally:
    driver.quit()
    with open(OUTPUT_FILE, "w") as f:
        json.dump(processed_projects, f, indent=2)
    print(f"\n💾 {len(processed_projects)} entries saved to '{OUTPUT_FILE}'. Exiting.")
