from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import lxml
import pandas as pd
import re
from datetime import datetime
from selenium.webdriver.common.keys import Keys


search_box_text = 'sports shoes for women'
website_link = 'https://www.flipkart.com/'


session_start_time = datetime.now().time()
print(f"Session Start Time: {session_start_time} ---------------------------> ")


driver = webdriver.Chrome()
driver.get(website_link)
driver.maximize_window()

print('Waiting for search input...')
search_input = WebDriverWait(driver, 120).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '[autocomplete="off"]')))

print('Typing in search input...')
search_input.send_keys(search_box_text)

print('Submitting search form...')
search_input.send_keys(Keys.RETURN)

print('Waiting for search results...')
WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[target="_blank"]')))

print('Collecting pagination links...')


all_pagination_links = []

first_page = driver.find_elements(By.CSS_SELECTOR, 'nav a')[0]
first_page_link = first_page.get_attribute('href')
all_pagination_links.append(first_page_link)

for i in range(2, 26):
    new_pagination_link = first_page_link[: -1] + str(i)
    all_pagination_links.append(new_pagination_link)

print('Pagination Links Count:', len(all_pagination_links))
print("All Pagination Links: ", all_pagination_links)

print("Collecting Product Detail Page Links")
all_product_links = []

for link in all_pagination_links:
    driver.get(link)

    WebDriverWait(driver, 120).until(lambda d: d.execute_script('return document.readyState') == 'complete')


    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CLASS_NAME, 'rPDeLR')))

    all_products = driver.find_elements(By.CLASS_NAME, 'rPDeLR')
    all_links = [element.get_attribute('href') for element in all_products]

    print(f"{link} Done ------>")

    all_product_links.extend(all_links)

print('All Product Detail Page Links Captured: ', len(all_product_links))


df_product_links = pd.DataFrame(all_product_links, columns=['product_links'])

df_product_links = df_product_links.drop_duplicates(subset=['product_links'])

print("Total Product Detail Page Links", len(df_product_links))
df_product_links.to_csv('flipkart_product_links.csv', index=False)

driver.close()
session_end_time = datetime.now().time()
print(f"Session End Time: {session_end_time} ---------------------------> ")


session_start_time = datetime.now().time()
print(f"Session Start Time: {session_start_time} ---------------------------> ")


df_product_links = pd.read_csv("flipkart_product_links.csv")


df_product_links = df_product_links.head(10)

all_product_links = df_product_links['product_links'].tolist()
print("Collecting Individual Product Detail Information")


driver = webdriver.Chrome()

complete_product_details = []
unavailable_products = []
successful_parsed_urls_count = 0
complete_failed_urls_count = 0
for product_page_link in all_product_links:

    try:
        driver.get(product_page_link)


        WebDriverWait(driver, 120).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[target="_blank"]')))


        try:
            product_status = driver.find_element(By.CLASS_NAME, 'Z8JjpR').text
            if product_status == 'Currently Unavailable' or product_status == 'Sold Out':
                unavailable_products.append(product_page_link)
                successful_parsed_urls_count += 1
                print(f"URL {successful_parsed_urls_count} completed --->")
        except:
            pass


        brand = driver.find_element(By.CLASS_NAME, 'mEh187').text


        title = driver.find_element(By.CLASS_NAME, 'VU-ZEz').text
        title = re.sub(r'\s*\([^)]*\)', '', title)  # removing data withing parenthesis (color information)


        price = driver.find_element(By.CLASS_NAME, 'Nx9bqj').text
        price = re.findall(r'\d+', price)
        price = ''.join(price)


        try:
            discount = driver.find_element(By.CLASS_NAME, 'UkUFwK').text
            discount = re.findall(r'\d+', discount)
            discount = ''.join(discount)
            discount = int(discount) / 100
        except:
            discount = ''


        try:
            product_review_status = driver.find_element(By.CLASS_NAME, 'E3XX7J').text
            if product_review_status == 'Be the first to Review this product':
                avg_rating = ''
                total_ratings = ''
        except:
            avg_rating = driver.find_element(By.CLASS_NAME, 'XQDdHH').text
            total_ratings = driver.find_element(By.CLASS_NAME, 'Wphh3N').text.split(' ')[0]
            # remove the special character
            if ',' in total_ratings:
                total_ratings = int(total_ratings.replace(',', ''))
            else:
                total_ratings = int(total_ratings)

        successful_parsed_urls_count += 1
        print(f"URL {successful_parsed_urls_count} completed *******")
        complete_product_details.append([product_page_link, title, brand, price, discount, avg_rating, total_ratings])
    except Exception as e:
        print(f"Failed to establish a connection for URL {product_page_link}:  {e}")
        unavailable_products.append(product_page_link)
        complete_failed_urls_count += 1
        print(f"Failed URL Count {complete_failed_urls_count}")


df = pd.DataFrame(complete_product_details,
                  columns=['product_link', 'title', 'brand', 'price', 'discount', 'avg_rating', 'total_ratings'])

df_duplicate_products = df[df.duplicated(subset=['brand', 'price', 'discount', 'avg_rating', 'total_ratings'])]
df = df.drop_duplicates(subset=['brand', 'price', 'discount', 'avg_rating', 'total_ratings'])

df_unavailable_products = pd.DataFrame(unavailable_products, columns=['link'])


print("Total product pages scrapped: ", len(all_product_links))
print("Final Total Products: ", len(df))
print("Total Unavailable Products : ", len(df_unavailable_products))
print("Total Duplicate Products: ", len(df_duplicate_products))


df.to_csv('flipkart_product_data.csv', index=False)
df_unavailable_products.to_csv('unavailable_products.csv', index=False)
df_duplicate_products.to_csv('duplicate_products.csv', index=False)

driver.close()
session_end_time = datetime.now().time()
print(f"Session End Time: {session_end_time} ---------------------------> ")

