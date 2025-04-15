import csv
import os
import pandas as pd
import utils

# Get the current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
# Declare the filepath for the csv file that would capture the successfully filtered URLs
filtered_links_filepath = os.path.join(current_dir, "ST.csv")

# create the filtered urls csv file with headers, if not present
if not os.path.exists(filtered_links_filepath):
    with open(filtered_links_filepath, mode="a", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "Datetime",
                "Title",
                "URL",
                "Content",
                "kw_relevance",
                "llm_relevance",
                "Summary",
            ],
        )
        writer.writeheader()

sys_msg = f"""You are an experienced officer of Competition and Consumer Commission of Singapore (CCCS). CCCS upholds Singapore Competition Act to prevent anti-competitive practices
amongst companies operating in Singapore. It also protects consumers against unfair business practices in Singapore under Consumer Protection (Fair Trading) Act. A dictionary of keywords is enclosed below within 
<keywords> tags. Each dictionary key represents a topic and the corresponding value represents list of keywords related to topic. You are to help filter for news articles 
relevant to CCCS, and summarise these relevant articles. Text summarisation capturing key points is your forte."""

user_msg = """Review the text enclosed below within <news> tags and assess if the news is relevant to CCCS, based on the dictionary of keywords. If relevant, i) reply "Yes",
ii) indicate ONLY the topic(s) and keyword(s) you use to substantiate your answer, iii) summarise the text. Use the format ```(Yes, {'topic': list of keywords}, text summmary)```.
If irrelevant, reply using the format ```(No, )```. Strictly adhere to the response formats."""

if __name__ == "__main__":

    try:

        # Read in the scraped news contents and news listings
        df = pd.read_csv("ST_Details.csv")
        df1 = pd.read_csv("ST_Listing.csv")

        # convert news content to lower case, remove punctuation and extra whitespaces
        df["Content_clean"] = df["Content"].apply(lambda text: utils.textclean(text))

        # filter the news content that contains CCCS's monitoring keywords
        df["kw_relevance"] = df.apply(
            lambda x: utils.kw_search(
                x["Content_clean"], x["Content"], utils.keyword_dict
            ),
            axis=1,
        )
        df = df[df["kw_relevance"].apply(lambda x: "Yes" in x)].copy()

        print(f"Number of news articles with detected keywords is {str(df.shape[0])}")
        entry = input('Enter "Y" to proceed, else "N" to cancel ')
        if entry.lower() == "y":

            # Pass the filtered keyword filtered contents to LLM to confirm relevance to CCCS
            df["llm_relevance"] = df.apply(
                lambda x: utils.llm_check(
                    client=utils.OAI_client,
                    sys_msg=sys_msg,
                    user_msg=user_msg,
                    keyword_dict=utils.keyword_dict,
                    news=x["Content"],
                    model=utils.OAI_model
                ),
                axis=1,
            )

            # Combine with news listings
            df2 = pd.merge(df1, df, how="inner", on="URL")[
                ["Datetime", "Title", "URL", "Content", "kw_relevance", "llm_relevance"]
            ]
            # Extract the summary
            df2["Summary"] = df2["llm_relevance"].apply(
                lambda x: x.split("},")[1].replace(")", "") if "Yes" in x else ""
            )
            # Save to file
            df2.to_csv("ST.csv", mode="a", header=False, index=False)

    except (Exception, BaseException) as e:
        print(f"Error: {str(e)}")
