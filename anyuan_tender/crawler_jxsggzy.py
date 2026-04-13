"""
网站4：江西省公共资源交易平台 (jxsggzy.cn)
API接口：POST http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew
"""

import requests
import time
import logging
import re
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retry_request(max_retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i < max_retries - 1:
                        logger.warning(f"请求失败，重试 {i+1}/{max_retries}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"请求最终失败: {e}")
                        raise
        return wrapper
    return decorator


class JxsggzyCrawler:
    """江西省公共资源交易平台爬虫"""
    
    BASE_URL = "http://www.jxsggzy.cn/XZinterface/rest/esinteligentsearch/getFullTextDataNew"
    KEYWORD = "安远"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Referer": "http://www.jxsggzy.cn/jiangxisearch/fullsearch.html"
        })
        # 禁用代理
        self.session.trust_env = False
    
    @retry_request(max_retries=3, delay=2)
    def fetch_page(self, page_index: int = 1, page_size: int = 10) -> Optional[Dict]:
        """
        获取指定页数据
        """
        pn = (page_index - 1) * page_size
        
        payload = {
            "token": "",
            "pn": pn,
            "rn": page_size,
            "sdt": "",
            "edt": "",
            "wd": self.KEYWORD,
            "inc_wd": "",
            "exc_wd": "",
            "fields": "title;content",
            "cnum": "",
            "sort": "{\"webdate\":0}",
            "ssort": "title",
            "cl": 500,
            "terminal": "",
            "condition": None,
            "time": None,
            "highlights": "title;content",
            "statistics": None,
            "unionCondition": None,
            "accuracy": "",
            "noParticiple": "1",
            "searchRange": None
        }
        
        logger.info(f"请求第 {page_index} 页，每页 {page_size} 条")
        
        resp = self.session.post(
            self.BASE_URL,
            json=payload,
            timeout=30
        )
        
        resp.raise_for_status()
        data = resp.json()
        
        if "result" not in data:
            logger.error(f"API返回数据格式异常: {data}")
            return None
            
        return data["result"]
    
    def parse_records(self, result: Dict) -> List[Dict]:
        """解析API返回的记录"""
        if not result or "records" not in result:
            return []
        
        records = []
        for r in result["records"]:
            link = r.get("linkurl", "")
            if link and not link.startswith("http"):
                link = "http://www.jxsggzy.cn" + link
            
            records.append({
                "title": self._clean_html(r.get("title", "")),
                "webdate": r.get("webdate", ""),
                "linkurl": link,
                "content": self._clean_html(r.get("content", "")),
                "categoryname": r.get("categoryname", ""),
                "zhaobiaofangshi": r.get("zhaobiaofangshi", ""),
                "xiaquname": r.get("xiaquname", ""),
                "infoid": r.get("infoid", ""),
            })
        
        return records
    
    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    
    def crawl_all(self, max_pages: int = 1, page_size: int = 5) -> List[Dict]:
        """抓取多页数据，默认只抓1页5条"""
        all_records = []
        total_count = 0
        
        for page in range(1, max_pages + 1):
            try:
                result = self.fetch_page(page, page_size)
                if not result:
                    break
                
                if page == 1:
                    total_count = result.get("totalcount", 0)
                    logger.info(f"总共 {total_count} 条记录，抓取前 {page_size} 条")
                
                records = self.parse_records(result)
                if not records:
                    logger.info(f"第 {page} 页无数据，停止抓取")
                    break
                
                all_records.extend(records)
                logger.info(f"获取 {len(records)} 条记录")
                
                # 只抓1页就够
                break
                
            except Exception as e:
                logger.error(f"抓取第 {page} 页失败: {e}")
                continue
        
        logger.info(f"抓取完成，共获取 {len(all_records)} 条记录")
        return all_records


def test():
    """测试函数"""
    crawler = JxsggzyCrawler()
    records = crawler.crawl_all(max_pages=2, page_size=5)
    
    print(f"\n获取到 {len(records)} 条记录：")
    for i, r in enumerate(records[:3], 1):
        print(f"\n--- 记录 {i} ---")
        print(f"标题: {r['title']}")
        print(f"时间: {r['webdate']}")
        print(f"链接: {r['linkurl']}")
        print(f"分类: {r['categoryname']}")


if __name__ == "__main__":
    test()
