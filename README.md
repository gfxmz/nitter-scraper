This Python script is designed to scrape data (tweets) from the Nitter platform (an alternative, less restrictive interface for Twitter/X) by utilizing the Selenium library for dynamic searching and content extraction. It is optimized for collecting data for multiple hashtags and is built with Machine Learning (ML) and Natural Language Processing (NLP) projects in mind, as it automatically adds feature engineering columns (e.g., text length, word count).

The script dynamically checks a list of available Nitter instances to increase the chance of successful data retrieval.

### Basic Syntax

python nitter-scraper.py <HASHTAG_1> <HASHTAG_2> ... [OPTIONS]

python nitter-scraper.py ukraine russia --max-tweets 200 --filename-prefix nawrocki

**Command Line Arguments**

Argument,Type,Default Value,Description
hashtags,List of strings,Required,List of hashtags to search for (without the # sign).
--max-tweets,Int,100,Maximum number of tweets to fetch for each hashtag.
--output-dir,String,data,Target directory for the CSV files.
--filename-prefix,String,tweets,"Prefix for the output CSV filenames (e.g., your last name)."
--delay,Float,5.0,Delay (in seconds) between processing consecutive hashtags.
--page-delay,Float,3.0,Delay (in seconds) between loading subsequent pages (scrolling).
--show-samples,Int,3,Number of sample tweets to display after the scraping process is finished.

### How the Script Works

1. Dynamic Nitter Instance Fetching
The script first attempts to fetch the current list of working Nitter instances from the official GitHub repository (get_nitter_instances function).

If dynamic fetching fails, a static fallback list is used. For each hashtag, the script iteratively attempts to use different Nitter instances until a working one is found and data is successfully retrieved.

2. Scraping and Data Cleaning
It uses Selenium in headless mode (without a visible browser window) to simulate user interaction and page scrolling.

It extracts key data: username, content, date, and interaction statistics (likes, retweets, replies).

The clean_text function is applied to remove links and excessive whitespace from the tweet content.

The parse_nitter_date function converts Nitter's relative (e.g., "5h", "2mo") and absolute date formats into the standard ISO format (%Y-%m-%d %H:%M:%S).

3. CSV Saving (ML Ready)
A separate CSV file is created for each hashtag. The filename format is: <prefix>_<hashtag>_<YYYYMMDD_HHMM>.csv.

The CSV files include the following columns, including feature engineering columns useful for subsequent analysis and modeling:

Column	Description
id	Unique identifier for the tweet within the entire dataset.
hashtag	The hashtag the tweet was collected for (e.g., #ukraine).
username	The user's handle (@name).
text	The cleaned content of the tweet.
likes	Number of likes.
retweets	Number of retweets.
replies	Number of replies.
total_interactions	Sum of likes, retweets, and replies.
post_date_iso	Date and time of posting in ISO format.
text_length	Length (character count) of the cleaned text (ML feature).
word_count	Number of words in the content (ML feature).
sentiment_label	Empty column, intended for a subsequent sentiment label (NLP target).
link	The full link to the tweet.