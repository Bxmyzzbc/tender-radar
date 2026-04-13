"""
ICT项目分类器
两层判断逻辑：
1. 第一层：判断是否为"招标公告"类型
2. 第二层：ICT判断（仅对招标公告执行）
"""

# ==================== 第一层：公告类型判断 ====================

# 允许进入ICT判断的"招标公告"类型关键词
TENDER_KEYWORDS = [
    "招标公告", "采购公告", "公开招标", "竞争性谈判", 
    "竞争性磋商", "邀请招标", "询价公告", "竞价公告",
    "电子化招标", "电子化采购", "谈判公告", "磋商公告",
]

# 直接判定为"其他类型"的关键词
# 注意：只包含明确表示"招标已失败/结束/已完成"的类型
# 不包含正文标准条款词（如"合同"、"补充"、"澄清"等）
INVALID_KEYWORDS = [
    # ====== 明确表示"招标已失败/终止"的类型 ======
    "流标", "废标", "终止公告", "暂停公告", "停标",
    
    # ====== 明确表示"已确定中标方"的类型 ======
    "中标结果", "中标公告", "中标公示", "中标候选人",
    "成交结果", "成交公告", "成交公示",
    "结果公示", "结果公告",
    
    # ====== 其他非招标公告类型 ======
    "合同公示", "验收公示", "投诉处理",
]


def is_tender_announcement(text: str) -> bool:
    """
    判断是否为招标公告类型
    
    只有包含TENDER_KEYWORDS中关键词的公告才会进入ICT判断
    """
    if not text:
        return False
    text_lower = text.lower()
    
    for keyword in TENDER_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def is_invalid_type(text: str) -> bool:
    """
    判断是否属于流标/废标/终止/中标/成交等非招标公告类型
    
    一旦匹配，直接归类为"其他类型"，不再进行ICT判断
    """
    if not text:
        return False
    text_lower = text.lower()
    
    for keyword in INVALID_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


# ==================== 第二层：ICT判断 ====================

# ICT关键词
ICT_KEYWORDS = [
    "信息化", "信息系统", "系统集成", "软件开发", "软件平台",
    "应用软件", "管理软件", "数据库", "云平台", "云计算",
    "网络工程", "网络安全", "网络设备", "网络维护",
    "交换机", "路由器", "防火墙", "网线",
    "大数据", "数据中心", "数据平台", "数据分析",
    "人工智能", "AI", "智慧城市", "智慧", "智能",
    "服务器", "存储设备", "计算机", "电脑",
    "监控系统", "安防系统", "门禁系统", "考勤系统",
    "视频会议", "广播系统", "多媒体系统", "LED屏",
    "显示屏", "投影仪", "打印机", "扫描仪",
    "机房", "IT设备", "办公设备",
]


def is_ict(text: str) -> bool:
    """
    判断是否为ICT项目（两层判断后的第二层）
    
    只有通过了is_tender_announcement且不是is_invalid_type的公告才会执行此判断
    """
    if not text:
        return False
    text_lower = text.lower()
    
    # 统计匹配的ICT关键词数
    matched = []
    for keyword in ICT_KEYWORDS:
        if keyword.lower() in text_lower:
            matched.append(keyword)
    
    # 匹配1个及以上ICT关键词即认为是ICT
    return len(matched) >= 1


def get_keywords(text: str) -> dict:
    """获取文本中匹配的所有关键词"""
    if not text:
        return {"is_tender": False, "is_invalid": False, "is_ict": False,
                "tender_keywords": [], "invalid_keywords": [], "ict_keywords": []}
    
    text_lower = text.lower()
    
    tender_kw = [k for k in TENDER_KEYWORDS if k in text_lower]
    invalid_kw = [k for k in INVALID_KEYWORDS if k in text_lower]
    ict_kw = [k for k in ICT_KEYWORDS if k.lower() in text_lower]
    
    return {
        "is_tender": len(tender_kw) > 0,
        "is_invalid": len(invalid_kw) > 0,
        "is_ict": len(ict_kw) > 0,
        "tender_keywords": tender_kw,
        "invalid_keywords": invalid_kw,
        "ict_keywords": ict_kw,
    }


def classify(text: str) -> str:
    """
    最终分类函数
    
    逻辑：
    1. 如果是流标/废标/终止/中标/成交等 → "其他类型"
    2. 如果是招标公告类型 → 判断ICT：
       - ICT匹配 → "ICT招标类公告"
       - 不匹配 → "其他类型"
    3. 其他 → "其他类型"
    """
    if not text:
        return "其他类型"
    
    kw_info = get_keywords(text)
    
    # 第一步：流标/废标/终止/中标/成交等 → 直接排除
    if kw_info["is_invalid"]:
        return "其他类型"
    
    # 第二步：只有招标公告类型才进行ICT判断
    if kw_info["is_tender"]:
        if kw_info["is_ict"]:
            return "ICT招标类公告"
    
    return "其他类型"


def classify_record(title: str, content: str = "") -> str:
    """对单条记录进行分类（使用标题+内容）"""
    text = (title or "") + " " + (content or "")
    return classify(text)


# ==================== 测试 ====================

def test():
    """测试分类逻辑"""
    test_cases = [
        # (标题+正文, 预期结果)
        ("安远县信息化建设项目招标公告", "ICT招标类公告"),
        ("安远县殡葬服务中心丧葬用品采购竞争性磋商公告 合同履行期限一年", "其他类型"),
        ("安远县网络工程公开招标公告", "ICT招标类公告"),
        ("安远县殡葬服务中心物资配送服务流标公告 正文含合同条款", "其他类型"),
        ("安远县办公设备采购项目废标公告 正文含补充条款", "其他类型"),
        ("安远县服务器采购竞争性谈判公告", "ICT招标类公告"),
        ("安远县智慧城市建设招标公告", "ICT招标类公告"),
        ("安远县供水工程中标结果公告 正文含合同条款", "其他类型"),
        ("安远县信息化建设工程更正公告", "其他类型"),
        ("安远县系统集成项目竞争性磋商公告 正文含补充事宜", "其他类型"),  # 更正=排除
        ("安远县园林绿化采购竞争性磋商公告 正文含合同条款", "其他类型"),
        ("安远县数据平台建设项目招标公告", "ICT招标类公告"),
        ("安远县第一中学标准化考场广播系统竞争性磋商公告 合同履行期限一年", "ICT招标类公告"),
    ]
    
    print("=" * 70)
    print("分类逻辑测试")
    print("=" * 70)
    
    correct = 0
    for text, expected in test_cases:
        result = classify(text)
        status = "✓" if result == expected else "✗"
        if result == expected:
            correct += 1
        
        kw = get_keywords(text)
        print(f"\n{status} [{result}] {text[:50]}...")
        if kw["invalid_keywords"]:
            print(f"   排除词: {kw['invalid_keywords']}")
        if kw["tender_keywords"]:
            print(f"   招标词: {kw['tender_keywords']}")
        if kw["ict_keywords"]:
            print(f"   ICT词: {kw['ict_keywords']}")
    
    print(f"\n{'=' * 70}")
    print(f"正确率: {correct}/{len(test_cases)} ({100*correct/len(test_cases):.1f}%)")


if __name__ == "__main__":
    test()
