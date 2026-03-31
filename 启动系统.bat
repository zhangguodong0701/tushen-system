@echo off
chcp 65001 >nul
title 图审云平台 - 启动服务

echo ========================================
echo          图审云平台 启动中...
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/2] 安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查Python环境
    pause
    exit /b 1
)

echo [2/2] 启动后端服务 (端口 8000)...
start "图审后端服务" cmd /k "python main.py"
timeout /t 2 /nobreak >nul

echo.
echo ✅ 后端服务已启动: http://localhost:8000
echo ✅ API文档地址:     http://localhost:8000/docs
echo.
echo 正在打开前端界面...
start "" "%~dp0frontend\index.html"

echo.
echo 系统已启动完成！
echo 管理员账号: 13800000000 / admin123
echo.
pause
