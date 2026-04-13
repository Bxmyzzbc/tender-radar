# 创建Windows计划任务
$scriptPath = "C:\Users\陈亮\.openclaw\workspace\anyuan_tender\main.py"
$pythonPath = "C:\Users\陈亮\AppData\Local\Programs\Python\Python312\python.exe"

# 删除已存在的任务（如果有）
schtasks /delete /tn "AnyuanTenderCrawler" /f 2>$null

# 创建新任务
$cmd = "$pythonPath `"$scriptPath`" --pages 5"
schtasks /create /tn "AnyuanTenderCrawler" /tr $cmd /sc daily /st 18:00 /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "计划任务创建成功！"
    Write-Host "任务名称: AnyuanTenderCrawler"
    Write-Host "运行时间: 每天 18:00"
    Write-Host "运行命令: $cmd"
} else {
    Write-Host "创建失败，退出码: $LASTEXITCODE"
}

# 显示任务信息
schtasks /query /tn "AnyuanTenderCrawler" /fo list 2>$null
