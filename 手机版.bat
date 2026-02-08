@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo      🛡️ 小吕布 - 手机远程连接模式
echo ==================================================
echo.
echo 请拿出手机，确保连接了同一个 WiFi。
echo 然后在手机浏览器输入下面 【IPv4 地址】 这一行的数字:
echo 例如看到: IPv4 地址 . . . 192.168.1.5
echo 就输入: http://192.168.1.5:8501
echo.
echo ================= [ 您的 IP 地址 ] =================
ipconfig | findstr "IPv4"
echo ==================================================
echo.

:: 启动允许外部访问模式
".venv\Scripts\python.exe" -m streamlit run app.py --server.address=0.0.0.0
pause