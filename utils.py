# importing relevant libraries
import csv
import os
import re
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import relativedelta
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from playwright.sync_api import sync_playwright, BrowserContext, Playwright, Page
from typing import IO

# load environment variables
load_dotenv()
username = os.getenv("ST_USR")
password = os.getenv("ST_PW")
Groq_model = os.getenv("GROQ_MODEL_NAME")
OAI_model = os.getenv("OPENAI_MODEL_NAME")
Groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
OAI_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Defining list of user agents for rotation purpose. Update this list where necessary
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Define CCCS keywords
keyword_dict = {
    "Competition Act": [
        "competition and consumer commission of singapore",
        "competition act",
        "competition watchdog",
        "fee guidelines",
        "price fixing",
        " cartel",
        "unfair practice",
        "unfair competition",
        " monopoly ",
        "abuse of dominance",
        "market power",
        "market share",
        "bid rigging",
        "competitive business practice",
        " merger",
        " acquisition",
        "joint venture",
        "block exemption",
        "price war",
        "price regulation",
        "price transparency",
        "antitrust",
        "anti competitive",
        "anticompetitive",
        "price increase",
        "price hike",
        "fee hike",
        "fee surcharge",
        " collusion",
        "coordinated conduct",
        "exclusivity clause",
        " tying ",
        " bundling",
        "bundle product",
        "exclusive agreement",
        "refusal to supply",
        "predatory pricing",
        "level playing field",
        "barriers to entry",
        "exchange sensitive information",
        "smaller players in the market",
        "airline alliance",
        "asean experts group on competition",
        " aegc ",
        " cccs ",
    ],
    "Fair trading (Consumer Protection Fair Trading Act)": [
        "false claim",
        "seller take advantage",
        "pressure selling",
        "pressure sales",
        "false representation",
        "false gift",
        "misrepresenting",
        "misrepresentation",
        "unsolicited goods",
        "unsolicited service",
        "retailer insolvency",
        " prepayment",
        "consumers association of singapore",
        " casetrust ",
        "charge fairly",
        " overcharging",
        "price discrepancy",
        "motorcar dealer",
        "lock-in period",
        "unfair trading",
        "unfair trade",
        "consumer harm",
        "hidden in fine print",
        "hidden charges",
        "consumer protection fair trading act",
        "fair trading",
        "fake review",
        "misleading claim",
    ],
    "Beauty Industry": [
        "beauty industry",
        "spa wellness",
        "pay upfront",
        "consumer cheated",
        "false product claim",
        "package refund",
    ],
    "Transport/Ride-Hailing Industry/Online Food Delivery": [
        "ride hailing",
        " uber",
        "comfortdelgro",
        "retail petrol",
        "shut off by main player",
        "refusal to add to platform",
        "conflict between operators",
        "point to point passenger transport industry bill",
        "school bus fare",
        "grab",
        " gojek",
        " deliveroo",
        "online food delivery",
        "food delivery service",
        "shared kitchen",
    ],
    "E-commerce/online shopping/Online hotel booking": [
        "e commerce",
        " ecommerce",
        "disruptive technologies",
        "online travel booking",
        "drip pricing",
        "digital market ",
        "digital markets",
        "digital platform",
        "competition issue",
        "tech giant",
        "technology giant",
        "network effect",
        "multi sided",
        "multi homing",
        " dominance",
        "digital competition",
        "stifling competition",
        "online ticketing",
        "ticketing panel model",
        "subscription trap",
        "false discount information",
        "inaccurate discount information",
        "pre ticked box",
    ],
}


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    # Defining __str__ so that print() returns this
    def __str__(self):
        return self.value


def date_input() -> tuple[datetime, datetime]:
    try:
        startdate = input("Enter start date in dd/mm/yyyy format (e.g. 01/01/2025):")
        enddate = input("Enter end date in dd/mm/yyyy format (e.g. 01/01/2025):")
        startdate = datetime.strptime(startdate, "%d/%m/%Y")
        enddate = datetime.strptime(enddate, "%d/%m/%Y")
        today = datetime.today()
        # Check for typo error in year
        if startdate.year != today.year or enddate.year != today.year:
            raise MyError("Wrong year selected, please check!")
        # Check for swapping of start and end dates
        if startdate > enddate:
            raise MyError("Start date cannot be later than end date, please check!")
        if startdate > today or enddate > today:
            raise MyError(
                "Start date or end date cannot be later than current date, please check!"
            )
        # Check that the input start date is within 10 days from current date
        # After all, Straits Times Online only archives 11-12 days worth of Singapore news,
        # therefore to be safe, fix the max at 10 days.
        if relativedelta.relativedelta(today, startdate).days + 1 > 10:
            raise MyError("Start date cannot be more than 10 days from current date")
        return (startdate, enddate)

    except (MyError, Exception, BaseException) as e:
        raise MyError(f"Error : {str(e)}")


def get_news_listing(
    category: str, user_agents: list, startdate: datetime, enddate: datetime
) -> list:
    i = 0
    listing = []
    try:
        # Straits Times Online only keeps 30 pages of archive
        while i <= 30:
            url = f"https://www.straitstimes.com/{category}/latest?page={i}"
            # randomising the user agent to be added to the request header
            headers = {"User-Agent": random.choice(user_agents)}
            response = requests.get(url, headers=headers)
            # capturing response error, if any
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            # Getting all the news listings on each page
            content = soup.find_all("div", class_="card-body")
            # Extract the title, news article url and date of publishing for each news listing
            temp = [
                {
                    "Title": ele.find("h5", class_="card-title").get_text().strip(),
                    "URL": "https://www.straitstimes.com" + ele.find("a").get("href"),
                    "Datetime": datetime.strptime(
                        ele.find("div", class_="card-time").get_text().strip(),
                        "%b %d, %Y, %I:%M %p",
                    ),
                }
                for ele in content
            ]
            # if the date of publishing of the last news listing on a page is later than the user provided end date, ignore all the news listing
            # on that page
            if temp[-1]["Datetime"] > enddate + timedelta(minutes=1439):
                pass
            # if the date of publishing of the first news listing on a page is earlier than the user provided start date, ignore all the news listing
            # on that page and stop iterating through the pages
            elif temp[0]["Datetime"] < startdate:
                break
            else:
                listing.extend(temp)
            i += 1

        # Filter only for news listings published within the user provided start and end dates
        filtered_listing = [
            dic
            for dic in listing
            if dic["Datetime"] >= startdate
            and dic["Datetime"] <= enddate + timedelta(minutes=1439)
        ]

        return filtered_listing

    except requests.exceptions.HTTPError as errh:
        raise MyError(f"Request http Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        raise MyError(f"Request connection error: {errc}")
    except requests.exceptions.Timeout as errt:
        raise MyError(f"Request timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        raise MyError(f"Request related error : {err}")
    except (MyError, Exception, BaseException) as e:
        raise MyError(f"Error : {str(e)}")


def scrape(
    completed_links_filepath: str,
    context: BrowserContext,
    url_tup: tuple[int, str],
    username: str,
    password: str,
    ad_handling: bool = False,
    subscription_handling: bool = False,
    login: bool = False,
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
            # cancel_cnt = await page.locator("#ei-btn-cancel").count()
            # if cancel_cnt > 0:
            #    print("Subscription pop-up detected. Proceed to reject")
            #    await page.locator("#ei-btn-cancel").click()

        # If login is required, see if already log-in, if not log in
        if login:
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
        if content == " " or content == "" or content is None:
            raise MyError(f"No content extracted for {url_tup[1]}")

        # Update the completed urls csv file
        with open(
            completed_links_filepath, mode="a", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=["URL_Index", "URL", "Content"])
            writer.writerow(
                {"URL_Index": str(url_tup[0]), "URL": url_tup[1], "Content": content}
            )

        print(f"Content of URL_{str(url_tup[0])} saved and record updated")
        page.close()

    except (MyError, Exception, BaseException) as e:
        raise MyError(f"Error : {str(e)}")


def save_pdf(pdf_folderpath: str, page: Page, url_tup: tuple[int, str]) -> IO:
    # Save the pdf of the entire page, then close the page
    # Generates a pdf with "screen" media type.
    page.emulate_media(media="screen")
    page.pdf(
        path=os.path.join(pdf_folderpath, f"URL_{url_tup[0]}.pdf"),
        display_header_footer=True,
        format="A4",
        margin={
            "top": "0.99in",
            "bottom": "0.99in",
            "left": "0.99in",
            "right": "0.99in",
        },
        print_background=True,
    )


def textclean(text: str) -> str:
    # to lowercase
    text = text.lower()
    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # remove extra whitespaces
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def kw_search(text: str, orgi_text: str, keyword_dict: dict) -> tuple:
    matched = []
    for topic in keyword_dict:
        found_kw = [ele for ele in keyword_dict[topic] if ele in text and ele != "grab"]
        if "Transport" in topic and "Grab" in orgi_text:
            found_kw.append("grab")
        if len(found_kw) > 0:
            matched.append({topic: found_kw})
    if len(matched) > 0:
        return ("Yes", matched)
    else:
        return ("No", "No matching keywords")


def llm_check(client: Groq | OpenAI, sys_msg: str, user_msg: str,
              keyword_dict: dict, news: str, model: str = "llama-3.3-70b-versatile",
              temperature: int = 0, top_p: int = 1, max_tokens: int = 1024):
    chat_completion = client.chat.completions.create(
        messages=[
            # Sets system message. This sets the behavior of the
            # assistant and can be used to provide specific instructions for
            # how it should behave throughout the conversation.
            {
             "role": "system",
             "content": f"{sys_msg}" + f"<keywords> {keyword_dict} </keywords>"
            },
            # Set a user message for the assistant to respond to.
            {
             "role": "user",
             "content": f"{user_msg}" + f"<news> {news} </news>",
            }
        ],

        # The language model which will generate the completion.
        model=model,

        # Controls randomness: lowering results in less random completions.
        # As the temperature approaches zero, the model will become deterministic
        # and repetitive.
        temperature=temperature,

        # The maximum number of tokens to generate. Requests can use up to
        # 32,768 tokens shared between prompt and completion.
        max_completion_tokens=max_tokens,

        # Controls diversity via nucleus sampling: 0.5 means half of all
        # likelihood-weighted options are considered.
        top_p=top_p,

        # A stop sequence is a predefined or user-specified text string that
        # signals an AI to stop generating content, ensuring its responses
        # remain focused and concise. Examples include punctuation marks and
        # markers like "[end]".
        stop=None,

        # If set, partial message deltas will be sent.
        stream=False,
    )

    return chat_completion.choices[0].message.content
