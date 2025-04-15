# Importing relevant libraries
import csv
import os
import pandas as pd
import random
import utils
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Get the current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# Declare the filepath for the csv file that would capture the successfully scraped URLs
completed_links_filepath = os.path.join(current_dir, "ST_Details.csv")
# Declare the directory that would contain the url pdfs
pdf_folderpath = os.path.join(current_dir, "pdfs")

# create the screenshot folder, if not present
os.makedirs(pdf_folderpath, exist_ok=True)
# create the completed urls csv file with headers, if not present
if not os.path.exists(completed_links_filepath):
    with open(completed_links_filepath, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["URL_Index", "URL", "Content"])
        writer.writeheader()

# Define the headers parts to update Playwright default headers so as to "humanise" the headers
extra_headers = {
    'sec-ch-ua': '\'Not A(Brand\';v=\'99\', \'Google Chrome\';v=\'121\', \'Chromium\';v=\'121\'',
    'user-agent': random.choice(utils.user_agents),
    'accept-Language': 'en-US,en;q=0.9'
}


if __name__ == '__main__':
    try:
        # Extract the list of urls from ST_Listing.csv
        df = pd.read_csv('ST_Listing.csv')
        urls = list(zip(df.index.to_list(), df.URL.to_list()))

        # Extract the ST section from url
        section = df.URL.to_list()[0].replace('https://www.straitstimes.com/', '').split('/')[0]
        if section not in ['singapore', 'business', 'opinion']:
            raise utils.MyError("Error: Invalid Straits Times section, please check")
        else:
            login_state = False
            if section == 'opinion':
                print('Scraping ST opinion section, login required')
                login_state = True
            # Scrape the news content
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False)
                context = browser.new_context(extra_http_headers=extra_headers)
                for ele in urls:
                    utils.scrape(completed_links_filepath, context, ele, utils.username,
                                 utils.password, ad_handling=True, subscription_handling=True, login=login_state)
                context.close()
                browser.close()

    except utils.MyError as e:
        print(str(e))
    except (Exception, BaseException) as e:
        print(f"Error: {str(e)}")
