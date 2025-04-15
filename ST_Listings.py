# Importing relevant libraries
import pandas as pd
import utils

listing = []
startdate, enddate = None, None


if __name__ == "__main__":
    try:
        section = input('Choose the Straits Times section to scrape from. Enter 1 for "singapore", 2 for "business", 3 for "opinion" ')
        if section == '1':
            category = ["singapore"]
        elif section == '2':
            category = ["business"]
        else:
            category = ["opinion"]

        while startdate is None and enddate is None:
            # Get user input on the start and end dates to extract the news listings
            startdate, enddate = utils.date_input()
            print(
                f"You have selected {startdate} as Start Date and {enddate} as End Date."
            )
            entry = input('Enter "Y" to proceed, else "N" ')
            if entry.lower() == "y":
                # Scrape the news listings
                for cat in category:
                    listing.extend(
                        utils.get_news_listing(cat, utils.user_agents, startdate, enddate)
                    )
            else:
                startdate, enddate = None, None
        # Saving as csv
        listing_df = pd.DataFrame.from_dict(listing)
        listing_df.to_csv('ST_Listing.csv')

    except utils.MyError as e:
        print(str(e))
    except (Exception, BaseException) as e:
        print(f"Error: {str(e)}")
