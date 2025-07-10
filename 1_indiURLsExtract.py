from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sys

# Set up WebDriver service
service = Service('/home/muhammad-umair/Desktop/Selenium Drivers/chromedriver')
driver = webdriver.Chrome(service=service)

# Open the Indiegogo page
url = "https://www.indiegogo.com/explore/tech-innovation?project_timing=all&product_stage=all&ended_campaigns_included=false&sort=trending"
driver.get(url)

# Set maximum execution time and results limit
timeout_seconds = 3600
start_time = time.time()
max_entries = 5000
all_data = []

# Function to scrape URLs from the current view
def scrape_urls():
    urls = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'projectDiscoverableCard'))
        )
        project_cards = driver.find_elements(By.CLASS_NAME, 'projectDiscoverableCard')
        print(f"Found {len(project_cards)} project cards on the current view.")
        for card in project_cards:
            try:
                anchor_tag = card.find_element(By.TAG_NAME, 'a')
                href = anchor_tag.get_attribute('href')
                if href and href not in urls:
                    urls.append(href)
            except NoSuchElementException:
                print("Skipping a project card due to missing anchor tag.")
            except Exception as e:
                print(f"Unexpected error while scraping a card: {e}")
    except TimeoutException:
        print("Timeout waiting for project cards to load.")
    except Exception as e:
        print(f"Error while finding project cards: {e}")
    return urls

# Function to click the "Show more" button
def click_show_more():
    try:
        show_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[gogo_test='show_more']"))
        )
        show_more_button.click()
        time.sleep(5)
        print("Clicked 'Show more' button.")
        return True
    except TimeoutException:
        print("'Show more' button not found or not clickable.")
    except ElementClickInterceptedException:
        print("Unable to click 'Show more' button due to overlay or interruption.")
    except Exception as e:
        print(f"Unexpected error while clicking 'Show more': {e}")
    return False

# Function to scroll near the footer
def scroll_near_footer():
    try:
        print("Scrolling near the footer...")
        total_height = driver.execute_script("return document.body.scrollHeight;")
        driver.execute_script(f"window.scrollTo(0, {total_height - 800});")
        time.sleep(5)
    except Exception as e:
        print(f"Error while scrolling near footer: {e}")

# Function to save data
def save_data():
    try:
        with open("URLs.json", "w", encoding="utf-8") as file:
            json.dump(list(set(all_data)), file, indent=4, ensure_ascii=False)
        print(f"Scraped data saved to 'URLs.json'. Total entries: {len(all_data)}")
    except Exception as e:
        print(f"Error saving data to file: {e}")

# Main execution with error handling
try:
    while len(all_data) < max_entries:
        if time.time() - start_time > timeout_seconds:
            print(f"Timeout of {timeout_seconds} seconds reached. Exiting scraping process.")
            break

        new_urls = scrape_urls()
        all_data.extend(new_urls)
        all_data = list(set(all_data))  # Deduplicate
        print(f"Scraped {len(all_data)} unique URLs so far...")

        if not click_show_more():
            scroll_near_footer()

except KeyboardInterrupt:
    print("\nScraper interrupted by user (Ctrl+C). Saving data...")

except Exception as e:
    print(f"\nUnexpected error occurred: {e}. Saving data...")

finally:
    save_data()
    driver.quit()
    print("Driver closed.")
