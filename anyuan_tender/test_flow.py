import json
import os

hist_file = 'C:/Users/陈亮/.openclaw/workspace/anyuan_tender/jxsggzy_history.json'
if os.path.exists(hist_file):
    print(f'历史文件存在，大小: {os.path.getsize(hist_file)} bytes')
    with open(hist_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(f'已记录URL数量: {len(data.get("seen_ids", []))}')
else:
    print('历史文件不存在')
