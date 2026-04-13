# 安远招标公告爬虫

多数据源政府采购/招标公告爬取系统，自动抓取、分类、去重，支持每日定时运行和飞书推送。

---

## 功能特点

- **多数据源整合**：江西省公共资源交易平台、中国政府采购网、江西省政府采购网
- **智能去重**：URL 去重 + 标题去重 + 基于项目名称相似度的内容去重
- **ICT 分类**：自动识别信息化（ICT）相关招标公告
- **每日定时**：通过 Windows 计划任务每天 18:00 自动运行
- **飞书推送**（可选）：抓取结果可推送到飞书群

---

## 项目结构

```
anyuan_tender/
├── main.py                 # 主程序入口
├── scheduler.py            # 定时任务调度器
├── create_task.py          # 创建 Windows 计划任务
├── create_task.ps1         # PowerShell 计划任务脚本
│
├── 数据源爬虫/
│   ├── crawler_jxsggzy.py  # 江西省公共资源交易平台（API）
│   ├── crawler_ccgp.py     # 中国政府采购网（Scrapling）
│   └── crawler_zfcg.py     # 江西省政府采购网（Scrapling）
│
├── 处理模块/
│   ├── classifier_ict.py   # ICT 招标分类器（两层判断）
│   ├── deduplicator.py     # URL 去重
│   └── content_dedup.py    # 内容去重（项目名称相似度）
│
├── feishu_sender.py        # 飞书推送（可选）
├── view_results.py         # 快速查看最近结果
│
├── output/                 # 抓取结果输出目录
├── logs/                   # 日志目录
└── jxsggzy_history.json    # URL 去重历史记录
```

---

## 数据来源

| 数据源 | 技术方案 | 网址 | 备注 |
|--------|---------|------|------|
| 江西省公共资源交易平台 | requests API | jxsggzy.cn | 速度快，有 URL |
| 中国政府采购网 | Scrapling（JS 渲染） | ccgp.gov.cn | 绕过反爬，有 URL |
| 江西省政府采购网 | Scrapling（JS 渲染） | zfcg.jxf.gov.cn | Vue 动态页面，部分无 URL |

---

## 处理流程

```
抓取各数据源
    ↓
[步骤1] URL去重（基于历史记录）
    ↓
[步骤2] 内容去重（项目名称相似度 ≥ 70%）
    ↓
[步骤3] ICT分类
    ↓
[步骤4] 标题去重
    ↓
[步骤5] 按时间降序排序
    ↓
[步骤6] 截断输出（ICT ≤5条，非ICT ≤5条）
    ↓
输出JSON / 推送飞书
```

---

## ICT 分类逻辑

### 第一层：公告类型判断

**允许进入 ICT 判断的关键词：**
- 招标公告、采购公告、公开招标
- 竞争性谈判、竞争性磋商、邀请招标
- 询价公告、竞价公告

**直接排除的关键词：**
- 流标、废标、终止公告、暂停公告
- 中标结果、中标公告、中标候选人
- 成交结果、成交公告、结果公示

### 第二层：ICT 关键词匹配

识别以下类型的招标：
- 信息化项目（智慧城市、数字化、信息化）
- 系统集成、网络建设、软件开发
- 服务器、存储、网络安全设备
- 大数据、人工智能、物联网

---

## 安装依赖

```bash
pip install scrapling requests
```

> scrapling 会自动下载 Chromium 浏览器（约 150MB）

---

## 使用方法

### 手动运行

```bash
cd anyuan_tender
python main.py
```

### 定时运行（每天 18:00）

```bash
python create_task.py
```

这会创建一个名为 `AnyuanTenderCrawler` 的 Windows 计划任务，每天 18:00 自动执行 `python main.py`。

---

## 输出格式

运行后在 `output/result_YYYY-MM-DD.json` 生成结果文件：

```json
{
  "date": "2026-04-13",
  "run_time": "18:00:00",
  "stats": {
    "total_fetched": 15,
    "skipped": 10,
    "new_urls": 5,
    "ict_count": 3,
    "non_ict_count": 2,
    "sources": {
      "jxsggzy": 5,
      "ccgp": 5,
      "zfcg": 5
    }
  },
  "ICT": [
    {
      "title": "安远县智慧城市建设项目",
      "date": "2026-04-13",
      "source": "jxsggzy",
      "linkurl": "https://..."
    }
  ],
  "NON_ICT": [
    {
      "title": "办公家具采购公告",
      "date": "2026-04-12",
      "source": "ccgp",
      "linkurl": "https://..."
    }
  ]
}
```

---

## 配置说明

### 修改爬取关键词

在 `main.py` 中修改：

```python
crawler = TenderCrawler(keyword="安远")  # 改成其他关键词
```

### 修改输出数量

```python
crawler.run(max_per_source=5)  # 每个数据源最多抓取5条
```

### 修改定时时间

编辑 `scheduler.py` 或重新运行 `create_task.py`：

```python
scheduler = Scheduler(hour=18, minute=0)  # 改成 18:30 等
```

---

## 飞书推送（可选）

需要配置飞书机器人 Webhook URL，编辑 `feishu_sender.py` 中的：

```python
FEISHU_WEBHOOK = "your-webhook-url-here"
```

---

## 注意事项

1. **首次运行**：scrapling 需要下载 Chromium，约 150MB
2. **URL 去重**：已爬取过的 URL 会被跳过，如需重新抓取，删除 `jxsggzy_history.json`
3. **zfcg 数据源**：江西省政府采购网搜索结果不提供详情页 URL
4. **运行时长**：完整抓取 3 个数据源约需 1-2 分钟

---

## 常见问题

**Q: 运行时显示"SSL 证书错误"？**
> 检查网络连接，部分数据源可能需要 VPN。

**Q: 如何查看更多日志？**
> 日志文件在 `logs/crawler_YYYYMMDD.log`

**Q: 如何清除已去重的历史记录？**
> 删除 `jxsggzy_history.json` 文件

**Q: 飞书推送失败？**
> 检查 Webhook URL 是否正确，机器人是否未被禁用
