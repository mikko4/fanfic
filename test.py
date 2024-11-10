from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.firefox.options import Options
# from bs4 import BeautifulSoup

# host = "us-ca.proxymesh.com"
# port = 31280

# options = Options()
# options.set_preference("network.proxy.type", 1)
# options.set_preference("network.proxy.http", host)
# options.set_preference("network.proxy.http_port", port)
# options.set_preference("network.proxy.ssl", host)
# options.set_preference("network.proxy.ssl_port", port)
# options.set_preference("network.proxy.no_proxies_on", "")

# options.add_argument("-headless")


# dirver = webdriver.Firefox(options=options)

# url = "https://archiveofourown.org/works/58270381?view_full_work=true&view_adult=true"

# dirver.get(url)

# chapter_texts = dirver.find_elements(By.CSS_SELECTOR, "div.userstuff")
# print(len(chapter_texts))
# full_text = ""
# for chapter in chapter_texts:

#     # Use BeautifulSoup to parse and extract text
#     soup = BeautifulSoup(chapter.get_attribute("outerHTML"), "html.parser")
#     text = soup.get_text()
#     print(text[:1000])
#     # chapter_html = chapter.get_attribute("outerHTML")
#     print("===")

#     # print(chapter_html)  # Prints the full HTML of the element
#     full_text += chapter.text + "\n\n"

# print(full_text)
import pandas

pandas.options.display.max_columns = None
df = pandas.read_pickle("results/03.22-09.22/result_part_0_summary.pkl")
df.to_csv("test1.csv")
print(len(df))
# print(df)
