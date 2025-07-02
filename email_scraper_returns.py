from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random
import re

# ChromeDriver path
chrome_driver_path = "/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver"
service = Service(executable_path=chrome_driver_path)

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=service, options=options)

# Hide navigator.webdriver
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

# People & companies to search
entities = ["SpaceX", "OpenAI", "Muhammad Umair", "Nvidia", "Elon Musk"]
results = {}

email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

def perform_search_and_extract(query):
    driver.get("https://www.google.com")
    time.sleep(random.uniform(2, 4))

    # Accept cookies
    try:
        agree = driver.find_element(By.XPATH, "//button[contains(text(),'I agree') or contains(text(),'Accept all')]")
        agree.click()
        time.sleep(1)
    except:
        pass

    # CAPTCHA handling
    if "sorry/index" in driver.current_url or "captcha" in driver.page_source.lower():
        print("🛑 CAPTCHA detected. Please solve it manually.")
        input("✅ Press Enter when done...")

    # Perform search
    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(random.uniform(3, 5))

    # Collect snippets and extract emails
    snippets = driver.find_elements(By.CSS_SELECTOR, "div.VwiC3b")
    emails_found = set()
    for snippet in snippets:
        text = snippet.text
        emails = re.findall(email_regex, text)
        emails_found.update(emails)

    return emails_found

for index, name in enumerate(entities):
    try:
        print(f"🔍 Searching for: {name}")
        is_person = " " in name.strip()

        # First attempt: company-style search
        company_query = f"{name} founder email contact site:{name.lower().replace(' ', '')}.com"
        emails = perform_search_and_extract(company_query)

        # If no emails found, try person-style search
        if not emails:
            print(f"🔁 No company email found for {name}, retrying as person...")
            person_query = f"{name} email contact gmail OR outlook"
            emails = perform_search_and_extract(person_query)

        # Store results
        if emails:
            results[name] = ", ".join(emails)
        else:
            results[name] = "No email found in both attempts."

    except Exception as e:
        results[name] = f"Error: {str(e)}"

    if (index + 1) % 5 == 0:
        print("⏳ Cooling down to avoid detection...")
        time.sleep(10)

driver.quit()

# Final Output
print("\n📨 Extracted Emails:\n")
for name, email in results.items():
    print(f"{name}: {email}")
