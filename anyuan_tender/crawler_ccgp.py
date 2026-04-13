"""
网站4：中国政府采购网搜索 (search.ccgp.gov.cn)
使用Scrapling绕过反爬，获取JavaScript动态渲染内容
"""

import time
import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict

from scrapling.fetchers import StealthyFetcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CcgpCrawler:
    """中国政府采购网爬虫 - 使用Scrapling"""
    
    BASE_URL = "https://search.ccgp.gov.cn/bxsearch"
    KEYWORD = "安远"
    SOURCE = "ccgp"
    
    def __init__(self):
        self.fetcher = StealthyFetcher()
    
    def fetch_page(self, page_index: int = 1) -> str:
        """
        使用Scrapling获取页面HTML
        
        Args:
            page_index: 页码
        """
        url = (
            f"{self.BASE_URL}?searchtype=1"
            f"&page_index={page_index}"
            f"&kw={self.KEYWORD}"
            f"&timeType=2"
        )
        
        logger.info(f"抓取第 {page_index} 页...")
        
        try:
            # 使用Scrapling抓取，等待JS渲染
            page = self.fetcher.fetch(
                url=url,
                headless=True,
                timeout=60000,  # 60秒超时
                wait=5000  # 等待5秒让JS执行
            )
            
            logger.info(f"页面长度: {len(page.body)} 字节")
            return page.body
            
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            return ""
    
    def parse_html(self, html: bytes) -> List[Dict]:
        """
        解析HTML，提取招标公告列表
        
        Args:
            html: 页面HTML字节
        """
        if not html:
            return []
        
        # 解析HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        records = []
        
        # 查找所有招标记录li
        lis = soup.find_all('li')
        logger.info(f"找到 {len(lis)} 个li元素")
        
        for li in lis:
            try:
                # 查找链接
                a = li.find('a', href=True)
                if not a:
                    continue
                
                href = a.get('href', '')
                # 必须是ccgp.gov.cn的链接
                if 'ccgp.gov.cn' not in href:
                    continue
                
                # 获取文本内容
                text = li.get_text(strip=True)
                
                # 必须包含安远
                if self.KEYWORD not in text:
                    continue
                
                # 提取时间（格式：2026.04.11）
                time_match = re.search(r'(2026\.\d{2}\.\d{2})', text)
                pub_time = time_match.group(1).replace('.', '-') if time_match else ''
                
                # 清理标题
                title = re.sub(r'2026\.\d{2}\.\d{2}', '', text).strip()
                title = re.sub(r'\s+', ' ', title)
                
                records.append({
                    "title": title,
                    "linkurl": href,
                    "webdate": pub_time,
                    "content": "",  # ccgp搜索页没有摘要
                    "source": self.SOURCE,
                })
                
            except Exception as e:
                logger.warning(f"解析li失败: {e}")
                continue
        
        logger.info(f"解析出 {len(records)} 条记录")
        return records
    
    def crawl_all(self, max_count: int = 5) -> List[Dict]:
        """
        抓取数据，只获取最新的max_count条
        
        Args:
            max_count: 最大条数限制
        """
        # 抓取第1页
        html = self.fetch_page(1)
        
        if not html:
            logger.warning("获取页面失败")
            return []
        
        # 解析
        records = self.parse_html(html)
        
        if not records:
            logger.warning("解析不出数据")
            return []
        
        # 只取前max_count条
        result = records[:max_count]
        logger.info(f"获取到 {len(result)} 条记录（限制{max_count}条）")
        
        return result


def test():
    """测试函数"""
    print("=" * 60)
    print("测试ccgp爬虫（Scrapling版）")
    print("=" * 60)
    
    crawler = CcgpCrawler()
    records = crawler.crawl_all(max_count=5)
    
    print(f"\n获取到 {len(records)} 条记录：\n")
    for i, r in enumerate(records, 1):
        print(f"{i}. [{r['webdate']}] {r['title'][:50]}...")
        print(f"   URL: {r['linkurl'][:60]}...")


if __name__ == "__main__":
    test()
