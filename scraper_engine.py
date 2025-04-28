import os
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class NitterScraper:
    """
    Klasa obsługująca pobieranie danych z instancji Nittera
    """
    
    def __init__(self, logger):
        """
        Inicjalizacja klasy scrapera
        
        Args:
            logger: Obiekt loggera do zapisu informacji
        """
        self.logger = logger
        
        # Ustaw tylko instancję nitter.net jako jedyną używaną
        self.instances = ["nitter.net"]
        
        # Selektory CSS dla różnych elementów na stronie Nitter
        self.selectors = {
            'tweets': [".timeline-item", ".tweet", "article.tweet", ".post", ".timeline-tweet"],
            'username': [".username", "a[href^='/']", ".fullname", ".name", ".tweet-name", ".tweet-header a"],
            'date': [".tweet-date a", "a[title*='20']", ".timestamp", "time", ".tweet-time a", 
                   "time[datetime]", ".date"],
            'content': [".tweet-content", ".content", ".tweet-text", ".post-content", 
                       "div.tweet-content", "p.tweet-content", ".tweet-body", ".timeline-item-content"],
            'replies': [".icon-comment", ".reply-count", ".tweet-reply", ".replies", ".comments-count",
                      "div.tweet-stats span:nth-child(1)", ".tweet-interaction-count[title*='repl']"],
            'retweets': [".icon-retweet", ".retweet-count", ".tweet-retweet", ".retweets", ".shares-count",
                       "div.tweet-stats span:nth-child(2)", ".tweet-interaction-count[title*='retw']"],
            'likes': [".icon-heart", ".like-count", ".tweet-like", ".likes", ".favorites-count",
                    "div.tweet-stats span:nth-child(3)", ".tweet-interaction-count[title*='like']", 
                    ".tweet-interaction-count[title*='fav']"],
            'link': [".tweet-link", "a[href*='/status/']", ".tweet-date a", ".tweet a[href*='/status/']"],
            'next_page': [".show-more a", "a.more-results", "a[href*='cursor']", 
                        ".load-more a", "a.next", ".pagination a.next", "a[rel='next']"]
        }

    def setup_webdriver(self, chromedriver_path=None):
        """
        Konfiguracja i inicjalizacja przeglądarki Selenium
        
        Args:
            chromedriver_path: Ścieżka do pliku chromedriver (opcjonalna)
            
        Returns:
            Skonfigurowany obiekt webdriver
        """
        self.logger.debug("Konfiguracja przeglądarki Selenium")
        
        # Konfiguracja opcji Chrome
        options = Options()
        options.add_argument("--headless")  # Uruchomienie bez UI (ważne dla serwera bez GUI)
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Dostosuj User-Agent dla lepszej kompatybilności
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # Dodatkowe opcje dla środowiska serwerowego
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")
        options.add_argument("--blink-settings=imagesEnabled=false")  # Wyłączenie ładowanie obrazów dla szybszego działania
        
        self.logger.info("Inicjalizacja przeglądarki...")
        
        try:
            # Inicjalizacja przeglądarki
            if chromedriver_path:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                # Automatyczne wykrycie ChromeDriver
                driver = webdriver.Chrome(options=options)
                
            self.logger.debug("Przeglądarka zainicjalizowana pomyślnie")
            return driver
            
        except Exception as e:
            self.logger.error(f"Błąd inicjalizacji przeglądarki: {e}")
            raise
    
    def extract_text_from_element(self, tweet, selectors):
        """
        Wydobywa tekst z elementu przy użyciu listy selektorów
        
        Args:
            tweet: Element tweeta
            selectors: Lista selektorów CSS do wypróbowania
            
        Returns:
            Wydobyty tekst lub wartość domyślna
        """
        for selector in selectors:
            try:
                element = tweet.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        return None
    
    def extract_attr_from_element(self, tweet, selectors, attr_name):
        """
        Wydobywa atrybut z elementu przy użyciu listy selektorów
        
        Args:
            tweet: Element tweeta
            selectors: Lista selektorów CSS do wypróbowania
            attr_name: Nazwa atrybutu do wydobycia
            
        Returns:
            Wydobyta wartość atrybutu lub wartość domyślna
        """
        for selector in selectors:
            try:
                element = tweet.find_element(By.CSS_SELECTOR, selector)
                attr_value = element.get_attribute(attr_name)
                if attr_value:
                    return attr_value
            except:
                continue
        return None
    
    def extract_numeric_value(self, tweet, selectors):
        """
        Wydobywa wartość liczbową z elementu przy użyciu listy selektorów
        
        Args:
            tweet: Element tweeta
            selectors: Lista selektorów CSS do wypróbowania
            
        Returns:
            Wydobyta wartość liczbowa lub 0
        """
        for selector in selectors:
            try:
                element = tweet.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    # Usuwanie niedigitowych znaków
                    digits = ''.join(c for c in text if c.isdigit())
                    if digits:
                        return int(digits)
            except:
                continue
        return 0
    
    def scrape_nitter_with_selenium(self, url, max_tweets=100, chromedriver_path=None):
        """
        Pobiera tweety z instancji Nitter przy użyciu Selenium
        
        Args:
            url: URL strony Nitter do przeszukania
            max_tweets: Maksymalna liczba tweetów do pobrania
            chromedriver_path: Ścieżka do chromedriver (opcjonalna)
            
        Returns:
            Lista zawierająca pobrane tweety
        """
        all_tweets = []
        current_url = url
        page_num = 1
        
        # Inicjalizacja WebDriver
        driver = self.setup_webdriver(chromedriver_path)
        
        try:
            # Będziemy kontynuować pobieranie, dopóki nie osiągniemy max_tweets lub nie będzie więcej stron
            while len(all_tweets) < max_tweets:
                self.logger.info(f"Otwieranie strony {page_num}: {current_url}")
                driver.get(current_url)
                
                # Czekamy na załadowanie strony - maksymalnie 15 sekund
                self.logger.debug("Czekanie na załadowanie strony...")
                wait = WebDriverWait(driver, 15)
                
                # Zapisz źródło strony dla celów debugowania (tylko dla pierwszej strony)
                if page_num == 1:
                    debug_dir = "debug"
                    if not os.path.exists(debug_dir):
                        os.makedirs(debug_dir)
                    
                    debug_file = os.path.join(debug_dir, f"debug_nitter_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    self.logger.debug(f"Zapisano źródło strony do pliku {debug_file}")
                
                # Szukamy elementów zawierających tweety
                tweet_elements = []
                for selector in self.selectors['tweets']:
                    try:
                        self.logger.debug(f"Próba znalezienia elementów z selektorem: {selector}")
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            self.logger.debug(f"Znaleziono {len(elements)} elementów pasujących do selektora: {selector}")
                            tweet_elements = elements
                            break
                    except Exception as e:
                        self.logger.debug(f"Błąd dla selektora {selector}: {e}")
                        continue
                
                if not tweet_elements:
                    self.logger.warning("Nie znaleziono elementów tweetów przy użyciu znanych selektorów.")
                    break
                
                # Przetwarzanie każdego znalezionego tweeta
                tweets_on_page = 0
                for i, tweet in enumerate(tweet_elements):
                    # Sprawdzamy czy już osiągnęliśmy maksymalną liczbę tweetów
                    if len(all_tweets) >= max_tweets:
                        break
                        
                    try:
                        # Pobieranie nazwy użytkownika
                        username = self.extract_text_from_element(tweet, self.selectors['username']) or "Nieznany"
                        # Usunięcie @ z nazwy użytkownika, jeśli istnieje
                        if username.startswith('@'):
                            username = username[1:]
                        
                        # Pobieranie daty tweeta
                        date = self.extract_attr_from_element(tweet, self.selectors['date'], "title") or \
                               self.extract_attr_from_element(tweet, self.selectors['date'], "datetime") or \
                               self.extract_text_from_element(tweet, self.selectors['date']) or "Nieznana"
                        
                        # Pobieranie treści tweeta
                        content = self.extract_text_from_element(tweet, self.selectors['content']) or "Brak treści"
                        
                        # Pobieranie interakcji
                        replies = self.extract_numeric_value(tweet, self.selectors['replies'])
                        retweets = self.extract_numeric_value(tweet, self.selectors['retweets'])
                        likes = self.extract_numeric_value(tweet, self.selectors['likes'])
                        interactions = replies + retweets + likes
                        
                        # Pobieranie linku do tweeta
                        link = self.extract_attr_from_element(tweet, self.selectors['link'], "href") or "Brak"
                        
                        # Sprawdź czy link jest względny - jeśli tak, dodaj bazowy URL
                        if link.startswith('/'):
                            base_url = "/".join(current_url.split('/')[:3])  # http(s)://domain.com
                            link = base_url + link
                        
                        # Dodawanie tweeta do listy
                        tweet_data = {
                            'username': username,
                            'date': date,
                            'content': content,
                            'interactions': interactions,
                            'replies': replies,
                            'retweets': retweets,
                            'likes': likes,
                            'link': link
                        }
                        
                        all_tweets.append(tweet_data)
                        tweets_on_page += 1
                        self.logger.debug(f"Dodano tweet #{len(all_tweets)} od {username}, data: {date[:10] if len(date) > 10 else date}")
                        
                    except Exception as e:
                        self.logger.warning(f"Błąd podczas przetwarzania tweeta {i+1}: {e}")
                        continue
                
                self.logger.info(f"Pobrano {tweets_on_page} tweetów z tej strony. Łącznie: {len(all_tweets)}/{max_tweets}")
                
                # Jeśli nie znaleziono żadnych tweetów na tej stronie, kończymy
                if tweets_on_page == 0:
                    self.logger.info("Nie znaleziono tweetów na tej stronie, kończenie.")
                    break
                    
                # Sprawdzenie, czy osiągnęliśmy limit
                if len(all_tweets) >= max_tweets:
                    self.logger.info(f"Osiągnięto maksymalną liczbę tweetów ({max_tweets}), kończenie.")
                    break
                
                # Szukanie linku do następnej strony
                next_url = None
                for selector in self.selectors['next_page']:
                    try:
                        next_page_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if next_page_elements and next_page_elements[0].is_displayed():
                            next_url = next_page_elements[0].get_attribute("href")
                            if next_url:
                                break
                    except Exception as e:
                        self.logger.debug(f"Błąd dla selektora następnej strony {selector}: {e}")
                        continue
                
                if next_url:
                    current_url = next_url
                    page_num += 1
                    
                    # Dodanie losowego opóźnienia, aby uniknąć blokady
                    sleep_time = random.uniform(3.0, 5.0)
                    self.logger.debug(f"Znaleziono link do następnej strony: {current_url}")
                    self.logger.debug(f"Oczekiwanie {sleep_time:.1f} sekund przed przejściem do następnej strony...")
                    time.sleep(sleep_time)
                    continue
                
                self.logger.info("Nie znaleziono linku do następnej strony, kończenie.")
                break
        
        except Exception as e:
            self.logger.error(f"Wystąpił błąd podczas scrapowania: {e}")
        
        finally:
            # Zamknięcie przeglądarki
            self.logger.debug("Zamykanie przeglądarki...")
            driver.quit()
        
        return all_tweets
    
    def try_different_nitter_instances(self, hashtag, max_tweets=100, chromedriver_path=None):
        """
        Próbuje różnych instancji Nitter, aż znajdzie działającą
        
        Args:
            hashtag: Hashtag do wyszukania (bez znaku #)
            max_tweets: Maksymalna liczba tweetów do pobrania
            chromedriver_path: Ścieżka do chromedriver (opcjonalna)
            
        Returns:
            Lista tweetów
        """
        all_tweets = []
        
        # Używamy tylko nitter.net (zgodnie z prośbą)
        instance = "nitter.net"
        try:
            self.logger.info(f"Używanie instancji: {instance}")
            search_url = f"https://{instance}/search?f=tweets&q={hashtag}"
            
            # Pobieranie tweetów
            tweets = self.scrape_nitter_with_selenium(search_url, max_tweets, chromedriver_path)
            
            # Jeśli udało się pobrać tweety
            if tweets:
                self.logger.info(f"Sukces! Pobrano {len(tweets)} tweetów z instancji {instance}")
                all_tweets = tweets
            else:
                self.logger.warning(f"Nie udało się pobrać tweetów z instancji {instance}")
                
        except Exception as e:
            self.logger.error(f"Błąd podczas używania instancji {instance}: {e}")
        
        return all_tweets