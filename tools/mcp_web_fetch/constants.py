"""
Constants and Configuration for Web Fetch Tool
"""

# HTTP Request Configuration - EXTREME LIMITS for technical documentation
REQUEST_TIMEOUT = 300  # seconds (5 minutes) - handle massive docs
MAX_CONTENT_SIZE = 500 * 1024 * 1024  # 500MB max content size - MASSIVE  
MAX_REDIRECTS = 20  # Maximum redirects to follow - very flexible

# User Agent Configuration - Anti-Detection
USER_AGENT = "MCP-WebFetch/1.0 (Web Content Fetcher)"  # Fallback only

# Modern Browser User-Agent Pool (Based on current market share)
USER_AGENT_POOL = [
    # Chrome 131 - Windows (30% distribution)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    
    # Chrome 131 - macOS (20% distribution)  
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    
    # Chrome 131 - Linux (15% distribution)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    
    # Firefox 133 - Windows (10% distribution)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    
    # Firefox 133 - macOS (5% distribution)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    
    # Safari 18 - macOS (7% distribution)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    
    # Edge 131 - Windows (8% distribution)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    
    # Mobile - iOS Safari (3% distribution)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1",
    
    # Mobile - Android Chrome (2% distribution)
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
]

# Content extraction settings - OPTIMIZED for AI context efficiency
MAX_EXTRACTED_TEXT_LENGTH = 2000000  # characters (2M) - MASSIVE for long technical docs
EXTRACT_IMAGES = False  # Keep FALSE - no binary data, text-only for AI efficiency
EXTRACT_LINKS = True   # Whether to extract links (lightweight metadata only)
MAX_LINKS_EXTRACT = 300  # Maximum number of links to extract per page (increased for documentation sites)

# Supported content types - Expanded for maximum compatibility  
SUPPORTED_CONTENT_TYPES = [
    'text/html',
    'text/plain', 
    'application/json',
    'application/xml',
    'text/xml',
    'application/rss+xml',
    'application/atom+xml', 
    'text/css',
    'application/javascript',
    'text/javascript',
    'application/xhtml+xml',
    'text/csv',
    'application/x-www-form-urlencoded',
    # Accept most text-based content
    'text/',  # Matches any text/* content type
    'application/x-'  # Matches many application/x-* types
]

# Request headers - Enhanced for stealth (User-Agent set dynamically)
DEFAULT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0'
}

# COMPLETE BROWSER PROFILES - Enhanced Headers System
BROWSER_PROFILES = {
    "chrome_windows": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Cache-Control": "max-age=0"
        }
    },
    "chrome_macos": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none", 
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Cache-Control": "max-age=0"
        }
    },
    "firefox_windows": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    },
    "firefox_macos": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
    },
    "safari_macos": {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    },
    "edge_windows": {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Cache-Control": "max-age=0"
        }
    }
}

# Helper function for User-Agent rotation (Legacy compatibility)
def get_random_user_agent():
    """
    Get a random User-Agent from the pool for anti-detection
    
    Returns:
        str: Random User-Agent string from the pool
    """
    import random
    return random.choice(USER_AGENT_POOL)

# Enhanced helper functions for Complete Browser Profiles
def get_random_browser_profile():
    """
    Get a complete random browser profile with matching headers
    
    Returns:
        dict: Complete browser profile with user_agent, headers, and profile_name
    """
    import random
    profile_name = random.choice(list(BROWSER_PROFILES.keys()))
    profile = BROWSER_PROFILES[profile_name].copy()
    profile["profile_name"] = profile_name
    return profile

def get_browser_profile_by_name(profile_name):
    """
    Get specific browser profile by name
    
    Args:
        profile_name (str): Name of browser profile (e.g., 'chrome_windows')
    
    Returns:
        dict: Browser profile or default chrome_windows if not found
    """
    return BROWSER_PROFILES.get(profile_name, BROWSER_PROFILES["chrome_windows"])

# JavaScript Rendering Configuration
JS_RENDERING_ENABLED = True  # Enable JavaScript rendering capabilities
JS_RENDERING_TIMEOUT = 30  # seconds - timeout for JS rendering
JS_RENDERING_METHODS = [
    "requests_html",  # Lightweight - built-in PyJSSEnvironment  
    "selenium_undetected",  # Advanced - undetected-chromedriver
    "selenium_stealth",  # Popular - selenium-stealth
    # "playwright"  # Modern - future implementation
]
DEFAULT_JS_METHOD = "requests_html"  # Start with lightweight option

# JavaScript detection patterns - indicators that JS rendering might be needed
JS_DETECTION_PATTERNS = [
    # Common JS-rendered content indicators
    "This page requires JavaScript",
    "Please enable JavaScript", 
    "JavaScript is required",
    "Loading...",
    "Please wait...",
    # SPA frameworks
    "__NEXT_DATA__",  # Next.js
    "window.__NUXT__",  # Nuxt.js
    "ng-app",  # Angular
    "data-reactroot",  # React
    "v-app",  # Vue.js
    # Empty content indicators
    "<body></body>",
    "<div id=\"root\"></div>",
    "<div id=\"app\"></div>",
]

# Error handling - Enhanced for reliability
MAX_RETRY_ATTEMPTS = 5  # More attempts for unreliable connections
RETRY_DELAY = 2  # seconds between retries - longer pause for stability

# Smart Retry Strategies
RETRY_STRATEGIES = [
    "exponential_backoff",   # 2s, 4s, 8s, 16s, 32s
    "linear_progression",    # 2s, 4s, 6s, 8s, 10s
    "fibonacci_sequence",    # 2s, 3s, 5s, 8s, 13s
    "random_jitter",         # 2s±1s, 4s±2s, 6s±3s, 8s±4s, 10s±5s
]
DEFAULT_RETRY_STRATEGY = "exponential_backoff"

# Retry triggers and conditions
RETRIABLE_STATUS_CODES = [429, 500, 502, 503, 504, 520, 521, 522, 523, 524]
RETRIABLE_EXCEPTIONS = [
    "ConnectionError", "Timeout", "SSLError", "TooManyRedirects", 
    "ChunkedEncodingError", "ContentDecodingError", "HTTPError"
]
