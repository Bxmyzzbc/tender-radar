"""
飞书机器人推送模块
将爬取结果通过飞书Webhook发送到群
"""

import requests
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 飞书Webhook地址
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v"


def send_feishu_message(webhook: str, message: str) -> bool:
    """
    向飞书Webhook发送消息
    
    Args:
        webhook: 飞书机器人Webhook地址
        message: 要发送的文本消息
    
    Returns:
        True=发送成功, False=发送失败
    """
    try:
        data = {
            "msg_type": "text",
            "content": {"text": message}
        }
        
        response = requests.post(webhook, json=data, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and result.get("code") == 0:
            logger.info("飞书消息发送成功")
            return True
        else:
            logger.error(f"飞书消息发送失败: {result}")
            return False
            
    except Exception as e:
        logger.error(f"飞书消息发送异常: {e}")
        return False


def format_message(json_file: str) -> str:
    """
    将JSON结果文件转换为飞书消息文本
    
    Args:
        json_file: JSON文件路径
    
    Returns:
        格式化后的消息文本
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        date = data.get("date", "")
        ict_list = data.get("ICT", [])
        non_ict_list = data.get("NON_ICT", [])
        
        # 构建消息（必须包含关键词"安远招标"）
        lines = ["安远招标"]
        lines.append("🔔 监控日报")
        lines.append(f"📅 {date}")
        
        # ICT招标类
        if ict_list:
            lines.append("📡 ICT招标类：")
            for i, item in enumerate(ict_list[:5], 1):  # 最多5条
                title = item.get("title", "")[:50]  # 标题截断
                item_date = item.get("date", "")
                url = item.get("url", "")
                lines.append(f"{i}. {title}")
                lines.append(f"   🕐 {item_date}")
                if url:
                    lines.append(f"   🔗 {url}")
                lines.append("")
        else:
            lines.append("📡 ICT招标类：暂无")
            lines.append("")
        
        # 其他公告
        if non_ict_list:
            lines.append("📄 其他公告：")
            for i, item in enumerate(non_ict_list[:5], 1):  # 最多5条
                title = item.get("title", "")[:50]  # 标题截断
                item_date = item.get("date", "")
                url = item.get("url", "")
                lines.append(f"{i}. {title}")
                lines.append(f"   🕐 {item_date}")
                if url:
                    lines.append(f"   🔗 {url}")
                lines.append("")
        else:
            lines.append("📄 其他公告：暂无")
            lines.append("")
        
        # 限制总长度
        message = "\n".join(lines)
        if len(message) > 4000:
            message = message[:4000] + "\n...(内容过长已截断)"
        
        return message
        
    except Exception as e:
        logger.error(f"格式化消息失败: {e}")
        return f"【安远招标监控】\n消息格式化失败: {e}"


def send_result_to_feishu(json_file: str, webhook: str = FEISHU_WEBHOOK) -> bool:
    """
    发送爬取结果到飞书群
    
    Args:
        json_file: JSON结果文件路径
        webhook: 飞书Webhook地址（可选）
    
    Returns:
        True=发送成功, False=发送失败
    """
    logger.info("正在发送结果到飞书...")
    
    # 格式化消息
    message = format_message(json_file)
    
    # 发送
    success = send_feishu_message(webhook, message)
    
    if success:
        logger.info("飞书推送完成")
    else:
        logger.warning("飞书推送失败，但不影响主流程")
    
    return success


def send_no_new_notice(webhook: str = FEISHU_WEBHOOK) -> bool:
    """
    发送"今日无新公告"通知
    
    Args:
        webhook: 飞书Webhook地址
    
    Returns:
        True=发送成功, False=发送失败
    """
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    message = f"""安远招标
🔔 监控日报 - {today}

📭 今日暂无新公告

⏰ 自动监控系统运行正常"""
    
    return send_feishu_message(webhook, message)


if __name__ == "__main__":
    # 测试
    import os
    test_file = "output/result_2026-04-13.json"
    if os.path.exists(test_file):
        msg = format_message(test_file)
        print(msg)
        print("\n" + "="*50)
        send_result_to_feishu(test_file)
    else:
        print(f"测试文件不存在: {test_file}")
