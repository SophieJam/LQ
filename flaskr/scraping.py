import requests
from bs4 import BeautifulSoup
import time
from db import create_quote_table, insert_quotes, fetch_all_quotes

base_url = 'http://www.meigensyu.com/quotations/index'
detail_base_url = 'http://www.meigensyu.com'

def scrape_detail_page(detail_url):
    print(f"Fetching detail page: {detail_url}")
    response = requests.get(detail_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch detail page {detail_url}. Status code: {response.status_code}")
        return None, None, None, None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    supplement_info_tag = soup.find('div', class_='meigen_memo')
    supplement_info = supplement_info_tag.text.strip() if supplement_info_tag else "N/A"

    author_name_tag = soup.find('div', class_='authorbox').find('div', class_='name')
    author_name = author_name_tag.text.strip() if author_name_tag else "N/A"
    
    author_dates_tag = soup.find('div', class_='authorbox').find('div', class_='date')
    author_dates = author_dates_tag.text.strip() if author_dates_tag else "N/A"
    
    author_memo_tag = soup.find('div', class_='authorbox').find('div', class_='memo')
    author_memo = author_memo_tag.text.strip() if author_memo_tag else "N/A"
    
    return supplement_info, author_name, author_dates, author_memo

def scrape_quotes():
    quotes_data = []

    for page in range(1, 99):
        url = f"{base_url}/page{page}.html"
        print(f"Fetching page: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        quotes = soup.find_all('div', class_='meigenbox')
        
        if not quotes:
            print(f"ページ {page} に名言データが見つかりませんでした。")
        
        for quote in quotes:
            try:
                quote_text = quote.find('div', class_='text').text.strip()
                link_section = quote.find('div', class_='link')
                source = link_section.find('a', href=True).text.strip()
                detail_link = link_section.find('a', string='[詳細]')['href']
                detail_url = f"{detail_base_url}{detail_link}"
                
                supplement_info, author_name, author_dates, author_memo = scrape_detail_page(detail_url)
                
                if supplement_info is None:
                    continue
                
                quotes_data.append({
                    'quote': quote_text,
                    'source': source,
                    'author_name': author_name,
                    'birthdate': author_dates,
                    'author_memo': author_memo,
                    'supplement_info': supplement_info
                })
            except AttributeError as e:
                print(f"エラーが発生しました: {e}")
                continue
        
        print(f"ページ {page} から {len(quotes)} 件の名言を取得しました。")
        time.sleep(1)
    
    return quotes_data

create_quote_table()
quotes = scrape_quotes()
insert_quotes(quotes)
quotes_from_db = fetch_all_quotes()
for quote in quotes_from_db:
    print(f"Quote: {quote[1]}, Source: {quote[2]}, Author Name: {quote[3]}, Birthdate: {quote[4]}, Author Memo: {quote[5]}, Supplement Info: {quote[6]}")

















