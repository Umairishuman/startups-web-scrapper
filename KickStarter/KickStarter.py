from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sys

# Set up the WebDriver service
# Ensure this path is correct for your chromedriver executable
service = Service('/home/muhammad-umair/Downloads/chromedriver-linux64/chromedriver')
driver = webdriver.Chrome(service=service)

# Open the webpage
url = "https://www.kickstarter.com/discover/advanced"
driver.get(url)

# Set maximum allowed execution time
timeout_seconds = 20  
start_time = time.time()
loadButtonClicked = False   
# Function to click the "Load More" button
def click_load_more_button():
    global loadButtonClicked
    try:
        if loadButtonClicked:
            print("Load More button has already been clicked. Skipping...")
            return True

        # Using By.ID, 'text' as confirmed by the user
        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'text'))
        )



        load_more_button.click()
        loadButtonClicked = True

        print("Load Button clicked successfully.")
        time.sleep(5)  # Give adequate time for new content to load
        return True
    except NoSuchElementException:
        print("Load More button not found or no more content to load!")
        return False
    except ElementClickInterceptedException:
        print("Load More button is not clickable or is covered by another element!")
        return False
    except TimeoutException:
        print("Timeout waiting for 'Load More' button to be clickable.")
        return False
    except Exception as e:
        print(f"Unexpected error while clicking 'Load More': {e}")
        return False

def scrape_projects():
    scraped_data = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-react-proj-card'))
        )
        projects = driver.find_elements(By.CLASS_NAME, 'js-react-proj-card')
        print(f"Found {len(projects)} project elements on the current page.")

        for project in projects:
            try:
                title_link_element = WebDriverWait(project, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.project-card__title'))
                )
                name = title_link_element.text
                link = title_link_element.get_attribute('href')

                description_element = WebDriverWait(project, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'p.pb3'))
                )
                description = description_element.text.strip() # .strip() to remove leading/trailing whitespace

                # Fallback if .text is empty for some reason, try innerText or textContent
                if not description:
                    description = description_element.get_attribute('innerText').strip() or \
                                  description_element.get_attribute('textContent').strip()

                founder_name_element = WebDriverWait(project, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'a.project-card__creator > span'))
                )
                founder_name = founder_name_element.text

                scraped_data.append({
                    'name': name,
                    'description': description,
                    'link': link,
                    'founder_name': founder_name
                })
            except TimeoutException:
                print("Timeout waiting for sub-elements (title, description, or founder) in a project card.")
                continue 
            except NoSuchElementException:
                print("Skipping a project card due to missing expected sub-element (e.g., name, description, founder).")
                continue
            except Exception as e:
                print(f"An unexpected error occurred while processing a project card: {e}")
                continue 
    except Exception as e:
        print(f"Error during initial wait or finding project cards: {e}")
    return scraped_data

all_data = []
max_entries = 5000  # Adjust the number of entries you want to scrape

while len(all_data) < max_entries:
    if time.time() - start_time > timeout_seconds:
        print(f"Timeout of {timeout_seconds} seconds reached. Exiting scraping process.")
        break

    new_data = scrape_projects()  # Scrape the current page
    all_data.extend(new_data)
    
    # Remove duplicates by description
    all_data = list({entry['description']: entry for entry in all_data}.values())
    print(f"Scraped {len(all_data)} unique entries so far...")

    # Break if no "Load More" button is found or it's not clickable
    if not click_load_more_button():
        print("No more 'Load More' button or it's not clickable. Finishing scraping.")
        break

# Save results to a JSON file
try:
    with open("results.json", "w", encoding="utf-8") as file:
        json.dump(all_data, file, indent=4, ensure_ascii=False)
    print(f"Scraped data saved to 'results.json'. Total entries: {len(all_data)}")
except Exception as e:
    print(f"Error saving data to file: {e}")

# Close the browser
driver.quit()