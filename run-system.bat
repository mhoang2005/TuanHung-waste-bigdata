@echo off
chcp 65001 >nul
title Khoi dong Tram Dieu Phoi Rac Tuan Hung

echo ========================================================
echo         KHOI DONG TRAM DIEU PHOI RAC TUAN HUNG
echo ========================================================

:: 0. Giai phong cong 8000 neu co ung dung chay nen khac (vd: Signal Forge) dang chiem
if exist "C:\Users\PC FUJISU\OneDrive\Documents\New project\backend\data\runtime_state" (
    echo stop > "C:\Users\PC FUJISU\OneDrive\Documents\New project\backend\data\runtime_state\watchdog_daemon.stop"
    echo stop > "C:\Users\PC FUJISU\OneDrive\Documents\New project\backend\data\runtime_state\long_run.stop"
)

:: 1. Kiem tra Docker Desktop
echo [1/4] Kiem tra Docker Desktop...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker chua chay. Dang mo Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Dang doi Docker Desktop khoi dong...
    :wait_docker
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto wait_docker
)
echo       - Docker Desktop da san sang!

:: 2. Chuyen vao thu muc bigdata (ho tro chay tu thu muc goc hoac trong bigdata)
if exist "%~dp0bigdata\compose.yaml" (
    cd /d "%~dp0bigdata"
) else if exist "%~dp0compose.yaml" (
    cd /d "%~dp0"
) else (
    echo [LOI] Khong tim thay file compose.yaml!
    pause
    exit /b 1
)

:: 3. Bat cac container Docker Compose
echo [2/4] Dang bat cac container Docker Compose...
docker compose up -d
docker compose port app 8000 >nul 2>&1
if %errorlevel% neq 0 (
    docker compose up -d --force-recreate app
)

:: 4. Doi Web API san sang va mo trinh duyet
echo [3/4] Dang doi Web Dashboard (http://localhost:8000) san sang...
:wait_api
timeout /t 2 /nobreak >nul
curl.exe -s -f http://localhost:8000/api/control >nul 2>&1
if %errorlevel% neq 0 goto wait_api

echo [4/4] He thong da san sang! Dang mo trinh duyet...
start http://localhost:8000

echo.
echo ========================================================
echo  Dashboard Chinh : http://localhost:8000
echo  Spark Master UI : http://localhost:8089
echo  Spark Driver UI : http://localhost:4040
echo  HDFS NameNode   : http://localhost:9870
echo ========================================================
echo.
pause
