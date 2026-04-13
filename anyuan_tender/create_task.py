# encoding: utf-8
# 创建Windows计划任务
import subprocess
import sys
import os

scriptPath = r"C:\Users\陈亮\.openclaw\workspace\anyuan_tender\main.py"
pythonPath = r"C:\Users\陈亮\AppData\Local\Programs\Python\Python312\python.exe"

# 删除已存在的任务
subprocess.run(["schtasks", "/delete", "/tn", "AnyuanTenderCrawler", "/f"], 
               capture_output=True)

# 创建新任务
cmd = f'"{pythonPath}" "{scriptPath}" --pages 5'
result = subprocess.run(
    ["schtasks", "/create", "/tn", "AnyuanTenderCrawler", "/tr", cmd, 
     "/sc", "daily", "/st", "18:00", "/f"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("计划任务创建成功!")
    print("任务名称: AnyuanTenderCrawler")
    print("运行时间: 每天 18:00")
else:
    print("创建失败:", result.stderr)
