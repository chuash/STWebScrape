import asyncio
import csv
import os
import re
import random
import utils
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, BrowserContext, Playwright, Page


urls = [(30, 'https://www.straitstimes.com/singapore/japan-can-play-a-larger-security-role-in-the-region-amid-uncertainties-said-sm-lee-hsien-loong'),
        (31, 'https://www.straitstimes.com/singapore/2-rsaf-c-130-aircraft-deliver-over-9-tonnes-of-aid-to-myanmar-quake-victims'),
        (32, 'https://www.straitstimes.com/opinion/spiking-the-ghost-gun-how-singapore-can-foil-3d-printed-firearms'),
        (33, 'https://www.straitstimes.com/singapore/roving-exhibition-to-celebrate-60th-anniversary-of-singapore-armed-forces'),
        (34, 'https://www.straitstimes.com/singapore/courts-crime/victims-lost-at-least-614k-to-scammers-exploiting-mas-e-service-portal-since-march'),
 ]

# Define the headers parts to update Playwright default headers so as to "humanise" the headers
extra_headers = {
    'sec-ch-ua': '\'Not A(Brand\';v=\'99\', \'Google Chrome\';v=\'121\', \'Chromium\';v=\'121\'',
    'user-agent': random.choice(utils.user_agents),
    'accept-Language': 'en-US,en;q=0.9'
}

# load environment variables
load_dotenv()
username = os.getenv("ST_USR")
password = os.getenv("ST_PW")

async def main_backup():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(extra_http_headers=extra_headers)
        page = await context.new_page()
        
        # open the target web page and add the referrer header
        await page.goto('https://www.straitstimes.com/singapore/politics/election-spotlight-race-heats-up-in-tampines-as-possible-4-way-fight-looms',
                        wait_until='domcontentloaded', referer='https://www.google.com/',
                        timeout=60000)

        await asyncio.sleep(5)

        # Setup the handler to remove advertisement.
        async def ad_handler():
            print("Advertisement detected. Proceed to reject")
            html = await page.content()
            button = re.compile(r"btn_close_\d{6}_\d{13}").findall(html)
            await page.locator('#'+button[0]).click()
        await page.add_locator_handler(page.get_by_text("Advertisement"),
                                       ad_handler)
        
        # Check if the popup to encourage subscription appears, if so, click to reject
        async def handler(locator):
            print("Subscription pop-up detected. Proceed to reject")
            await locator.click()
        await page.add_locator_handler(page.locator("#ei-btn-cancel"), handler, times=1)
        
        content = await page.locator(".paragraph-base").all_inner_texts()
        content = ' '.join(content)
        print(content)
          
        # Check for presence of LOG IN, if so, click to log in
#        item = await page.get_by_text('LOG IN', exact=True).count()
#        if item > 0:
#           print("Log in detected.")
#            await page.get_by_text('LOG IN', exact=True).click(timeout=60000)
#            await page.locator("#IDToken1").fill(username)
#            await page.locator("#IDToken2").fill(password)
#            await asyncio.sleep(1)
#            await page.locator("#btnLogin").click()
    
#        await asyncio.sleep(25)
        
#        await page.goto('https://www.straitstimes.com/singapore/roti-eggs-and-kopi-new-exhibition-celebrates-nanyang-breakfast',
#                        wait_until='commit', referer='https://www.google.com/', timeout=60000)
        
#        await asyncio.sleep(5)
        # Find all elements with class "paragraph-base" and extract text
#        content = await page.locator(".paragraph-base").all_inner_texts()
#        content = ' '.join(content)
#        print(content)
        await context.close()
        await browser.close()


async def main(urls: list[tuple], is_headless: bool = False):

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=is_headless)
        context = await browser.new_context(extra_http_headers=extra_headers)
        # create all tasks
        tasks = [asyncio.create_task(utils.scrape(completed_links_filepath, context, ele,
                                                  ad_handling=True, subscription_handling=True)) for ele in urls]
        # wait for each task to complete
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except utils.MyError as e:
                raise str(e)
            except (Exception, BaseException) as e:
                raise (f"Error: {str(e)}")
        await context.close()
        await browser.close()   


def scrape(
    context: BrowserContext,
    url_tup: tuple[int, str],
    ad_handling=False,
    subscription_handling=False,
) -> str:
    try:
        # navigate to the relevant url and wait till network response received and document started loading
        page = context.new_page()
        page.goto(
            url_tup[1],
            wait_until="domcontentloaded",
            referer="https://www.google.com/",
            timeout=30000,
        )  # set timeout to 30 sec

        # wait for 3 sec to give some buffer for the text content to be loaded and also not to load the server, in case of rate limiting
        page.wait_for_timeout(3000)

        # Check if advertisement appears, if so, click to close
        if ad_handling:
            # Setup the handler to remove advertisement.
            def ad_handler():
                html = page.content()
                button = re.compile(r"btn_close_\d{6}_\d{13}").findall(html)
                page.locator("#" + button[0]).click()

            page.add_locator_handler(page.get_by_text("Advertisement"), ad_handler)

        # Check if the popup to encourage subscription appears, if so, click to reject
        if subscription_handling:

            def handler(locator):
                locator.click()

            page.add_locator_handler(page.locator("#ei-btn-cancel"), handler, times=1)

        # see if already log-in, if not log in
        ele_cnt = page.get_by_text("LOG IN", exact=True).count()
        if ele_cnt > 0:
            print("Log in detected.")
            page.get_by_text("LOG IN", exact=True).click()
            page.locator("#IDToken1").fill(username)
            page.locator("#IDToken2").fill(password)
            page.wait_for_timeout(1000)
            page.locator("#btnLogin").click()
            page.wait_for_timeout(20000)
        
        # Find all elements with class "paragraph-base" and extract text
        content = page.locator(".paragraph-base").all_inner_texts()
        content = " ".join(content)
        print(content)

        print(f"Content of URL_{str(url_tup[0])} saved and record updated")
        page.close()

    except (Exception, BaseException) as e:
        print(f"Error : {str(e)}")



if __name__ == '__main__':
    #asyncio.run(main(urls))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(extra_http_headers=extra_headers)
        for ele in urls:
            scrape(context, ele,
                   ad_handling=True, subscription_handling=True)

        context.close()
        browser.close()
