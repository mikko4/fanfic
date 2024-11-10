import re
import time
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_date_range_from_string(mos):
    # Extract start and end values using regex
    match = re.match(r"(\d+)-(\d+)\+months", mos)
    if not match:
        raise ValueError("Invalid format. Expected format is 'START-END+months'")

    start_months_ago = int(match.group(1))
    end_months_ago = int(match.group(2))

    # Get today's date
    today = datetime.today()

    # Calculate the start and end dates
    start_date = today - timedelta(days=start_months_ago * 30)
    end_date = today - timedelta(days=end_months_ago * 30)

    # Return the date range as a string
    return f"{end_date.strftime('%Y-%m-%d')} to {start_date.strftime('%Y-%m-%d')}"


class ProxyRotator:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_proxy_index = 0

    def get_driver(self):
        """Create a WebDriver instance with the current proxy and rotate to the next one."""
        # Get the current proxy
        host = self.proxies[self.current_proxy_index][0]
        port = self.proxies[self.current_proxy_index][1]

        # Update the index to the next proxy
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)

        options = Options()
        options.set_preference("network.proxy.type", 1)
        options.set_preference("network.proxy.http", host)
        options.set_preference("network.proxy.http_port", port)
        options.set_preference("network.proxy.ssl", host)
        options.set_preference("network.proxy.ssl_port", port)
        options.set_preference("network.proxy.no_proxies_on", "")

        options.add_argument("-headless")

        # Create and return a new WebDriver instance
        driver = webdriver.Firefox(
            options=options,
        )

        return driver


def custom_sleep(amount=0.1):
    time.sleep(amount)


def clear_tos(driver):
    driver.get("https://archiveofourown.org/works/search?work_search%5Bquery%5D=")
    # Wait for the checkbox to be clickable
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "tos_agree")))

    # Check the #tos_agree checkbox
    checkbox = driver.find_element(By.ID, "tos_agree")
    checkbox.click()

    # Wait for the accept button to be clickable
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "accept_tos")))

    # Click the #accept_tos button
    accept_button = driver.find_element(By.ID, "accept_tos")
    accept_button.click()


# Function to scrape a single page
def scrape_page(driver, page_link):
    work_details = []
    num_empty_works = 0
    driver.get(page_link)
    custom_sleep()

    works_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "work.index.group"))
    )

    # Find all the work items
    work_items = works_list.find_elements(By.CSS_SELECTOR, "li.work")

    # Initialize a list to store the links
    work_links = []

    # Iterate over each work item to extract the link
    for work in work_items:
        try:
            link_element = work.find_element(
                By.CSS_SELECTOR, "div.header.module h4.heading a"
            )
            work_link = (
                link_element.get_attribute("href")
                + "?view_full_work=true&view_adult=true"
            )
            work_links.append(work_link)
        except Exception as e:
            print(e)
            continue

    for work in work_links:
        driver.get(work)

        work_info = {"url": work.replace("?view_full_work=true&view_adult=true", "")}
        # work_info = {"url": work}

        # Wait for the work page to load
        custom_sleep()

        # Get the metadata
        try:
            meta_dl = driver.find_element(By.CSS_SELECTOR, "dl.work.meta.group")
            dt_elements = meta_dl.find_elements(By.TAG_NAME, "dt")
            dd_elements = meta_dl.find_elements(By.TAG_NAME, "dd")
            metadata = {
                dt.text[:-1]: dd.text for dt, dd in zip(dt_elements, dd_elements)
            }
            work_info["metadata"] = metadata
        except:
            work_info["metadata"] = None

        try:
            chapter_texts = driver.find_elements(By.CSS_SELECTOR, "div.userstuff")
            full_text = ""
            for chapter in chapter_texts:
                soup = BeautifulSoup(chapter.get_attribute("outerHTML"), "html.parser")
                chapter_text = soup.get_text()
                full_text += chapter_text + "\n\n"
            if not bool(full_text.strip()):
                print(work)
                num_empty_works += 1
            # full_text = get_all_chapter_text(driver)
            work_info["text"] = full_text
        except:
            work_info["text"] = None
            num_empty_works += 1

        work_details.append(work_info)

    return work_details, num_empty_works


def make_csv(work_details, name):

    if not work_details:
        print("No data")
        return

    # Convert the list of work details to a DataFrame
    df = pd.DataFrame(work_details)

    # Define the combinations of columns
    combine_columns = {
        "Relationships": ["Relationship", "Relationships"],
        "Characters": ["Character", "Characters"],
        "Categories": ["Category", "Categories"],
        "Fandom": ["Fandom", "Fandoms"],
        "Archive Warnings": ["Archive Warning", "Archive Warnings"],
    }

    # Extract all unique keys from the dictionary column
    all_keys = set()
    for d in df["metadata"]:
        if d:
            all_keys.update(d.keys())

    # Create new columns for each unique key
    for key, aliases in combine_columns.items():
        df[key] = df["metadata"].apply(
            lambda x: next((x[k] for k in aliases if x and k in x), None)
        )

        # Drop the column if it is entirely blank (i.e., all values are None)
        if df[key].isnull().all():
            df.drop(columns=[key], inplace=True)

    always_cols = [
        "Bookmarks",
        "Published",
        "Updated",
        "Hits",
        "Words",
        "Chapters",
        "Comments",
        "Kudos",
    ]
    for col in always_cols:
        if col not in df.columns:
            df[col] = None

    # Add any remaining keys that were not combined
    for key in all_keys:
        if key not in [col for cols in combine_columns.values() for col in cols]:
            df[key] = df["metadata"].apply(lambda x: x.get(key, None) if x else None)

    df = df.drop(columns=["metadata"])
    if "Stats" in df.columns:
        df = df.drop(columns=["Stats"])

    fixed = ["url", "text"]
    # Extract and sort the remaining columns
    sorted_columns = sorted([col for col in df.columns if col not in fixed])

    # Concatenate the fixed columns with the sorted columns
    new_order = fixed + sorted_columns
    df = df[new_order]

    # Save the DataFrame to a CSV file
    df.to_csv(name + ".csv", index=False, encoding="utf-8")
    # df.to_excel(name + ".xlsx", index=False)


def scrape_all_pages(start_page, end_page, base_query):
    work_details = []

    try:
        driver = proxy_rotator.get_driver()
        driver.get(base_query)
        custom_sleep(2)
        # Get the page source
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")

        # Find the pagination section
        pagination = soup.find("ol", class_="pagination actions")

        # Get the last page number
        pages = pagination.find_all("li")

        num_pages = int(pages[-2].text.strip())
        print(num_pages)
        driver.quit()

    except Exception as e:
        print("Error determining number of pages", e)
        return

    for p in range(start_page, end_page + 1):
        for i in range(5):
            try:
                driver = proxy_rotator.get_driver()
                page_link = base_query + f"&page={p}"
                page_works, num_empty_works = scrape_page(driver, page_link)
                break
            except Exception as e:
                print(f"Attempt {i}: An error occurred:", e)
                print(
                    f"Using proxy: {proxy_rotator.proxies[proxy_rotator.current_proxy_index]}"
                )
                custom_sleep(2)
                driver.quit()

        if not page_works:
            print(f"Could not scrape page {p}. Continuing.")
            continue

        if (num_empty_works / len(page_works) * 100) != 0:
            print(f"Page {p}: {num_empty_works / len(page_works) * 100}% missing works")
        work_details += page_works
        if p % 20 == 0:
            print(f"Page {p}")
        if p % 100 == 0:
            make_csv(work_details, f"{start_num}-{end_page}")
        driver.quit()

    return work_details


PROXIES = [
    ("us-ca.proxymesh.com", 31280),
    ("us-wa.proxymesh.com", 31280),
    ("us-il.proxymesh.com", 31280),
    ("fr.proxymesh.com", 31280),
    ("nl.proxymesh.com", 31280),
    ("au.proxymesh.com", 31280),
    ("sg.proxymesh.com", 31280),
    ("de.proxymesh.com", 31280),
    ("jp.proxymesh.com", 31280),
    ("sg.proxymesh.com", 31280),
    ("us-tx.proxymesh.com", 31280),
    ("us-dc.proxymesh.com", 31280),
]

START_MONTH = 42
END_MONTH = 48

if __name__ == "__main__":
    proxy_rotator = ProxyRotator(PROXIES)

    mos = f"{START_MONTH}-{END_MONTH}+months"

    base_query = f"https://archiveofourown.org/works/search?work_search%5Bquery%5D=%28%22Fluff%22+OR+%22Alternate+Universe%22+OR+%22Angst%22+OR+%22Hurt%2FComfort%22+OR+%22Family%22+OR+%22Friendship%22+OR+%22Not+Canon+Compliant%22+OR+%22Humor%22+OR+%22Alternate+Universe+-+Canon+Divergence%22%29++NOT+%28%22Sexual+Content%22+OR+%22Sex%22+OR+%22Smut%22+OR+%22Oral+Sex%22+OR+%22BDSM%22+OR+%22Porn%22+OR+%22Anal%22+OR+%22Anal+Sex%22+OR+%22Fingerfucking%22+OR+%22Non-Consensual%22+OR+%22Plot+What+Plot%2FPorn+Without+Plot%22+OR+%22Dom%2Fsub%22+OR+%22Blow+Jobs%22+OR+%22Consent%22+OR+%22Rape%2FNon-con+Elements%22+OR+%22Vaginal%22+OR+%22Bodily+Fluids%22+OR+%22Kinks%22+OR+%22Homosexuality%22+OR+%22Cuddling+%26+Snuggling%22+OR+%22Child+Abuse%22+OR+%22Gay%22+OR+%22Familial+Abuse%22+OR+%22Fluff+and+Smut%22+OR+%22Roughness%22%29&work_search%5Btitle%5D=&work_search%5Bcreators%5D=&work_search%5Brevised_at%5D={mos}&work_search%5Bcomplete%5D=T&work_search%5Bcrossover%5D=&work_search%5Bsingle_chapter%5D=0&work_search%5Bword_count%5D=&work_search%5Blanguage_id%5D=en&work_search%5Bfandom_names%5D=&work_search%5Brating_ids%5D=&work_search%5Bcharacter_names%5D=&work_search%5Brelationship_names%5D=&work_search%5Bfreeform_names%5D=&work_search%5Bhits%5D=%3E2000&work_search%5Bkudos_count%5D=&work_search%5Bcomments_count%5D=&work_search%5Bbookmarks_count%5D=&work_search%5Bsort_column%5D=_score&work_search%5Bsort_direction%5D=desc&commit=Search"
    # base_query = f"https://archiveofourown.org/works/search?work_search[query]=&work_search[hits]=%3E100&work_search[language_id]=en"

    start_num = 1001
    end_num = 2000
    work_details = scrape_all_pages(start_num, end_num, base_query)
    # csv_name = get_date_range_from_string(mos)
    csv_name = f"{start_num}-{end_num}"
    make_csv(work_details, csv_name)

    print("Scraping complete. Data saved to csv.")
