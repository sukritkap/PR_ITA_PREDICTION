from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

# Set up Selenium with headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
service = Service(chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

url ="https://www.canada.ca/en/immigration-refugees-citizenship/corporate/mandate/policies-operational-instructions-agreements/ministerial-instructions/express-entry-rounds.html"
driver.get(url)

try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")

    all_draws = []
    for row in rows[1:]:  # skip header
        cols = row.find_all("td")
        if len(cols) >= 5:
            draw = {
                "Round Number": cols[0].text.strip(),
                "Date": cols[1].text.strip(),
                "Type": cols[2].text.strip(),
                "Invitations": cols[3].text.strip(),
                "CRS Score": cols[4].text.strip()
            }
            all_draws.append(draw)

    df = pd.DataFrame(all_draws)
    df.to_csv("ircc_draw_history.csv", index=False)
    print("✅ All historical draw data saved to ircc_draw_history.csv")

except Exception as e:
    print("❌ Error while scraping:", e)

finally:
    driver.quit()
