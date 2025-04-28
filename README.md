# Nitter Scraper

Skrypt do automatycznego pobierania postów z Twittera poprzez instancje Nittera. Wykorzystuje Selenium do ekstrakcji danych i jest zoptymalizowany do pracy na serwerze VPS bez interfejsu graficznego.

## Funkcje

- Automatyczne pobieranie postów zawierających określone hashtagi (od 1 do 5 tagów)
- Zapisywanie danych w formacie CSV w folderze data
- Obsługa instancji nitter.net
- Regularne uruchamianie (co godzinę lub według harmonogramu)
- Szczegółowe logowanie operacji

## Struktura projektu

- `nitter_scraper.py` - główny skrypt
- `scraper_engine.py` - silnik scrapera
- `data_exporter.py` - eksporter danych
- `hourly_scraper.sh` - skrypt do regularnego uruchamiania
- `requirements.txt` - wymagane pakiety Python

## Użycie

```bash
python3 nitter_scraper.py [hashtag1] [hashtag2] ... [hashtag5] --max-tweets [liczba]