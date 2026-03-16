# Nitter Scraper (v2.1 - Stable Base)

A Python script designed for bulk data collection from various Nitter instances (an alternative interface for X/Twitter) based on user-provided hashtags. This tool utilizes **Selenium** for dynamic page loading and navigating around potential rate limits or blocks, making it suitable for acquiring large text corpora for Machine Learning (ML) and Natural Language Processing (NLP) projects.

## Requirements

The project requires a standard Python environment and an up-to-date browser installation.

* **Python:** Version 3.8+
* **Browser:** **Google Chrome** must be installed. The script relies on Selenium Manager to automatically download and configure the necessary ChromeDriver.

## Installation

1.  **Clone or download the repository:**

    ```bash
    git clone https://github.com/gfxmz/nitter-scraper.git
    cd nitter-scraper
    ```

2.  **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

The script is executed via the command line, accepting a list of hashtags as positional arguments.

### Syntax

```bash
python nitter-scraper.py <HASHTAG1> <HASHTAG2> [OPTIONS]
```

### Options

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `hashtags` | Positional | N/A | List of hashtags to search for (without the # sign) |
| `--max-tweets` | Integer | `100` | Maximum number of tweets for each hashtag |
| `--output-dir` | String | `data` | Target directory for CSV files |
| `--filename-prefix` | String | `tweets` | Prefix for the output CSV filenames (e.g., your last name) |
| `--since` | String | `None` | Lower bound date (YYYY-MM-DD) for tweets, e.g. 2023-01-01 |
| `--until` | String | `None` | Upper bound date (YYYY-MM-DD) for tweets, e.g. 2023-12-31 |
| `--delay` | Float | `5.0` | Delay in seconds between hashtags |
| `--show-samples` | Integer | `3` | Number of sample tweets to display in console |
| `--page-delay` | Float | `3.0` | Delay between pages in seconds |

### Usage Examples

Fetch 100 tweets for #ukraine and 100 for #russia:
```bash
python nitter-scraper.py ukraine russia
```

Fetch posts with a custom limit and specific file prefix:
```bash
python nitter-scraper.py ukraine russia --max-tweets 500 --filename-prefix nawrocki
```

Fetch historical tweets using date filters (from Jan 1, 2023 to Dec 31, 2023):
```bash
python nitter-scraper.py ukraine --since 2023-01-01 --until 2023-12-31
```

Save the resulting CSV files to an `output/` directory instead of the default `data/`:
```bash
python nitter-scraper.py poland --output-dir output
```

## Output data format 

The script generates a separate CSV file for each hashtag in the specified output directory.

### Filename Format Breakdown

| Element | Description | Example Value |
| :--- | :--- | :--- |
| **Prefix** | Custom prefix (e.g., last name) defined by `--filename-prefix`. | `nawrocki` |
| **Hashtag** | The hashtag used for scraping. | `ukraine` |
| **Timestamp (Date)** | The date the script was run. | `20251108` |
| **Timestamp (Time)** | The time the script was run. | `1015` |

**Full Filename Format:** `<prefix>_<hashtag>_<YYYYMMDD_HHMM>.csv`

**Example Filename:** `nawrocki_ukraine_20251108_1015.csv`