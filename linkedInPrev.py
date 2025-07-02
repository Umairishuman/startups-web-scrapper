import json
import time
import random
import signal
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# === Configuration ===
INPUT_FILE = "indiResults.json"
OUTPUT_FILE = "linkedin_scraped.json"
NUM_TO_SCRAPE = 15

# === ChromeDriver path ===
chrome_driver_path = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"
service = Service(executable_path=chrome_driver_path)

# === Chrome options to evade detection ===
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

# === Load input data ===
with open(INPUT_FILE, "r") as f:
    projects = json.load(f)

# === Save and Exit Handler ===
def save_and_exit(signum=None, frame=None):
    print("\n💾 Saving progress...")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(projects, f, indent=2)
    try:
        driver.quit()
    except:
        pass
    print("✅ Saved and exiting.")
    exit(0)

signal.signal(signal.SIGINT, save_and_exit)

# === Function to search LinkedIn URL ===
def perform_linkedin_search(query):
    driver.get("https://www.google.com")
    time.sleep(random.uniform(2, 4))

    try:
        agree = driver.find_element(By.XPATH, "//button[contains(text(),'I agree') or contains(text(),'Accept all')]")
        agree.click()
        time.sleep(1)
    except:
        pass

    if "sorry/index" in driver.current_url or "captcha" in driver.page_source.lower():
        print("🛑 CAPTCHA detected. Please solve it manually.")
        input("✅ Press Enter when done...")

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(random.uniform(3, 5))

    try:
        link_element = driver.find_element(By.XPATH, '(//a[contains(@class, "zReHs") and contains(@href, "linkedin.com")])[1]')
        return link_element.get_attribute("href")
    except:
        return None

# === Perform scraping ===
for i, project in enumerate(projects[:NUM_TO_SCRAPE]):
    founder = project.get("founder_name", "").strip()
    if not founder:
        project["linkedin"] = "No founder name"
        continue

    print(f"🔍 Searching LinkedIn for: {founder}")
    try:
        query = f"{founder} site:linkedin.com"
        linkedin_url = perform_linkedin_search(query)

        if linkedin_url:
            project["linkedin"] = linkedin_url
        else:
            project["linkedin"] = "No LinkedIn found"

    except Exception as e:
        project["linkedin"] = f"Error: {str(e)}"

    if (i + 1) % 5 == 0:
        print("⏳ Cooling down for 10 seconds...")
        time.sleep(10)

# Add blank values for the rest
for project in projects[NUM_TO_SCRAPE:]:
    project["linkedin"] = ""

# === Save final output ===
save_and_exit()
