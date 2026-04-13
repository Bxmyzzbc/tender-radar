"""
安远招标公告爬虫 - 主程序
多数据源：整合jxsggzy、ccgp、zfcg三个数据源
"""

import os
import json
import logging
from datetime import datetime

# 配置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f"crawler_{datetime.now().strftime('%Y%m%d')}.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入各模块
from crawler_jxsggzy import JxsggzyCrawler
from crawler_ccgp import CcgpCrawler
from crawler_zfcg import ZfcgCrawler
from classifier_ict import classify
from deduplicator import Deduplicator
from content_dedup import deduplicate_by_content
from feishu_sender import send_result_to_feishu


class TenderCrawler:
    """招标公告爬虫主类"""
    
    def __init__(self, keyword: str = "安远", output_dir: str = "output"):
        self.keyword = keyword
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化各数据源爬虫
        self.crawlers = {
            "jxsggzy": JxsggzyCrawler(),
            "ccgp": CcgpCrawler(),
            "zfcg": ZfcgCrawler(),
        }
        
        # 初始化去重模块
        self.dedup = Deduplicator("jxsggzy_history.json")
        
        # 统计
        self.stats = {
            "total_fetched": 0,
            "skipped": 0,
            "new_urls": 0,
            "ict_count": 0,
            "non_ict_count": 0,
            "sources": {},
        }
    
    def _deduplicate_by_title(self, records: list) -> list:
        """标题去重：如果标题相同，只保留最新的一条"""
        seen_titles = {}
        result = []
        
        for r in records:
            title = r.get("title", "")
            date = r.get("date", "")
            
            if title not in seen_titles:
                seen_titles[title] = date
                result.append(r)
            else:
                if date > seen_titles[title]:
                    for i, existing in enumerate(result):
                        if existing.get("title") == title:
                            result[i] = r
                            seen_titles[title] = date
                            break
        
        return result
    
    def _merge_records(self, all_records: list) -> list:
        """合并去重：基于URL去重"""
        seen_urls = set()
        result = []
        
        for r in all_records:
            url = r.get("linkurl", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                result.append(r)
        
        return result
    
    def run(self, max_per_source: int = 5):
        """运行爬虫"""
        logger.info(f"=== 开始抓取 '{self.keyword}' 相关招标公告 ===")
        start_time = datetime.now()
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_records = []
        
        # ========== 步骤1: 依次抓取各数据源 ==========
        logger.info("[步骤1] 抓取各数据源...")
        
        for source_name, crawler in self.crawlers.items():
            try:
                logger.info(f"--- 抓取 {source_name} ---")
                
                if source_name == "jxsggzy":
                    records = crawler.crawl_all(max_pages=1, page_size=max_per_source)
                elif source_name == "ccgp":
                    records = crawler.crawl_all(max_count=max_per_source)
                elif source_name == "zfcg":
                    records = crawler.crawl_all(max_count=max_per_source)
                
                # 添加来源标识
                for r in records:
                    r["source"] = source_name
                
                all_records.extend(records)
                self.stats["sources"][source_name] = len(records)
                logger.info(f"  {source_name} 获取 {len(records)} 条")
                
            except Exception as e:
                logger.error(f"  {source_name} 抓取失败: {e}")
                self.stats["sources"][source_name] = 0
        
        self.stats["total_fetched"] = len(all_records)
        logger.info(f"共抓取 {len(all_records)} 条公告")
        
        if not all_records:
            logger.warning("未抓取到任何数据")
            return None
        
        # ========== 步骤2: URL去重 ==========
        logger.info("[步骤2] URL去重...")
        new_records = []
        for r in all_records:
            if self.dedup.is_seen(r):
                self.stats["skipped"] += 1
            else:
                new_records.append(r)
                self.dedup.add_seen(r)
        
        self.stats["new_urls"] = len(new_records)
        logger.info(f"跳过 {self.stats['skipped']} 条已爬取，新增 {len(new_records)} 条")
        
        if not new_records:
            logger.info("没有新增数据")
            # 发送无新公告通知
            try:
                from feishu_sender import send_no_new_notice
                send_no_new_notice()
            except Exception as e:
                logger.error(f"飞书推送失败: {e}")
            return None
        
        # ========== 步骤3: 内容去重（基于项目名称相似度） ==========
        logger.info("[步骤3] 内容去重（多数据源重复检测）...")
        before_count = len(new_records)
        new_records = deduplicate_by_content(new_records, threshold=0.70)
        after_count = len(new_records)
        logger.info(f"内容去重: {before_count} -> {after_count} 条（过滤 {before_count - after_count} 条重复）")
        
        # ========== 步骤4: ICT分类 ==========
        logger.info("[步骤4] ICT分类...")
        ict_list = []
        non_ict_list = []
        
        for r in new_records:
            # 拼接标题+内容用于分类
            text = (r.get("title", "") + " " + r.get("content", "")).strip()
            category = classify(text)
            
            record = {
                "title": r.get("title", ""),
                "date": r.get("webdate", "")[:10] if r.get("webdate") else "",
                "url": r.get("linkurl", ""),
                "source": r.get("source", ""),
            }
            
            if category == "ICT招标类公告":
                ict_list.append(record)
            else:
                non_ict_list.append(record)
        
        self.stats["ict_count"] = len(ict_list)
        self.stats["non_ict_count"] = len(non_ict_list)
        
        # ========== 步骤5: 标题去重 ==========
        logger.info("[步骤5] 标题去重...")
        ict_list = self._deduplicate_by_title(ict_list)
        non_ict_list = self._deduplicate_by_title(non_ict_list)
        logger.info(f"去重后: ICT={len(ict_list)}, 非ICT={len(non_ict_list)}")
        
        # ========== 步骤6: 排序（按时间降序） ==========
        logger.info("[步骤6] 排序...")
        ict_list.sort(key=lambda x: x["date"], reverse=True)
        non_ict_list.sort(key=lambda x: x["date"], reverse=True)
        
        # ========== 步骤7: 截断（最多各5条） ==========
        logger.info("[步骤7] 截断（ICT最多5条，非ICT最多5条）...")
        ict_list = ict_list[:5]
        non_ict_list = non_ict_list[:5]
        
        # ========== 步骤8: 保存结果 ==========
        logger.info("[步骤8] 保存JSON结果...")
        result = {
            "date": today,
            "ICT": ict_list,
            "NON_ICT": non_ict_list,
        }
        
        result_file = os.path.join(self.output_dir, f"result_{today}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存: {result_file}")
        
        # ========== 步骤9: 保存history ==========
        self.dedup._save_history()
        
        # ========== 步骤10: 发送飞书通知 ==========
        logger.info("[步骤10] 发送飞书通知...")
        try:
            send_result_to_feishu(result_file)
        except Exception as e:
            logger.error(f"飞书推送失败（不影响主流程）: {e}")
        
        # ========== 完成 ==========
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== 抓取完成，耗时 {elapsed:.1f} 秒 ===")
        logger.info(f"统计: 总抓取={self.stats['total_fetched']}, "
                   f"新增={self.stats['new_urls']}, "
                   f"ICT={len(ict_list)}, "
                   f"非ICT={len(non_ict_list)}")
        for src, cnt in self.stats["sources"].items():
            logger.info(f"  {src}: {cnt} 条")
        
        return result


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="安远招标公告爬虫")
    parser.add_argument("--keyword", "-k", default="安远", help="搜索关键词")
    parser.add_argument("--max", "-m", type=int, default=5, help="每个数据源最多抓取条数")
    parser.add_argument("--output", "-o", default="output", help="输出目录")
    
    args = parser.parse_args()
    
    crawler = TenderCrawler(keyword=args.keyword, output_dir=args.output)
    result = crawler.run(max_per_source=args.max)
    
    if result:
        print(f"\n今日结果 ({result['date']}):")
        print(f"ICT类: {len(result['ICT'])} 条")
        for i, item in enumerate(result['ICT'], 1):
            print(f"  {i}. [{item['date']}] {item['title'][:40]}... [{item.get('source', '')}]")
        
        print(f"\n非ICT类: {len(result['NON_ICT'])} 条")
        for i, item in enumerate(result['NON_ICT'], 1):
            print(f"  {i}. [{item['date']}] {item['title'][:40]}... [{item.get('source', '')}]")


if __name__ == "__main__":
    main()
