@echo off
:: 强制UTF-8，防止乱码
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo        🛡️ 小吕布 - 自动寻路启动模式
echo ========================================================

:: 1. 先检查粮草（虚拟环境）在不在
if not exist ".venv\Scripts\python.exe" (
    echo [大怒] 找不到虚拟环境 .venv！请确认文件夹是否完整！
    pause
    exit
)

:: 2. 第一策：看看 app.py 是否就在脚下（根目录）
if exist "app.py" (
    echo [发现] 主帅 app.py 就在大营！准备出征！
    ".venv\Scripts\python.exe" -m streamlit run app.py
    goto end
)

:: 3. 第二策：看看 app.py 是否藏在 DL_Quant_System 营寨里
if exist "DL_Quant_System\app.py" (
    echo [发现] 主帅 app.py 藏在子目录中！正在前往...
    ".venv\Scripts\python.exe" -m streamlit run "DL_Quant_System\app.py"
    goto end
)

:: 4. 如果两处都找不到，那就是真丢了
echo.
echo [崩溃] 挖地三尺也没找到 app.py！
echo.
echo 请主公确认：您的 app.py 到底放在哪个文件夹里了？
echo 当前目录文件列表如下：
dir /b
echo.

:end
pause