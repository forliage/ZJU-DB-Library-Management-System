# web_crawler.py (Revised)
import requests
from bs4 import BeautifulSoup
import time
import random
import re
# Make sure db_utils.py is in the same directory or accessible via PYTHONPATH
try:
    from db_utils import execute_modify, execute_query
except ImportError as e:
    print(f"Error importing from db_utils: {e}")
    print("Please ensure db_utils.py is in the correct location and has no errors.")
    exit()


# Simulate browser headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7', # Added language preference
    'Referer': 'https://book.douban.com/' # Added referer
}

def get_page_html(url):
    """Fetches HTML content for a given URL."""
    try:
        # Add a small delay before each request
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=HEADERS, timeout=15) # Increased timeout
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        # print(f"Successfully fetched: {url}") # Debug fetch success
        return response.text
    except requests.exceptions.Timeout:
        print(f"Request timed out for URL: {url}")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} for URL: {url}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception occurred: {req_err} for URL: {url}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during fetch: {e} for URL: {url}")
        return None


def extract_douban_id(url):
    """Extracts Douban subject ID from URL."""
    match = re.search(r'/subject/(\d+)/?', url)
    if match:
        return match.group(1)
    return None

def parse_book_info(html):
    """Parses HTML to extract book information."""
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    book_list = []
    items = soup.find_all('tr', class_='item')
    # print(f"Found {len(items)} items on the page.") # Debug item count

    for item in items:
        book_data = {}
        try:
            # 1. Title and Detail URL (which contains the ID)
            title_tag = item.find('div', class_='pl2').find('a')
            if title_tag:
                book_data['BookName'] = title_tag.get('title', '').strip()
                if not book_data['BookName']:
                    book_data['BookName'] = title_tag.get_text(strip=True)

                detail_url = title_tag.get('href', '')
                if detail_url:
                    book_data['BookNo'] = extract_douban_id(detail_url) # Use Douban ID as BookNo
            else:
                # print("Could not find title tag for an item.") # Debug missing title
                continue # Skip if title tag not found

            # 2. Publication Info (Author/Publisher/Year/Price)
            pub_info_tag = item.find('p', class_='pl')
            if pub_info_tag:
                pub_info_text = pub_info_tag.get_text(strip=True)
                parts = [p.strip() for p in pub_info_text.split('/') if p.strip()]
                # print(f"Debug Pub Info Parts for {book_data.get('BookName')}: {parts}") # Debug parts

                # Extract Author (usually the first part, can be complex)
                if len(parts) > 0:
                     # Basic cleaning for author: remove country/translator marks
                    author_text = re.sub(r'^\s*\[.*?\]\s*|\s*\(.*?\)\s*|\s*/.*', '', parts[0]).strip() # Remove country, translator, and potential extra slashes
                    book_data['Author'] = author_text if len(author_text) < 100 else author_text[:100] # Limit length


                # Extract Publisher, Year, Price (order varies, use regex and keywords)
                publisher = None
                year = None
                price_str = None
                price_decimal = None

                # Iterate backwards for potentially more reliable Publisher/Year/Price detection
                possible_publisher_parts = []
                for part in reversed(parts[1:]): # Start from the end, skip author part
                    # Try Price (e.g., CNY 1.00, 68.00元, USD 35.99, $29.95)
                    price_match = re.search(r'(?:CNY|RMB|￥|\$|USD|元)?\s*(\d+(?:\.\d{1,2})?)', part, re.IGNORECASE)
                    if price_match and not price_str:
                         price_str = part # Store original price string if needed
                         price_decimal = float(price_match.group(1))
                         continue # Found price, continue to next part

                    # Try Year (YYYY or YYYY-MM)
                    year_match = re.search(r'^\b(\d{4})\b(?:-\d{1,2})?$', part) # Match full part as year
                    if year_match and not year:
                        year = int(year_match.group(1))
                        continue # Found year, continue

                    # If it's not clearly price or year, add to potential publisher parts
                    possible_publisher_parts.insert(0, part) # Insert at beginning to maintain order


                # Combine remaining parts as publisher (handle potential translators mixed in)
                if possible_publisher_parts:
                     # Simple approach: join parts, filter common non-publisher keywords if needed
                     full_publisher_text = " / ".join(possible_publisher_parts)
                     # Further cleaning might be needed based on observed patterns
                     publisher = full_publisher_text if len(full_publisher_text) < 100 else full_publisher_text[:100] # Limit length


                book_data['Publisher'] = publisher
                book_data['Year'] = year
                book_data['Price'] = price_decimal # Store decimal price

            else:
                 print(f"Could not find publication info tag for: {book_data.get('BookName')}")


            # 3. Rating (Optional)
            rating_tag = item.find('span', class_='rating_nums')
            # if rating_tag:
            #     try:
            #         book_data['Rating'] = float(rating_tag.get_text(strip=True))
            #     except ValueError:
            #         book_data['Rating'] = None

            # 4. Book Type (Generic for now)
            book_data['BookType'] = '综合推荐'

            # 5. Default Stock (More realistic random numbers)
            initial_stock = random.randint(5, 15)
            book_data['Total'] = initial_stock
            book_data['Storage'] = initial_stock

            # --- Debugging Print ---
            # print(f"--- Parsed Data ---")
            # print(f"  BookNo: {book_data.get('BookNo')}")
            # print(f"  BookName: {book_data.get('BookName')}")
            # print(f"  Author: {book_data.get('Author')}")
            # print(f"  Publisher: {book_data.get('Publisher')}")
            # print(f"  Year: {book_data.get('Year')}")
            # print(f"  Price: {book_data.get('Price')}")
            # print("--------------------")

            # Check if essential data (BookNo and BookName) is present
            if book_data.get('BookNo') and book_data.get('BookName'):
                book_list.append(book_data)
            else:
                print(f"信息不完整，跳过: BookNo='{book_data.get('BookNo')}', BookName='{book_data.get('BookName')}'")

        except Exception as e:
            # Log detailed error including the problematic item's HTML if possible
            item_html_snippet = item.prettify()[:500] # Get first 500 chars of the item's HTML
            print(f"解析图书条目时发生意外错误: {e}")
            # print(f"Problematic Item Snippet:\n{item_html_snippet}\n--------------------")


    return book_list

def save_books_to_db(book_list):
    """Saves a list of book data dictionaries to the database."""
    if not book_list:
        return 0

    saved_count = 0
    for book in book_list:
        # Check if book with the same BookNo (Douban ID) already exists
        check_sql = "SELECT BookNo FROM Books WHERE BookNo = %s"
        try:
            existing_book = execute_query(check_sql, (book['BookNo'],))
        except Exception as query_err:
             print(f"查询数据库时出错 (BookNo: {book['BookNo']}): {query_err}")
             continue # Skip this book if query fails

        if existing_book:
            print(f"图书 '{book.get('BookName', 'N/A')}' (ID: {book['BookNo']}) 已存在，跳过。")
            continue

        # Prepare SQL INSERT statement
        sql = """
        INSERT INTO Books
        (BookNo, BookType, BookName, Publisher, Year, Author, Price, Total, Storage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            book.get('BookNo'),
            book.get('BookType', '未分类'),
            book.get('BookName'),
            book.get('Publisher'),
            book.get('Year'),
            book.get('Author'),
            book.get('Price'), # Can be None
            book.get('Total', 0),
            book.get('Storage', 0)
        )

        # Execute the insert operation
        try:
             # execute_modify returns lastrowid for INSERT, which might be 0 or None if not applicable/supported.
             # Success is better determined by lack of exception here.
             execute_modify(sql, params)
             # We assume success if no exception was raised
             saved_count += 1
             print(f"成功插入: {book.get('BookName', 'N/A')} (ID: {book['BookNo']})")
        except Exception as modify_err:
             print(f"插入图书失败 (ID: {book['BookNo']}, Name: {book.get('BookName', 'N/A')}): {modify_err}")
             # You might want to log the failing 'params' here for debugging
             # print(f"Failing Params: {params}")

    return saved_count

# --- Main Execution ---
if __name__ == "__main__":
    base_url = "https://book.douban.com/top250?start={}"
    start_page = 0  # Start from the first page (index 0)
    max_pages_to_crawl = 3 # Limit the crawl to 3 pages (75 books) for testing
    total_saved_books = 0

    print("开始爬取豆瓣图书 Top 250...")

    for i in range(start_page, max_pages_to_crawl):
        page_offset = i * 25
        current_url = base_url.format(page_offset)
        print(f"\n>>> 正在爬取页面 {i+1}/{max_pages_to_crawl}: {current_url}")

        page_html = get_page_html(current_url)

        if page_html:
            parsed_books = parse_book_info(page_html)
            if parsed_books:
                print(f"页面解析完成，找到 {len(parsed_books)} 本有效图书信息。准备存入数据库...")
                saved_this_page = save_books_to_db(parsed_books)
                total_saved_books += saved_this_page
                print(f"本页成功存入 {saved_this_page} 本图书。")
            else:
                print("未能从页面解析出有效图书信息。")
        else:
            print(f"无法获取页面内容，跳过此页。")

        # Wait a bit before the next request
        sleep_duration = random.uniform(1.5, 3.5) # Slightly longer random delay
        print(f"暂停 {sleep_duration:.2f} 秒...")
        time.sleep(sleep_duration)

    print(f"\n爬取任务完成！总共成功存入 {total_saved_books} 本图书到数据库。")