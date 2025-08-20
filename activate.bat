@echo off
echo 🔧 Activating Web_MCP environment...

if not exist "venv\" (
    echo ❌ Virtual environment not found!
    echo 📦 Run setup_environment.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate

echo ✅ Environment activated!
echo.
echo 🧪 Available commands:
echo   python test_quick_web_fetch.py          - Quick test (5 tests)
echo   python test_comprehensive_web_fetch.py  - Full test (20+ tests)
echo   python debug_requests_html.py           - Debug JS rendering
echo.
echo 🚀 Web_MCP ready to use!
