import csv
from datetime import datetime, timedelta
import time
import random
import argparse
import sys
import os
import re
import unicodedata
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# --- CRITICAL: Dynamic Nitter Instance Fetching ---
def get_nitter_instances(url="[https://github.com/zedeus/nitter/wiki/Instances](https://github.com/zedeus/nitter/wiki/Instances)"):
    """
    Fetches the current list of Nitter instances from the GitHub page.
    Uses simple heuristics to parse the markdown/HTML content.
    """
    print(f"Fetching current list of instances from: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Simple extraction of domains from the public instances section
        content = response.text
        domains = set()
        
        # Regex for domains in the text (e.g., nitter.net, nitter.cz, [https://nitter.privacydev.net](https://nitter.privacydev.net))
        found_links = re.findall(r'(https?:\/\/[a-zA-Z0-9\-\.]+\/[a-zA-Z0-9\-\.]+|[a-zA-Z0-9\-\.]+\.(?:net|cz|eu|me|org|dev|lt|ch|tech|pizza|com|space))', content)
        
        for link in found_links:
            link = link.strip()
            if 'nitter' in link and 'onion' not in link and '/' not in link[link.find('nitter'):].replace('nitter', '', 1):
                domain = link.split('//')[-1].split('/')[0]
                domains.add(domain)

        # Secondary heuristic - search for nitter.something.domain
        nitter_domains = re.findall(r'nitter\.[a-zA-Z0-9\-\.]+', content)
        for domain in nitter_domains:
            if 'onion' not in domain:
                 domains.add(domain.split('|')[0].strip())
        
        if not domains:
            print("Warning: Failed to dynamically fetch the instance list.")
            # Fallback static list
            return [
                "nitter.net", "nitter.cz", "nitter.unixfox.eu", "nitter.moomoo.me", 
                "nitter.privacydev.net", "nitter.poast.org", "nitter.projectsegfau.lt"
            ]
        
        sorted_domains = sorted(list(domains))
        print(f"Fetched {len(sorted_domains)} unique instances.")
        return sorted_domains

    except requests.exceptions.RequestException as e:
        print(f"Error while fetching instances, using static list. Error: {e}")
        return [
            "nitter.net", "nitter.cz", "nitter.unixfox.eu", "nitter.moomoo.me", 
            "nitter.privacydev.net", "nitter.poast.org", "nitter.projectsegfau.lt"
        ]


def parse_arguments():
    """
    Parses command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Scraper for tweets from various Nitter instances for given hashtags',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Usage Examples:
  python nitter-scraper-en.py ukraine russia --filename-prefix nawrocki
        '''
    )
    
    parser.add_argument(
        'hashtags',
        nargs='+',
        help='List of hashtags to search for (without the # sign)'
    )
    
    parser.add_argument(
        '--max-tweets',
        type=int,
        default=100,
        help='Maximum number of tweets for each hashtag (default: 100)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Target directory for CSV files (default: data)'
    )
    
    # NOWY ARGUMENT: PREFIX
    parser.add_argument(
        '--filename-prefix',
        type=str,
        default='tweets',
        help='Prefix for the output CSV filenames (e.g., your last name)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=5.0,
        help='Delay in seconds between hashtags (default: 5.0)'
    )
    
    parser.add_argument(
        '--show-samples',
        type=int,
        default=3,
        help='Number of sample tweets to display (default: 3)'
    )
    
    parser.add_argument(
        '--page-delay',
        type=float,
        default=3.0,
        help='Delay between pages in seconds (default: 3.0)'
    )
    
    return parser.parse_args()


# --- DATE AND TEXT PARSING TOOLS (ML READY) ---
def clean_text(text):
    """
    Cleans text: removes excessive whitespace and links.
    """
    if not isinstance(text, str):
        return ""
    # Remove links (URL)
    text = re.sub(r'http\S+|www\S+|\S+\.com\S+|t.co\S+', '', text, flags=re.MULTILINE)
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_nitter_date(date_str, base_time=None):
    """
    Attempts to parse the date from Nitter, handling absolute and relative formats.
    """
    if base_time is None:
        base_time = datetime.now()
        
    date_str = date_str.strip().lower()

    # Absolute format (example: Feb 25, 2022 · 12:00 AM UTC)
    date_formats = [
        "%b %d, %Y · %I:%M %p %Z",
        "%b %d, %Y",
        "%d %b %Y",
        "%Y/%m/%d"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass

    # Relative format (e.g., 1h, 5d, 2mo)
    match = re.match(r'(\d+)\s*(s|m|h|d|w|mo|y)', date_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        delta = timedelta()
        if unit == 's': delta = timedelta(seconds=value)
        elif unit == 'm': delta = timedelta(minutes=value)
        elif unit == 'h': delta = timedelta(hours=value)
        elif unit == 'd': delta = timedelta(days=value)
        elif unit == 'w': delta = timedelta(weeks=value)
        elif unit == 'mo': delta = timedelta(days=value * 30)
        elif unit == 'y': delta = timedelta(days=value * 365)
        
        return base_time - delta
        
    return None

def transform_tweets_for_csv(tweets_by_hashtag):
    """
    Transforms raw tweet data into structured rows ready for CSV saving.
    Adds feature engineering columns.
    """
    transformed_rows = []
    tweet_id = 1
    for hashtag, tweets in tweets_by_hashtag.items():
        for tweet in tweets:
            cleaned_text = clean_text(tweet.get("content", ""))
            
            # Date parsing
            post_date_raw = tweet.get("date", "")
            parsed_date = parse_nitter_date(post_date_raw)
            formatted_date_iso = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else post_date_raw
            
            row = {
                "id": tweet_id,
                "hashtag": f"#{hashtag}",
                "username": tweet.get("username", ""),
                "text": cleaned_text,
                "likes": tweet.get("likes", 0),
                "retweets": tweet.get("retweets", 0),
                "replies": tweet.get("replies", 0),
                "total_interactions": tweet.get("interactions", 0),
                "post_date_iso": formatted_date_iso, 
                "text_length": len(cleaned_text),
                "word_count": len(cleaned_text.split()),
                "sentiment_label": "", 
                "link": tweet.get("link", "")
            }
            transformed_rows.append(row)
            tweet_id += 1
    return transformed_rows


# --- MAIN SCRAPER LOGIC ---

def scrape_nitter_with_selenium(url, max_tweets=100, page_delay=3.0):
    """
    Function to fetch tweets from Nitter using Selenium.
    Uses automatic Chrome configuration (Selenium Manager).
    """
    all_tweets = []
    current_url = url
    page_num = 1
    
    # Selenium Configuration - relies on Selenium Manager
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    
    print("Initializing browser (automatic configuration)...")
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
    except WebDriverException as e:
        print(f"Browser initialization error: {e}")
        print("Ensure Chrome is installed and up-to-date.")
        return []
        
    try:
        while len(all_tweets) < max_tweets:
            print(f"Opening page {page_num}: {current_url}")
            try:
                driver.get(current_url)
                
                wait = WebDriverWait(driver, 15)
                
                # Attempt to find elements containing tweets
                selectors = [".timeline-item", ".tweet", "article.tweet", ".post", ".timeline-tweet"]
                tweet_elements = []
                
                for selector in selectors:
                    try:
                        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                        if elements:
                            print(f"Found {len(elements)} elements matching selector: {selector}")
                            tweet_elements = elements
                            break
                    except TimeoutException:
                        continue
                
                if not tweet_elements:
                    print("No tweet elements found. Ending or instance error.")
                    break
                    
            except TimeoutException:
                print("Page load timeout exceeded. Trying a different instance/hashtag.")
                break
            except Exception as e:
                print(f"Error while loading page: {e}")
                break
            
            # Processing each found tweet
            tweets_on_page = 0
            for i, tweet in enumerate(tweet_elements):
                if len(all_tweets) >= max_tweets:
                    break
                    
                try:
                    # Expand long content ("Show more")
                    try:
                        show_more_button = tweet.find_element(
                            By.XPATH, ".//a[contains(text(), 'Pokaż więcej') or contains(text(), 'Show more')]"
                        )
                        if show_more_button.is_displayed():
                            driver.execute_script("arguments[0].click();", show_more_button)
                            time.sleep(0.5)
                    except NoSuchElementException:
                        pass
                    except Exception as e:
                        print(f"Warning: Error while trying to click 'Show more': {e}")
                        
                    # --- Data Fetching ---
                    
                    # Fetching tweet content
                    content = "No content"
                    content_selectors = [".tweet-content", ".content", ".tweet-text", "p.tweet-content", 
                                       ".timeline-item-content", ".post-content"]
                    for selector in content_selectors:
                        try:
                            content_elem = tweet.find_element(By.CSS_SELECTOR, selector)
                            content = content_elem.text.strip()
                            if content:
                                break
                        except:
                            continue
                            
                    # Fetching username
                    username = "Unknown"
                    try:
                        username_selectors = [".username", "a[href^='/']", ".tweet-name", ".tweet-header a"]
                        for selector in username_selectors:
                            try:
                                username_elem = tweet.find_element(By.CSS_SELECTOR, selector)
                                username = username_elem.text.strip().replace('@', '')
                                if username: break
                            except: continue
                    except: pass
                    
                    # Fetching tweet date
                    date = "Unknown"
                    try:
                        date_selectors = [".tweet-date a", "a[title*='20']", ".timestamp", "time", "time[datetime]"]
                        for selector in date_selectors:
                            try:
                                date_elem = tweet.find_element(By.CSS_SELECTOR, selector)
                                date = date_elem.get_attribute("title") or date_elem.get_attribute("datetime") or date_elem.text.strip()
                                if date: break
                            except: continue
                    except: pass
                    
                    # Fetching interactions
                    interactions = {'replies': 0, 'retweets': 0, 'likes': 0, 'total': 0}
                    
                    stat_selectors = [".tweet-stats .icon-comment + span", ".tweet-stats .icon-retweet + span", ".tweet-stats .icon-heart + span"]
                    
                    for key, selector in zip(['replies', 'retweets', 'likes'], stat_selectors):
                        try:
                            elem = tweet.find_element(By.CSS_SELECTOR, selector)
                            text = elem.text.strip()
                            text_num = ''.join(c for c in text if c.isdigit())
                            if text_num:
                                interactions[key] = int(text_num)
                        except:
                            continue
                    
                    # Calculate total interactions
                    interactions['total'] = interactions['replies'] + interactions['retweets'] + interactions['likes']
                    
                    # Fetching tweet link
                    link = "None"
                    try:
                        link_selectors = ["a[href*='/status/']"]
                        for selector in link_selectors:
                            try:
                                link_elem = tweet.find_element(By.CSS_SELECTOR, selector)
                                link_attr = link_elem.get_attribute("href")
                                if link_attr:
                                    if link_attr.startswith('/'):
                                        base_url = "/".join(current_url.split('/')[:3])
                                        link = base_url + link_attr
                                    else:
                                        link = link_attr
                                    break
                            except: continue
                    except: pass
                    
                    # Add tweet to the list only if it has meaningful content
                    if content != "No content" and len(content.strip()) > 5:
                        tweet_data = {
                            'username': username,
                            'date': date,
                            'content': content,
                            'interactions': interactions['total'],
                            'replies': interactions['replies'],
                            'retweets': interactions['retweets'],
                            'likes': interactions['likes'],
                            'link': link
                        }
                        
                        all_tweets.append(tweet_data)
                        tweets_on_page += 1
                        content_preview = clean_text(content)[:50] + "..." if len(content) > 50 else content
                        print(f"Tweet #{len(all_tweets)}: {username} - {content_preview}")
                    
                except Exception as e:
                    print(f"Error while processing tweet {i+1}: {type(e).__name__} - {e}")
                    continue
            
            print(f"Fetched {tweets_on_page} tweets from this page. Total: {len(all_tweets)}/{max_tweets}")
            
            if tweets_on_page == 0 and len(all_tweets) > 0:
                print("No new tweets found on this page, ending (might be a duplicate page).")
                break
            
            if len(all_tweets) >= max_tweets:
                print(f"Reached maximum number of tweets ({max_tweets}), ending.")
                break
                
            # Finding the link to the next page (More)
            try:
                next_page_selectors = [".show-more a", "a.more-results", "a[href*='cursor']"]
                next_page = None
                
                for selector in next_page_selectors:
                    try:
                        next_page_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if next_page_elements:
                            next_page = next_page_elements[0]
                            break
                    except: continue

                if not next_page:
                    try:
                        next_page_elements = driver.find_elements(By.XPATH, "//a[contains(text(), 'Więcej') or contains(text(), 'More')]")
                        if next_page_elements:
                            next_page = next_page_elements[-1]
                    except: pass
                
                if next_page and next_page.is_displayed():
                    next_url = next_page.get_attribute("href")
                    if next_url and next_url != current_url:
                        current_url = next_url
                        page_num += 1
                        
                        # Delay with randomness
                        sleep_time = random.uniform(page_delay, page_delay + 2.0)
                        print(f"Found link to the next page. Waiting {sleep_time:.1f} seconds...")
                        time.sleep(sleep_time)
                        continue
                        
                print("Did not find a link to the next page, ending.")
                break
                
            except Exception as e:
                print(f"Error while searching for the next page link: {type(e).__name__} - {e}")
                break
    
    except Exception as e:
        print(f"An unexpected error occurred in Selenium: {type(e).__name__} - {e}")
    
    finally:
        if 'driver' in locals():
            print("Closing browser...")
            driver.quit()
    
    return all_tweets

def try_different_nitter_instances(hashtag, max_tweets=100, page_delay=3.0):
    """
    Tries different, dynamically fetched Nitter instances until a working one is found.
    """
    instances = get_nitter_instances()
    all_tweets = []
    
    for instance in instances:
        print(f"\nAttempting to use instance: {instance}")
        search_url = f"https://{instance}/search?f=tweets&q=%23{hashtag}"
        
        try:
            tweets = scrape_nitter_with_selenium(search_url, max_tweets, page_delay)
            
            if tweets:
                print(f"Successfully fetched {len(tweets)} tweets from instance {instance}")
                all_tweets = tweets
                break
            else:
                print(f"Failed to fetch tweets from instance {instance}. Trying next one.")
                
        except Exception as e:
            print(f"Critical error while using instance {instance}: {e}. Trying next one.")
            continue
    
    return all_tweets

def scrape_multiple_hashtags(hashtags, max_tweets=100, delay=5.0, page_delay=3.0):
    """
    Fetches tweets for multiple hashtags
    """
    if isinstance(hashtags, str):
        hashtags = [hashtags]
    
    all_results = {}
    
    for i, hashtag in enumerate(hashtags):
        print(f"\n{'='*60}")
        print(f"Starting fetch for hashtag: #{hashtag} ({i+1}/{len(hashtags)})")
        print(f"{'='*60}")
        
        try:
            tweets = try_different_nitter_instances(
                hashtag, 
                max_tweets, 
                page_delay
            )
            
            if tweets:
                print(f"✅ Successfully fetched {len(tweets)} tweets for #{hashtag}")
                all_results[hashtag] = tweets
            else:
                print(f"❌ Failed to fetch tweets for #{hashtag}")
                all_results[hashtag] = []
                
        except Exception as e:
            print(f"Error while fetching tweets for #{hashtag}: {e}")
            all_results[hashtag] = []
        
        # Delay between hashtags
        if i < len(hashtags) - 1:
            sleep_time = random.uniform(delay, delay + 3.0)
            print(f"Waiting {sleep_time:.1f} seconds before the next hashtag...")
            time.sleep(sleep_time)
    
    return all_results

# --- CSV SAVING (UPDATED) ---

def save_to_separate_csvs(tweets_by_hashtag, output_dir="data", prefix="tweets"):
    """
    Saves processed data to separate CSV files for each hashtag, using a custom prefix.
    
    Filename format: <prefix>_<hashtag>_<YYYYMMDD_HHMM>.csv
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Concise timestamp for the entire run (e.g., 20251027_0604)
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    
    fieldnames = [
        'id', 'hashtag', 'username', 'text', 'likes', 'retweets', 'replies',
        'total_interactions', 'post_date_iso', 'text_length',
        'word_count', 'sentiment_label', 'link'
    ]
    
    total_saved = 0
    
    # Process all data at once to ensure consistent IDs and parsing
    transformed_data = transform_tweets_for_csv(tweets_by_hashtag)
    
    # Group the processed data back to save them separately
    grouped_data = {}
    for row in transformed_data:
        hashtag_name = row['hashtag'].lstrip('#')
        if hashtag_name not in grouped_data:
            grouped_data[hashtag_name] = []
        grouped_data[hashtag_name].append(row)

    for hashtag, rows in grouped_data.items():
        if not rows:
            continue

        # New filename format: <prefix>_<hashtag>_<timestamp>.csv
        filename = f"{prefix}_{hashtag}_{current_time}.csv"
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                    
            print(f"Saved {len(rows)} tweets for #{hashtag} to file {filepath}")
            total_saved += len(rows)

        except Exception as e:
            print(f"Error saving CSV for #{hashtag}: {e}")
            
    # Removed the code for saving the combined CSV file.
    
    return total_saved


def print_sample_tweets(tweets, n=5):
    """
    Displays sample tweets in the console
    """
    if not isinstance(tweets, dict):
        print("Invalid data format for display.")
        return
        
    for hashtag, tweet_list in tweets.items():
        if not tweet_list:
            print(f"\n=== #{hashtag}: No tweets to display ===")
            continue
            
        print(f"\n=== #{hashtag}: SAMPLE TWEETS ({min(n, len(tweet_list))}/{len(tweet_list)}) ===")
        
        for i, tweet in enumerate(tweet_list[:n]):
            print(f"\n--- Tweet {i+1} ---")
            print(f"Hashtag: #{hashtag}")
            print(f"Author: @{tweet['username']}")
            print(f"Date: {tweet['date']} (Parsed: {parse_nitter_date(tweet['date']) or 'Unknown'})")
            content_preview = clean_text(tweet['content'])[:150] + "..." if len(tweet['content']) > 150 else clean_text(tweet['content'])
            print(f"Content: {content_preview}")
            print(f"Interactions: {tweet['interactions']} (Replies: {tweet['replies']}, Retweets: {tweet['retweets']}, Likes: {tweet['likes']})")
            print(f"Link: {tweet['link']}")


# === Main function ===
def main():
    args = parse_arguments()
    print("⭐ === NITTER SCRAPER - ML/NLP VERSION (v2.1) ===")
    
    try:
        results = scrape_multiple_hashtags(
            hashtags=args.hashtags,
            max_tweets=args.max_tweets,
            delay=args.delay,
            page_delay=args.page_delay
        )
        total_tweets = sum(len(v) for v in results.values())
        
        if total_tweets > 0:
            print_sample_tweets(results, n=args.show_samples)
            # Pass the new 'prefix' argument to the save function
            save_to_separate_csvs(results, 
                                  output_dir=args.output_dir, 
                                  prefix=args.filename_prefix)
            print(f"\n✅ Finished successfully. Total {total_tweets} tweets fetched.")
        else:
            print("\n❌ No tweets fetched. Check Nitter instances and network connection.")
            
    except KeyboardInterrupt:
        print("\nInterrupted by user (Ctrl+C).")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Critical error: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()