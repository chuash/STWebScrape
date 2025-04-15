import csv
import os
import pandas as pd
import utils

# Get the current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# Declare the filepath for the master csv files
master_filepath = os.path.join(current_dir, "ST_Listing_Content_Master.csv")
master_filter_filepath = os.path.join(current_dir, "ST_Filter_Master.csv")

# create the relevant csv file with headers, if not present
if not os.path.exists(master_filepath):
    with open(master_filepath, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Datetime", "Title", "URL", "Content"])
        writer.writeheader()

if not os.path.exists(master_filter_filepath):
    with open(master_filter_filepath, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["Datetime", "Title", "URL", "Content", "kw_relevance", "llm_relevance", "Summary"])
        writer.writeheader()

if __name__ == '__main__':

    try:

        # Read in the scraped news contents, news listings, and filtered urls master
        df = pd.read_csv('ST_Details.csv')
        df1 = pd.read_csv('ST_Listing.csv')
        df2 = pd.read_csv('ST.csv')

        # Combine the listings with news content and sort by date in ascending order
        df3 = pd.merge(df1, df, how='inner', on='URL')[['Datetime', 'Title', 'URL', 'Content']]
        sorted_df3 = df3.sort_values(by=["Datetime"], ascending=True)
        # Save to file
        sorted_df3.to_csv('ST_Listing_Content_Master.csv', mode='a', header=False, index=False)

        # sort the filtered urls master in ascending date
        if len(df2) > 0:
            sorted_df2 = df2.sort_values(by=["Datetime"], ascending=True)
            sorted_df2.to_csv("ST_Filter_Master.csv", mode='a', header=False, index=False)

        # Remove the files no longer required
        os.remove('ST_Details.csv')
        os.remove('ST_Listing.csv')
        os.remove('ST.csv')

    except (Exception, BaseException) as e:
        print(f"Error: {str(e)}")
