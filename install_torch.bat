@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo    小吕布 - torch 快速修复/重装脚本（短路径安装）
echo ========================================================
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到 .venv 虚拟环境，请先创建虚拟环境！
    pause
    exit /b 1
)
set "TORCH_TARGET=%LOCALAPPDATA%\torchlib"
echo 目标安装目录: %TORCH_TARGET%
echo 正在安装 torch (CPU 版)...
".venv\Scripts\python.exe" -m pip install --target "%TORCH_TARGET%" torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo [失败] torch 安装失败，请检查网络后重试。
    pause
    exit /b 1
)
rem 生成 .pth 桥接文件，让虚拟环境能找到 torch
> ".venv\Lib\site-packages\torch_target.pth" echo %TORCH_TARGET%
".venv\Scripts\python.exe" -c "import torch; print('torch OK:', torch.__version__)"
echo.
echo ✅ torch 修复完成！可以重新启动 start.bat 了。
pause
