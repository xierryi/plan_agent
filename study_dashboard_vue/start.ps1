# StudyAgent Vue 版本启动脚本 (Windows PowerShell)

Write-Host "🚀 启动 StudyAgent Vue 版本..." -ForegroundColor Cyan

# 启动后端
Write-Host "`n📦 启动后端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate; python main.py"

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端
Write-Host "`n🎨 启动前端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n✅ 服务已启动!" -ForegroundColor Green
Write-Host "前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "后端: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor Cyan
