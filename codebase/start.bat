@echo off
chcp 65001 >nul
title VinpearlAI — Backend Server

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   MyVinpearl AI Booking Assistant        ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Kiểm tra .env
if not exist ".env" (
    echo  [!] Chưa có file .env
    echo  [!] Tạo .env từ .env.example:
    echo      copy .env.example .env
    echo  [!] Sau đó điền OPENAI_API_KEY vào .env
    echo.
    pause
    exit /b 1
)

:: Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Python chưa được cài đặt
    echo  [!] Tải tại: https://python.org/downloads
    pause
    exit /b 1
)

:: Cài packages nếu chưa có
echo  [*] Kiểm tra dependencies...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo  [*] Cài đặt dependencies (lần đầu chạy)...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo  [!] Lỗi cài packages. Xem lại requirements.txt
        pause
        exit /b 1
    )
)

echo  [*] Khởi động server...
echo.
echo  Frontend: http://localhost:8000
echo  API docs: http://localhost:8000/docs
echo.

:: Chạy từ thư mục src/
cd src
python main.py

pause
