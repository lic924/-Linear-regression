import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

class EduNewsScraper:
    def __init__(self):
        self.base_url = "https://www.edu.tw"
        self.news_url = "https://www.edu.tw/News.aspx?n=9E7AC85F1954DDA8"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_news_list(self, page=1):
        """獲取新聞列表"""
        try:
            params = {
                'n': '9E7AC85F1954DDA8',
                'page': page
            }
            response = self.session.get(self.news_url, params=params)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except Exception as e:
            print(f"獲取新聞列表失敗: {e}")
            return None
    
    def extract_news_items(self, soup):
        """從頁面提取新聞項目"""
        news_items = []
        
        # 尋找新聞項目容器（需要根據實際網頁結構調整）
        news_containers = soup.find_all('div', class_='news_item') or \
                         soup.find_all('tr', class_='news_row') or \
                         soup.find_all('li', class_='news') or \
                         soup.select('div.CP_list tr')
        
        if not news_containers:
            # 如果找不到特定class，嘗試其他選擇器
            news_containers = soup.select('table tr')[1:]  # 跳過表頭
        
        for container in news_containers:
            try:
                # 提取標題和連結
                title_elem = container.find('a') or container.find('td', string=re.compile(r'.+'))
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True) if title_elem else ""
                link = ""
                
                if title_elem.name == 'a':
                    link = urljoin(self.base_url, title_elem.get('href', ''))
                
                # 提取時間
                date_text = ""
                date_elem = container.find('td', string=re.compile(r'\d{4}')) or \
                           container.find(string=re.compile(r'\d{4}'))
                if date_elem:
                    date_text = date_elem.strip()
                
                # 提取發布單位
                unit = ""
                unit_elem = container.find('td')
                if unit_elem:
                    unit_text = unit_elem.get_text(strip=True)
                    # 簡單判斷是否為發布單位
                    if any(keyword in unit_text for keyword in ['署', '司', '局', '處', '部', '會']):
                        unit = unit_text
                
                if title and link:
                    news_items.append({
                        'title': title,
                        'link': link,
                        'date': date_text,
                        'unit': unit
                    })
                    
            except Exception as e:
                print(f"解析新聞項目時出錯: {e}")
                continue
        
        return news_items
    
    def get_news_detail(self, news_url):
        """獲取新聞詳細內容"""
        try:
            response = self.session.get(news_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取內文
            content_selectors = [
                'div.content',
                'div.news-content', 
                'div.article-content',
                'div#content',
                'div.CP_content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # 提取聯絡人和電話
            contact_info = self.extract_contact_info(content, soup)
            
            return {
                'contact_name': contact_info.get('person', ''),
                'contact_tel': contact_info.get('phone', '')
            }
            
        except Exception as e:
            print(f"獲取新聞詳情失敗 {news_url}: {e}")
            return {
                'contact_name': '',
                'contact_tel': ''
            }
    
    def extract_contact_info(self, content, soup):
        """提取聯絡人和電話信息"""
        contact_info = {'person': '', 'phone': ''}
        
        # 常見的聯絡人模式
        contact_patterns = [
            r'聯絡人[：:]\s*([^\s\n]+)',
            r'連絡人[：:]\s*([^\s\n]+)',
            r'新聞聯絡人[：:]\s*([^\s\n]+)',
            r'承辦人[：:]\s*([^\s\n]+)'
        ]
        
        # 電話號碼模式
        phone_patterns = [
            r'電話[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{4})',
            r'聯絡電話[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{4})',
            r'(?:TEL|Tel|tel)[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{4})'
        ]
        
        # 搜尋聯絡人
        for pattern in contact_patterns:
            match = re.search(pattern, content)
            if match:
                contact_info['person'] = match.group(1).strip()
                break
        
        # 搜尋電話
        for pattern in phone_patterns:
            match = re.search(pattern, content)
            if match:
                contact_info['phone'] = match.group(1).strip()
                break
        
        return contact_info
    
    def filter_by_unit(self, news_items, target_unit):
        """根據發布單位過濾新聞"""
        filtered_items = []
        for item in news_items:
            if target_unit in item.get('unit', '') or target_unit in item.get('title', ''):
                filtered_items.append(item)
        return filtered_items
    
    def scrape_news(self, target_unit, max_count):
        """主要爬取函數"""
        print(f"開始爬取 {target_unit} 的新聞，目標數量: {max_count}")
        
        scraped_news = []
        page = 1
        max_pages = 10  # 防止無限循環
        
        while len(scraped_news) < max_count and page <= max_pages:
            print(f"正在爬取第 {page} 頁...")
            
            soup = self.get_news_list(page)
            if not soup:
                print(f"無法獲取第 {page} 頁內容")
                break
            
            news_items = self.extract_news_items(soup)
            if not news_items:
                print(f"第 {page} 頁沒有找到新聞項目")
                break
            
            # 過濾指定單位的新聞
            filtered_items = self.filter_by_unit(news_items, target_unit)
            
            for item in filtered_items:
                if len(scraped_news) >= max_count:
                    break
                
                print(f"處理新聞: {item['title'][:30]}...")
                
                # 獲取詳細內容
                detail = self.get_news_detail(item['link'])
                
                news_data = {
                    'date': item['date'],
                    'unit': item['unit'] or target_unit,
                    'title': item['title'],
                    'url': item['link'],
                    'author': {
                        'name': detail['contact_name'],
                        'tel': detail['contact_tel']
                    }
                }
                
                scraped_news.append(news_data)
                time.sleep(1)  # 避免過於頻繁的請求
            
            page += 1
        
        print(f"成功爬取 {len(scraped_news)} 筆 {target_unit} 的新聞")
        return scraped_news

def get_user_input():
    """獲取用戶輸入並進行防呆檢查"""
    while True:
        try:
            # 輸入文章數量
            count_input = input("請輸入要爬取的文章數量 (1-50): ").strip()
            if not count_input.isdigit():
                print("❌ 請輸入有效的數字！")
                continue
            
            count = int(count_input)
            if count < 1 or count > 50:
                print("❌ 文章數量必須在 1-50 之間！")
                continue
            
            # 輸入發布單位
            print("\n可選的發布單位: 體育署、國教署、青年署、高教司、技職司等")
            unit_input = input("請輸入要爬取的發布單位: ").strip()
            if not unit_input:
                print("❌ 發布單位不能為空！")
                continue
            
            # 確認輸入
            print(f"\n✅ 確認設定:")
            print(f"   文章數量: {count}")
            print(f"   發布單位: {unit_input}")
            
            confirm = input("確認以上設定嗎？(y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                return count, unit_input
            else:
                print("請重新輸入...\n")
                
        except KeyboardInterrupt:
            print("\n程式已取消執行")
            exit()
        except Exception as e:
            print(f"❌ 輸入錯誤: {e}")

def save_to_json(data, filename):
    """保存數據到JSON文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 數據已保存到 {filename}")
    except Exception as e:
        print(f"❌ 保存文件失敗: {e}")

def main():
    """主函數"""
    print("=" * 50)
    print("🏫 教育部新聞爬蟲程式")
    print("=" * 50)
    
    scraper = EduNewsScraper()
    
    # 方式一：手動輸入模式
    mode = input("選擇模式 - 1: 手動輸入, 2: 預設爬取體育署/國教署/青年署各5筆 (1/2): ").strip()
    
    if mode == "1":
        # 手動輸入模式
        count, unit = get_user_input()
        
        print(f"\n🚀 開始爬取...")
        news_data = scraper.scrape_news(unit, count)
        
        if news_data:
            filename = f"{unit}_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_to_json(news_data, filename)
        else:
            print("❌ 沒有爬取到任何數據")
    
    elif mode == "2":
        # 預設模式：爬取體育署、國教署、青年署各5筆
        units = ['體育署', '國教署', '青年署']
        all_results = {}
        
        for unit in units:
            print(f"\n🚀 開始爬取 {unit} 的新聞...")
            news_data = scraper.scrape_news(unit, 5)
            all_results[unit] = news_data
            time.sleep(2)  # 單位間暫停
        
        # 保存合併結果
        result_data = []
        for unit, data in all_results.items():
            result_data.extend(data)
        
        filename = f"edu_news_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_to_json(result_data, filename)
        
        # 顯示摘要
        print("\n📊 爬取摘要:")
        for unit, data in all_results.items():
            print(f"   {unit}: {len(data)} 篇文章")
    
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main()