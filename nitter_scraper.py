# GFXMZ NITTER SCRAPER

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging
import os
import sys
from datetime import datetime

# Import modułów własnych
from scraper_engine import NitterScraper
from data_exporter import save_to_csv, print_sample_tweets

def setup_logger(log_dir="logs"):
    """
    Konfiguracja systemu logowania
    
    Args:
        log_dir: Katalog na pliki logów
    
    Returns:
        Obiekt loggera
    """
    # Tworzenie katalogu na logi, jeśli nie istnieje
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nazwa pliku logu z datą i godziną
    log_filename = os.path.join(log_dir, f"nitter_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Konfiguracja loggera
    logger = logging.getLogger("nitter_scraper")
    logger.setLevel(logging.INFO)
    
    # Handler dla zapisywania do pliku
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # Handler dla wyświetlania w konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format logów
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Dodanie handlerów do loggera
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def parse_arguments():
    """
    Parsowanie argumentów wiersza poleceń
    
    Returns:
        Sparsowane argumenty
    """
    parser = argparse.ArgumentParser(description="Scraper postów z Twittera przez instancje Nittera")
    
    # Argumenty obowiązkowe
    parser.add_argument("hashtags", nargs='+', help="Hashtagi do wyszukania (bez znaku #), od 1 do 5 tagów")
    
    # Argumenty opcjonalne
    parser.add_argument("--max-tweets", type=int, default=100, 
                        help="Maksymalna liczba tweetów do pobrania dla KAŻDEGO hashtagu (domyślnie 100)")
    parser.add_argument("--chromedriver-path", help="Ścieżka do pliku chromedriver (opcjonalna)")
    parser.add_argument("--output-file", help="Bazowa nazwa pliku wyjściowego CSV (opcjonalna, hashtag zostanie dodany)")
    parser.add_argument("--log-dir", default="logs", help="Katalog na pliki logów (domyślnie 'logs')")
    parser.add_argument("--debug", action="store_true", help="Włącz tryb debugowania")
    
    args = parser.parse_args()
    
    # Sprawdzenie, czy liczba tagów nie przekracza 5
    if len(args.hashtags) > 5:
        print("BŁĄD: Maksymalna liczba tagów to 5. Podano:", len(args.hashtags))
        sys.exit(1)
        
    return args

def main():
    # Parsowanie argumentów
    args = parse_arguments()
    
    # Konfiguracja loggera
    logger = setup_logger(args.log_dir)
    
    # Ustawienie poziomu logowania
    if args.debug:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # Początek pomiaru czasu całego procesu
    total_start_time = datetime.now()
    
    # Informacja o rozpoczęciu całego procesu
    logger.info(f"Rozpoczynam pobieranie tweetów dla {len(args.hashtags)} tagów: {', '.join(['#' + tag for tag in args.hashtags])}")
    logger.info(f"Cel: maksymalnie {args.max_tweets} tweetów dla KAŻDEGO hashtagu")
    
    # Przechowywanie wszystkich tweetów po tagach
    all_tweets_by_hashtag = {}
    total_tweets_count = 0
    
    try:
        # Inicjalizacja scrapera
        scraper = NitterScraper(logger)
        
        # Przetwarzanie każdego hashtagu osobno
        for hashtag in args.hashtags:
            hashtag_start_time = datetime.now()
            logger.info(f"Rozpoczynam pobieranie tweetów dla #{hashtag}")
            
            # Pobieranie tweetów dla bieżącego hashtagu
            tweets = scraper.try_different_nitter_instances(hashtag, args.max_tweets, args.chromedriver_path)
            
            # Czas zakończenia dla bieżącego hashtagu
            hashtag_end_time = datetime.now()
            hashtag_elapsed_time = hashtag_end_time - hashtag_start_time
            
            logger.info(f"Pobrano {len(tweets)} tweetów dla #{hashtag} w czasie {hashtag_elapsed_time}")
            
            # Zapisanie wyników dla tego hashtagu
            all_tweets_by_hashtag[hashtag] = tweets
            total_tweets_count += len(tweets)
            
            # Wyświetlenie przykładowych tweetów
            if tweets:
                print_sample_tweets(tweets, logger)
                
                # Określenie nazwy pliku wyjściowego dla tego hashtagu
                output_file = args.output_file
                if not output_file:
                    output_file = f"data/tweety_{hashtag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                else:
                    # Jeśli podano nazwę pliku a mamy wiele tagów, dodaj tag do nazwy
                    if len(args.hashtags) > 1:
                        base_name, ext = os.path.splitext(output_file)
                        output_file = f"{base_name}_{hashtag}{ext}"
                
                # Zapisanie do CSV
                save_to_csv(tweets, output_file, logger)
            else:
                logger.warning(f"Nie udało się pobrać żadnych tweetów dla #{hashtag}")
        
        # Podsumowanie całego procesu
        total_end_time = datetime.now()
        total_elapsed_time = total_end_time - total_start_time
        
        logger.info(f"===== PODSUMOWANIE =====")
        logger.info(f"Łącznie przetworzono {len(args.hashtags)} tagów")
        logger.info(f"Łącznie pobrano {total_tweets_count} tweetów")
        if len(args.hashtags) > 0:
            logger.info(f"Średnio {total_tweets_count/len(args.hashtags):.1f} tweetów na tag")
        for hashtag, tweets in all_tweets_by_hashtag.items():
            logger.info(f"  #{hashtag}: {len(tweets)} tweetów")
        logger.info(f"Całkowity czas: {total_elapsed_time}")
    
    except Exception as e:
        logger.error(f"Wystąpił błąd: {e}", exc_info=True)
        return 1
    
    logger.info("Zakończono pobieranie danych")
    return 0

if __name__ == "__main__":
    sys.exit(main())