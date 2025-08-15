"""
Constants and Configuration for Web Fetch Tool
"""

# HTTP Request Configuration - EXTREME LIMITS for technical documentation
REQUEST_TIMEOUT = 300  # seconds (5 minutes) - handle massive docs
MAX_CONTENT_SIZE = 500 * 1024 * 1024  # 500MB max content size - MASSIVE  
MAX_REDIRECTS = 20  # Maximum redirects to follow - very flexible

# User Agent for requests
USER_AGENT = "MCP-WebFetch/1.0 (Web Content Fetcher)"

# Content extraction settings - OPTIMIZED for AI context efficiency
MAX_EXTRACTED_TEXT_LENGTH = 2000000  # characters (2M) - MASSIVE for long technical docs
EXTRACT_IMAGES = False  # Keep FALSE - no binary data, text-only for AI efficiency
EXTRACT_LINKS = True   # Whether to extract links (lightweight metadata only)

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

# Request headers
DEFAULT_HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Error handling - Enhanced for reliability
MAX_RETRY_ATTEMPTS = 5  # More attempts for unreliable connections
RETRY_DELAY = 2  # seconds between retries - longer pause for stability
