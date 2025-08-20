# 📦 INSTALLATION GUIDE - Web MCP 2025 Dependencies

## 🚀 Quick Installation

### Required Dependencies for Full 2025 Features:

```bash
# Core dependencies
pip install mcp requests beautifulsoup4 lxml

# HTTP/2 Support (Recommended)
pip install httpx[http2] h2

# JavaScript Rendering (Recommended) 
pip install requests-html lxml-html-clean

# OR install all at once:
pip install mcp requests httpx[http2] h2 requests-html lxml-html-clean beautifulsoup4 lxml
```

## 🔧 Alternative Installation

### Using pip install from project directory:

```bash
cd Web_mcp
pip install -e .
```

## ⚠️ Troubleshooting

### 1. HTTP/2 Not Available Error:
```
ERROR: Using http2=True, but the 'h2' package is not installed
```
**Solution:**
```bash
pip install httpx[http2] h2
```

### 2. JavaScript Rendering Error:
```
ERROR: requests-html not installed
```
**Solution:**
```bash
pip install requests-html
```

### 3. lxml.html.clean Error:
```
ERROR: lxml.html.clean module is now a separate project lxml_html_clean
```
**Solution:**
```bash
pip install lxml-html-clean
```

### 4. Browser Dependencies (for requests-html):
```
ERROR: Chromium browser not found
```
**Solution:**
```bash
# Install Chromium for JavaScript rendering
pyppeteer-install
```

## 🎯 Minimal Installation (Basic Features Only):

If you want basic functionality without HTTP/2 and JS rendering:

```bash
pip install mcp requests beautifulsoup4 lxml
```

**Note:** Tool will automatically fallback to HTTP/1.1 và skip JS rendering.

## 📋 Dependency Details:

| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| `mcp` | Latest | MCP protocol | ✅ Yes |
| `requests` | Latest | HTTP client fallback | ✅ Yes |
| `httpx[http2]` | Latest | HTTP/2 client | ⚡ Recommended |
| `h2` | Latest | HTTP/2 protocol | ⚡ Recommended |
| `requests-html` | Latest | JS rendering | 🎭 Optional |
| `lxml-html-clean` | Latest | Fix lxml compatibility | 🎭 Optional |
| `beautifulsoup4` | Latest | HTML parsing | ✅ Yes |
| `lxml` | Latest | Fast XML parser | ✅ Yes |

## 🚀 Verification:

After installation, test với:

```bash
cd Web_mcp
python test_quick_web_fetch.py
```

Expected output với full dependencies:
```
🚀 HTTP/2: ENABLED
🌐 JavaScript rendering: ENABLED
📊 RESULTS: 4-5/5 tests passed
```

Expected output với minimal dependencies:
```
🚀 HTTP/2: DISABLED (fallback to HTTP/1.1)  
🌐 JavaScript rendering: DISABLED
📊 RESULTS: 2-3/5 tests passed
```

## 💡 Pro Tips:

1. **Virtual Environment Recommended:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Check Installation:**
   ```python
   import httpx, requests, bs4
   print("✅ Basic dependencies OK")
   
   try:
       import h2
       print("✅ HTTP/2 support OK")
   except ImportError:
       print("❌ HTTP/2 not available")
   
   try:
       import requests_html
       print("✅ JS rendering OK")
   except ImportError:
       print("❌ JS rendering not available")
   ```

## 🆘 Support:

If you encounter issues:

1. Check Python version: `python --version` (requires 3.13+)
2. Update pip: `pip install --upgrade pip`
3. Clear cache: `pip cache purge`
4. Reinstall: `pip uninstall <package> && pip install <package>`
