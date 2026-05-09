@echo off
REM ============================================================
REM  WorkBuddy Skills Installer - 一键安装脚本
REM ============================================================
echo.
echo ============================================================
echo  WorkBuddy Skills 安装工具
echo ============================================================
echo.
echo 本脚本将依次安装当前目录下的3个技能包：
echo   1. Stata-run.zip
echo   2. python-run.zip
echo   3. 时间序列分析.zip
echo.
echo 安装目标: %%USERPROFILE%%\.workbuddy\skills\
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PowerShell not found. Please install skills manually.
    pause
    exit /b 1
)

REM Install each skill
for %%s in (Stata-run python-run 时间序列分析) do (
    if exist %%s.zip (
        echo [*] Installing %%s...
        powershell -Command "Expand-Archive -Path '%%s.zip' -DestinationPath '%USERPROFILE%\.workbuddy\skills\' -Force"
        if !ERRORLEVEL! EQU 0 (
            echo [OK] %%s installed successfully
        ) else (
            echo [ERROR] Failed to install %%s
        )
    ) else (
        echo [WARN] %%s.zip not found in current directory, skipping...
    )
)

echo.
echo ============================================================
echo  安装完成！
echo  在WorkBuddy对话框中输入以下指令验证：
echo    @skill://Stata-run  help
echo    @skill://python-run  help
echo    @skill://时间序列分析  help
echo ============================================================
echo.

REM Configure Stata path
echo.
echo 注意：如果您的Stata安装路径不是 D:\STATA\STATA14\Stata.exe，
echo 请在以下文件中修改路径：
echo   %%USERPROFILE%%\.workbuddy\skills\Stata-run\scripts\run_stata.py
echo.
echo 也可以设置环境变量 STATA_PATH 来指定路径。
echo.

pause
