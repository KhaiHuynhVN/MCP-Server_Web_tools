@echo off
echo 🚀 Setting up Web_MCP isolated environment...
echo.

echo 📦 Creating virtual environment (like node_modules)...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)

echo 🔧 Activating virtual environment...
call venv\Scripts\activate

echo 📥 Installing dependencies (like npm install)...
pip install --upgrade pip
pip install -e .

echo 🌐 Installing browser binaries...
playwright install chromium

echo.
echo ✅ Setup complete! To use the environment:
echo.
echo   📂 Navigate to Web_mcp folder
echo   ⚡ Run: venv\Scripts\activate
echo   🧪 Test: python test_quick_web_fetch.py
echo.
echo 🎉 Web_MCP ready with isolated dependencies!
pause
