import csv
import os
import json
from datetime import datetime

def save_to_csv(tweets, filename, logger):
    """
    Zapisuje pobrane tweety do pliku CSV
    
    Args:
        tweets: Lista tweetów do zapisania
        filename: Nazwa pliku
        logger: Obiekt loggera
    """
    try:
        # Upewniamy się, że katalog dla pliku istnieje
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:  # utf-8-sig dla lepszej obsługi w Excel
            # Zmieniona kolejność kolumn: data, użytkownik, ilość interakcji, treść, link
            fieldnames = ['date', 'username', 'interactions', 'content', 'link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            
            writer.writeheader()
            for tweet in tweets:
                # Zapisujemy tylko wybrane pola w określonej kolejności
                writer.writerow({
                    'date': tweet['date'],
                    'username': tweet['username'],
                    'interactions': tweet['interactions'],
                    'content': tweet['content'],
                    'link': tweet['link']
                })
                
        logger.info(f"Zapisano {len(tweets)} tweetów do pliku {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania do pliku CSV: {e}")
        return False

def save_to_json(tweets, filename, logger):
    """
    Zapisuje pobrane tweety do pliku JSON
    
    Args:
        tweets: Lista tweetów do zapisania
        filename: Nazwa pliku
        logger: Obiekt loggera
    """
    try:
        # Upewniamy się, że katalog dla pliku istnieje
        output_dir = os.path.dirname(filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(tweets, jsonfile, ensure_ascii=False, indent=2)
                
        logger.info(f"Zapisano {len(tweets)} tweetów do pliku JSON {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Błąd podczas zapisywania do pliku JSON: {e}")
        return False

def print_sample_tweets(tweets, logger, n=5):
    """
    Wyświetla przykładowe tweety w konsoli i zapisuje je w logu
    
    Args:
        tweets: Lista tweetów
        logger: Obiekt loggera
        n: Liczba tweetów do wyświetlenia (domyślnie 5)
    """
    if not tweets:
        logger.info("Brak tweetów do wyświetlenia")
        return
    
    logger.info(f"=== PRZYKŁADOWE TWEETY ({min(n, len(tweets))}/{len(tweets)}) ===")
    
    for i, tweet in enumerate(tweets[:n]):
        logger.info(f"--- Tweet {i+1} ---")
        logger.info(f"Data: {tweet['date']}")
        logger.info(f"Autor: {tweet['username']}")
        logger.info(f"Interakcje: {tweet['interactions']}")
        content_preview = tweet['content'][:150] + "..." if len(tweet['content']) > 150 else tweet['content']
        logger.info(f"Treść: {content_preview}")
        logger.info(f"Link: {tweet['link']}")