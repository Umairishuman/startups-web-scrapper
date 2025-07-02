from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# Set up WebDriver service
service = Service('/home/muhammad-umair/Downloads/chromedriver-linux64/chromedriver')
driver = webdriver.Chrome(service=service)

# Open the Indiegogo page
url = "https://www.indiegogo.com/explore/tech-innovation?project_timing=all&product_stage=all&ended_campaigns_included=false&sort=trending"
driver.get(url)

# Set maximum execution time and results limit
timeout_seconds = 180
start_time = time.time()
max_entries = 5000
all_data = []

# Function to scrape URLs from the current view
def scrape_urls():
    urls = []
    try:
        # Wait for the project cards to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'projectDiscoverableCard'))
        )
        
        project_cards = driver.find_elements(By.CLASS_NAME, 'projectDiscoverableCard')
        print(f"Found {len(project_cards)} project cards on the current view.")

        for card in project_cards:
            try:
                # Locate the anchor tag within the project card
                anchor_tag = card.find_element(By.TAG_NAME, 'a')
                href = anchor_tag.get_attribute('href')

                # Only add unique URLs
                if href not in urls:
                    urls.append(href)
            except NoSuchElementException:
                print("Skipping a project card due to missing anchor tag.")
                continue
            except Exception as e:
                print(f"Unexpected error while scraping a card: {e}")
                continue
    except TimeoutException:
        print("Timeout waiting for project cards to load.")
    except Exception as e:
        print(f"Error while finding project cards: {e}")
    return urls

# Main scraping loop
while len(all_data) < max_entries:
    if time.time() - start_time > timeout_seconds:
        print(f"Timeout of {timeout_seconds} seconds reached. Exiting scraping process.")
        break

    # Scrape the current view
    new_urls = scrape_urls()
    all_data.extend(new_urls)

    # Remove duplicates
    all_data = list(set(all_data))
    print(f"Scraped {len(all_data)} unique URLs so far...")

    # Scroll down to load more projects
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
        time.sleep(5)  # Allow time for new content to load
    except Exception as e:
        print(f"Error while scrolling: {e}")
        break

# Save results to a JSON file
try:
    with open("results2.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4, ensure_ascii=False)
    print(f"Scraped data saved to 'results2.json'. Total entries: {len(all_data)}")
except Exception as e:
    print(f"Error saving data to file: {e}")

# Close the browser
driver.quit()
