"""
网站1：江西省政府采购网 (zfcg.jxf.gov.cn)
使用Scrapling绕过Vue动态渲染，获取JavaScript渲染内容
"""

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


class ZfcgCrawler:
    """江西省政府采购网爬虫 - 使用Scrapling"""
    
    BASE_URL = "https://zfcg.jxf.gov.cn/maincms-web/fullSearchingJx"
    KEYWORD = "安远"
    SOURCE = "zfcg"
    
    def __init__(self):
        self.fetcher = StealthyFetcher()
    
    def fetch_page(self, page_index: int = 1) -> bytes:
        """使用Scrapling获取页面HTML"""
        url = f"{self.BASE_URL}?searchKey={self.KEYWORD}&pageIndex={page_index}"
        
        logger.info(f"抓取第 {page_index} 页（等待15秒让Vue渲染）...")
        
        try:
            page = self.fetcher.fetch(
                url=url,
                headless=True,
                timeout=120000,
                wait=15000
            )
            
            logger.info(f"页面长度: {len(page.body)} 字节")
            return page.body
            
        except Exception as e:
            logger.error(f"抓取失败: {e}")
            return b""
    
    def parse_html(self, html: bytes) -> List[Dict]:
        """解析HTML，提取招标公告列表"""
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        if self.KEYWORD not in text:
            logger.warning(f"页面中未找到关键词'{self.KEYWORD}'")
            return []
        
        records = []
        
        # 日期模式
        date_pattern = r'(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        dates = [(d.start(), d.group(1)) for d in re.finditer(date_pattern, text)]
        
        # 标题模式 - 匹配完整的"XXX有限公司关于...公告/通知/结果/公示/变更"
        # 也匹配"XXX局关于..."等模式
        title_patterns = [
            r'([\u4e00-\u9fa5]*(?:有限公司|局|院|馆|校|处|部|集团)关于[^\n]{5,150}?(?:公告|通知|结果|公示|变更|更正|废标|终止))',
        ]
        
        all_titles = []
        for pattern in title_patterns:
            for m in re.finditer(pattern, text):
                title = m.group(1).strip()
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 15 and self.KEYWORD in title:
                    all_titles.append((m.start(), m.end(), title))
        
        # 按位置排序
        all_titles.sort(key=lambda x: x[0])
        
        # 为每个标题匹配日期
        for idx, (start, end, title) in enumerate(all_titles):
            # 找这个标题之后最近的日期
            next_date = None
            for pos, date_str in dates:
                if pos > end:
                    next_date = date_str
                    break
            
            if next_date:
                records.append({
                    "title": f"[安远县]{title}",
                    "linkurl": "",  # zfcg页面没有直接链接
                    "webdate": next_date,
                    "content": "",  # 暂时不需要详情
                    "source": self.SOURCE,
                })
        
        logger.info(f"解析出 {len(records)} 条记录")
        return records
    
    def crawl_all(self, max_count: int = 5) -> List[Dict]:
        """抓取数据"""
        html = self.fetch_page(1)
        
        if not html:
            logger.warning("获取页面失败")
            return []
        
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
    print("测试zfcg爬虫（Scrapling版）")
    print("=" * 60)
    
    crawler = ZfcgCrawler()
    records = crawler.crawl_all(max_count=5)
    
    print(f"\n获取到 {len(records)} 条记录：\n")
    for i, r in enumerate(records, 1):
        print(f"{i}. [{r.get('webdate', '')}]")
        print(f"   标题: {r.get('title', '')[:70]}...")
        print()


if __name__ == "__main__":
    test()
