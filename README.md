## Nitter Scraper (ML/NLP Version v2.1)

A robust Python script for scraping tweets from multiple Nitter instances using Selenium. This tool is designed for collecting clean, structured data suitable for Machine Learning and Natural Language Processing (NLP) tasks. It supports searching for multiple hashtags, handles dynamic instance selection, and includes features for text cleaning and date parsing.

## Features

  * **Dynamic Instance Selection:** Automatically fetches and attempts to use a list of current Nitter instances to maximize success rate and stability.
  * **Selenium-Based Scraping:** Uses Selenium with a headless Chrome browser for reliable navigation and data extraction, including handling "Show more" buttons for full tweet content.
  * **Multiple Hashtag Support:** Scrapes data for a list of hashtags provided as command-line arguments.
  * **Data Cleaning & Feature Engineering:** Cleans tweet text (removes links, excess whitespace) and calculates basic features like `text_length` and `word_count`.
  * **Robust Date Parsing:** Handles various absolute and relative date formats used by Nitter (e.g., "Feb 25, 2022", "1h", "5d").
  * **Customizable Output:** Saves results to separate CSV files per hashtag with a customizable prefix and timestamp.

## Prerequisites

1.  **Python:** Ensure you have Python 3.6+ installed.
2.  **Dependencies:** Install the required Python packages.
3.  **Chrome/Chromium Browser:** A working installation of Chrome or Chromium is required, as the script relies on Selenium to automatically manage the corresponding ChromeDriver.

### Installation

1.  Clone the repository or download the script.

2.  Install the required Python libraries:

    ```bash
    pip install selenium requests
    ```

## Usage

The script is executed via the command line, providing the hashtags you wish to search for and optional parameters.

### Basic Execution

Provide one or more hashtags (without the `#` sign) as positional arguments:

```bash
python nitter-scraper.py ukraine russia
```

### Full Example with Options

The following example searches for the hashtags `#ukraine` and `#russia`, limits the scrape to 50 tweets per hashtag, saves the output files with the prefix `nawrocki_`, and increases the delay between pages to be less aggressive.

```bash
python nitter-scraper.py ukraine russia --max-tweets 50 --filename-prefix nawrocki --page-delay 5.0
```

### Command Line Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `hashtags` | `str` (Nargs: `+`) | N/A | **REQUIRED** List of hashtags to search for (without the `#` sign). |
| `--max-tweets` | `int` | `100` | Maximum number of tweets to scrape for **each** hashtag. |
| `--output-dir` | `str` | `data` | Target directory for the output CSV files. |
| `--filename-prefix` | `str` | `tweets` | Prefix for the output CSV filenames (e.g., `yourname_ukraine_...csv`). |
| `--delay` | `float` | `5.0` | Delay in seconds between scraping different hashtags (adds randomness). |
| `--page-delay` | `float` | `3.0` | Delay in seconds between scrolling/loading new pages during a single hashtag scrape (adds randomness). |
| `--show-samples` | `int` | `3` | Number of sample tweets to display in the console after scraping. |

## Output Data Structure

The script saves the structured data into separate CSV files for each hashtag. The filename format is: `<filename-prefix>_<hashtag>_<YYYYMMDD_HHMM>.csv`.

Each CSV file contains the following columns:

| Column Name | Description |
| :--- | :--- |
| `id` | Unique ID for the row (global across the run). |
| `hashtag` | The hashtag used for the search (with the `#` sign). |
| `username` | The author's username (without the `@` sign). |
| `text` | The cleaned text content of the tweet (links removed). |
| `likes` | Number of likes. |
| `retweets` | Number of retweets. |
| `replies` | Number of replies. |
| `total_interactions` | Sum of `likes`, `retweets`, and `replies`. |
| `post_date_iso` | The parsed date and time in ISO format (`YYYY-MM-DD HH:MM:SS`). |
| `text_length` | Length of the cleaned tweet text. |
| `word_count` | Number of words in the cleaned tweet text. |
| `sentiment_label` | Placeholder column for future NLP analysis. |
| `link` | The direct link to the tweet on the Nitter instance used. |

## How it Works

1.  **Argument Parsing:** The script first reads the required hashtags and optional settings.
2.  **Instance Fetching:** It connects to the Nitter GitHub wiki to dynamically retrieve a list of working Nitter instances.
3.  **Iteration:** For each requested hashtag, it iterates through the fetched Nitter instances.
4.  **Scraping:** It constructs a search URL (e.g., `https://nitter.net/search?f=tweets&q=%23hashtag`) and uses a headless Selenium Chrome browser to navigate and scroll/click the "More" button to load content.
5.  **Extraction:** It extracts the username, date (raw format), content, and interaction counts (replies, retweets, likes) using CSS selectors.
6.  **Processing:** Extracted data is cleaned and the raw date string is converted into a standard ISO format.
7.  **Saving:** The processed data is written to the designated output directory in separate, named CSV files.

## Troubleshooting

  * **`WebDriverException`:** This usually means the script could not initialize the Chrome browser. Ensure that **Chrome/Chromium** is installed on your system. Selenium automatically manages the ChromeDriver, but it requires the browser binary to be present.
  * **"No tweet elements found" or "Failed to fetch tweets"**: The Nitter instance might be down or blocked. The script automatically tries the next instance in the list. If all instances fail, check your network connection or the status of public Nitter instances.
  * **Captchas/Rate Limiting:** If you are scraping a large volume of data very quickly, you might encounter rate-limiting or CAPTCHAs, which Nitter instances are not immune to. Use the `--delay` and `--page-delay` arguments to slow down the scraping process.

<!-- end list -->

```
```