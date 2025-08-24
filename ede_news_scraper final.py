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
        # 修正網址，加入缺少的 sms 參數
        self.news_url = "https://www.edu.tw/News.aspx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_news_list(self, page=1):
        """獲取新聞列表"""
        try:
            # 修正參數
            params = {
                'n': '9E7AC85F1954DDA8',
                'sms': '169B8E91BB75571F',
                'page': page
            }
            
            print(f"正在請求網址: {self.news_url} 參數: {params}")
            response = self.session.get(self.news_url, params=params, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"頁面標題: {soup.title.string if soup.title else '無法取得標題'}")
            return soup
            
        except requests.exceptions.RequestException as e:
            print(f"網路請求錯誤: {e}")
            return None
        except Exception as e:
            print(f"獲取新聞列表失敗: {e}")
            return None
    
    def extract_news_items(self, soup):
        """從頁面提取新聞項目"""
        news_items = []
        
        # 根據實際網頁結構，嘗試多種選擇器
        selectors_to_try = [
            # 表格行選擇器（最常見）
            'table tr',
            'tbody tr',
            # 列表選擇器
            'div.news_item',
            'li.news',
            '.CP_list tr',
            # 通用選擇器
            'tr:has(a)',
            'div:has(a[href*="News_Content"])'
        ]
        
        news_containers = []
        for selector in selectors_to_try:
            try:
                containers = soup.select(selector)
                if containers and len(containers) > 1:  # 至少要有2個以上才算有效
                    news_containers = containers[1:] if selector.endswith('tr') else containers  # 跳過表頭
                    print(f"使用選擇器: {selector}, 找到 {len(news_containers)} 個項目")
                    break
            except:
                continue
        
        if not news_containers:
            print("❌ 無法找到新聞項目容器，嘗試印出頁面結構...")
            # 輸出部分頁面結構以便調試
            print("頁面內容預覽:")
            print(str(soup)[:2000] + "..." if len(str(soup)) > 2000 else str(soup))
            return []
        
        print(f"開始解析 {len(news_containers)} 個新聞項目...")
        
        for i, container in enumerate(news_containers):
            try:
                # 尋找新聞連結
                link_elem = container.find('a', href=re.compile(r'News_Content|news|News'))
                if not link_elem:
                    # 嘗試找任何連結
                    link_elem = container.find('a')
                
                if not link_elem:
                    continue
                
                # 提取標題
                title = link_elem.get_text(strip=True)
                if not title or len(title) < 3:  # 標題太短可能不是新聞
                    continue
                
                # 提取連結
                href = link_elem.get('href', '')
                if href:
                    link = urljoin(self.base_url, href)
                else:
                    continue
                
                # 提取時間（尋找包含日期格式的文字）
                date_text = ""
                all_text = container.get_text()
                date_patterns = [
                    r'(\d{3}-\d{2}-\d{2})',  # 114-08-14
                    r'(\d{4}-\d{2}-\d{2})',  # 2025-08-14
                    r'(\d{1,2}/\d{1,2}/\d{4})',  # 8/14/2025
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, all_text)
                    if match:
                        date_text = match.group(1)
                        break
                
                # 提取發布單位（通常在表格的某一欄）
                unit = ""
                td_elements = container.find_all('td')
                for td in td_elements:
                    td_text = td.get_text(strip=True)
                    # 檢查是否包含常見的教育部單位名稱
                    unit_keywords = ['署', '司', '處', '部', '會', '局', '中心']
                    if any(keyword in td_text for keyword in unit_keywords) and len(td_text) < 20:
                        unit = td_text
                        break
                
                news_item = {
                    'title': title,
                    'link': link,
                    'date': date_text,
                    'unit': unit
                }
                
                news_items.append(news_item)
                print(f"  {i+1}. {title[:50]}... [{unit}] [{date_text}]")
                
            except Exception as e:
                print(f"解析第 {i+1} 個項目時出錯: {e}")
                continue
        
        print(f"成功提取 {len(news_items)} 個新聞項目")
        return news_items
    
    def get_news_detail(self, news_url):
        """獲取新聞詳細內容"""
        try:
            print(f"正在獲取詳細內容: {news_url}")
            response = self.session.get(news_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取內文（嘗試多種選擇器）
            content_selectors = [
                'div.content',
                'div.news-content', 
                'div.article-content',
                'div#content',
                'div.CP_content',
                '.page_content',
                'div:contains("聯絡人")',
                'div:contains("電話")'
            ]
            
            content = ""
            for selector in content_selectors:
                try:
                    if selector.startswith('div:contains'):
                        # 特殊處理包含文字的選擇器
                        elements = soup.find_all('div')
                        for elem in elements:
                            if '聯絡人' in elem.get_text() or '電話' in elem.get_text():
                                content = elem.get_text(strip=True)
                                break
                        if content:
                            break
                    else:
                        content_elem = soup.select_one(selector)
                        if content_elem:
                            content = content_elem.get_text(strip=True)
                            break
                except:
                    continue
            
            # 如果還是找不到，就用整個頁面內容
            if not content:
                content = soup.get_text()
            
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
            r'聯絡人[：:]\s*([^\s\n,，；;]+)',
            r'連絡人[：:]\s*([^\s\n,，；;]+)',
            r'新聞聯絡人[：:]\s*([^\s\n,，；;]+)',
            r'承辦人[：:]\s*([^\s\n,，；;]+)',
            r'聯絡人\s*([^\s\n,，；;]+)',
        ]
        
        # 電話號碼模式（更完整）
        phone_patterns = [
            r'電話[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{3,4})',
            r'聯絡電話[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{3,4})',
            r'(?:TEL|Tel|tel)[：:]?\s*(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{3,4})',
            r'(\(?0\d{1,2}\)?\s*-?\s*\d{3,4}\s*-?\s*\d{3,4})',  # 通用電話格式
        ]
        
        # 搜尋聯絡人
        for pattern in contact_patterns:
            match = re.search(pattern, content)
            if match:
                person_name = match.group(1).strip()
                # 過濾太長的結果（可能匹配到錯誤內容）
                if len(person_name) <= 10 and not re.search(r'\d{3,}', person_name):
                    contact_info['person'] = person_name
                    break
        
        # 搜尋電話
        for pattern in phone_patterns:
            match = re.search(pattern, content)
            if match:
                phone_number = match.group(1).strip()
                # 簡單驗證電話號碼格式
                if re.match(r'^\(?0\d{1,2}\)?[-\s]?\d{3,4}[-\s]?\d{3,4}$', phone_number):
                    contact_info['phone'] = phone_number
                    break
        
        return contact_info
    
    def filter_by_unit(self, news_items, target_unit):
        """根據發布單位過濾新聞 - 只檢查單位欄位，不檢查標題"""
        filtered_items = []
        
        # 單位關鍵字映射
        unit_keywords = {
            '體育署': ['體育署', '體育', 'Sports'],
            '國教署': ['國教署', '國民及學前教育署', '國教', 'K-12'],
            '青年署': ['青年署', '青年發展署', '青年', 'Youth']
        }
        
        target_keywords = unit_keywords.get(target_unit, [target_unit])
        
        for item in news_items:
            unit_text = item.get('unit', '')
            
            # 檢查是否匹配任一關鍵字 - 只檢查單位
            match_found = False
            for keyword in target_keywords:
                if keyword in unit_text:  # 只檢查 unit_text
                    match_found = True
                    break
            
            if match_found:
                filtered_items.append(item)
                
        return filtered_items
    
    def scrape_news(self, target_unit, max_count):
        """主要爬取函數 - 改進版：持續爬取直到達到目標數量"""
        print(f"開始爬取 {target_unit} 的新聞，目標數量: {max_count}")
        
        scraped_news = []
        page = 1
        max_pages = 100  # 大幅增加最大頁數
        consecutive_empty_pages = 0  # 連續空頁計數
        max_empty_pages = 3  # 連續空頁上限
        
        while len(scraped_news) < max_count and page <= max_pages and consecutive_empty_pages < max_empty_pages:
            print(f"\n{'='*60}")
            print(f"正在爬取第 {page} 頁... (已收集: {len(scraped_news)}/{max_count})")
            print(f"{'='*60}")
            
            soup = self.get_news_list(page)
            if not soup:
                print(f"❌ 無法獲取第 {page} 頁內容")
                consecutive_empty_pages += 1
                page += 1
                continue
            
            news_items = self.extract_news_items(soup)
            if not news_items:
                print(f"❌ 第 {page} 頁沒有找到新聞項目")
                consecutive_empty_pages += 1
                page += 1
                continue
            
            # 重置連續空頁計數
            consecutive_empty_pages = 0
            
            # 過濾指定單位的新聞
            filtered_items = self.filter_by_unit(news_items, target_unit)
            print(f"✅ 找到 {len(filtered_items)} 篇符合 '{target_unit}' 的新聞")
            
            # 如果這一頁沒有符合的新聞，繼續下一頁
            if not filtered_items:
                print(f"⚠️ 第 {page} 頁沒有 {target_unit} 的新聞，繼續搜尋...")
                page += 1
                time.sleep(1)
                continue
            
            # 處理符合條件的新聞
            for item in filtered_items:
                if len(scraped_news) >= max_count:
                    break
                
                print(f"\n處理新聞 {len(scraped_news)+1}/{max_count}: {item['title'][:50]}...")
                
                # 檢查是否重複（根據URL或標題）
                is_duplicate = False
                for existing_news in scraped_news:
                    if (existing_news['url'] == item['link'] or 
                        existing_news['title'] == item['title']):
                        print(f"⚠️ 發現重複新聞，跳過: {item['title'][:30]}...")
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    continue
                
                # 獲取詳細內容
                try:
                    detail = self.get_news_detail(item['link'])
                except Exception as e:
                    print(f"⚠️ 無法獲取詳細內容: {e}")
                    detail = {'contact_name': '', 'contact_tel': ''}
                
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
                print(f"✅ 成功處理第 {len(scraped_news)} 篇新聞")
                
                # 適當延遲避免被封鎖
                time.sleep(1)
            
            # 如果已經達到目標數量，結束爬取
            if len(scraped_news) >= max_count:
                print(f"\n🎉 已達到目標數量！")
                break
                
            page += 1
            time.sleep(1)  # 頁面間延遲
            
            # 每10頁顯示進度
            if page % 10 == 0:
                print(f"\n📊 進度報告: 已搜尋 {page} 頁，收集到 {len(scraped_news)} 篇新聞")
        
        # 結果摘要
        if consecutive_empty_pages >= max_empty_pages:
            print(f"\n⚠️ 連續 {max_empty_pages} 頁沒有找到內容，停止搜尋")
        elif page > max_pages:
            print(f"\n⚠️ 已達到最大頁數限制 ({max_pages} 頁)")
        
        print(f"\n🎉 爬取完成！成功收集 {len(scraped_news)} 筆 {target_unit} 的新聞")
        return scraped_news

def get_user_input():
    """獲取用戶輸入並進行防呆檢查"""
    while True:
        try:
            # 輸入文章數量
            count_input = input("請輸入要爬取的文章數量 (1-80): ").strip()
            if not count_input.isdigit():
                print("❌ 請輸入有效的數字！")
                continue
            
            count = int(count_input)
            if count < 1 or count > 80:  # 減少到20篇
                print("❌ 文章數量必須在 1-80 之間！")
                continue
            
            # 輸入發布單位
            print("\n可選的發布單位: 體育署、國教署、青年署")
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
        return True
    except Exception as e:
        print(f"❌ 保存文件失敗: {e}")
        return False

def main():
    """主函數"""
    print("=" * 50)
    print("🏫 教育部新聞爬蟲程式 (修正版)")
    print("=" * 50)
    
    scraper = EduNewsScraper()
    
    # 方式一：手動輸入模式
    mode = input("選擇模式 - 1: 手動輸入, 2: 測試模式(爬取體育署3篇) (1/2): ").strip()
    
    if mode == "1":
        # 手動輸入模式
        count, unit = get_user_input()
        
        print(f"\n🚀 開始爬取...")
        news_data = scraper.scrape_news(unit, count)
        
        if news_data:
            filename = f"{unit}_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if save_to_json(news_data, filename):
                print(f"\n📊 爬取結果摘要:")
                print(f"   目標單位: {unit}")
                print(f"   成功數量: {len(news_data)}")
                print(f"   儲存檔案: {filename}")
        else:
            print("❌ 沒有爬取到任何數據，請檢查網路連線或單位名稱")
    
    elif mode == "2":
        # 測試模式
        print(f"\n🧪 測試模式：爬取體育署 3 篇新聞...")
        news_data = scraper.scrape_news("體育署", 3)
        
        if news_data:
            filename = f"test_sports_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            save_to_json(news_data, filename)
            print(f"\n📊 測試結果: 成功爬取 {len(news_data)} 篇新聞")
        else:
            print("❌ 測試失敗，請檢查網路連線")
    
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main()