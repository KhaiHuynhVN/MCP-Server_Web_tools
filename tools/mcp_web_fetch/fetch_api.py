"""
HTTP Client for Web Fetch Tool - Content fetching and extraction
"""

import httpx
import requests
import time
import random
from typing import Dict, Any, Optional, Union
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from .constants import (
    REQUEST_TIMEOUT, MAX_CONTENT_SIZE, MAX_REDIRECTS, DEFAULT_HEADERS,
    MAX_EXTRACTED_TEXT_LENGTH, EXTRACT_LINKS, SUPPORTED_CONTENT_TYPES,
    MAX_RETRY_ATTEMPTS, RETRY_DELAY, get_random_user_agent, 
    get_random_browser_profile, BROWSER_PROFILES, JS_RENDERING_ENABLED,
    JS_RENDERING_TIMEOUT, DEFAULT_JS_METHOD, JS_DETECTION_PATTERNS,
    DEFAULT_RETRY_STRATEGY, RETRIABLE_STATUS_CODES, RETRIABLE_EXCEPTIONS
)


class WebContentFetcher:
    """HTTP client for fetching and extracting web content"""
    
    def __init__(self, retry_strategy: str = DEFAULT_RETRY_STRATEGY):
        # Setup HTTP/2 capable client (2025 Standard)
        # Use complete browser profile for enhanced stealth (2025 Best Practice)
        self.browser_profile = get_random_browser_profile()
        
        # Session management (2025 Enhancement) - intelligent session pools
        self.session_pool = {}  # Domain-specific sessions for better cookie management
        self.current_session_domain = None
        
        # Smart retry configuration (2025 Enhancement)
        self.retry_strategy = retry_strategy
        self.retry_attempt_history = []  # Track retry patterns for learning
        
        # Requests session (fallback) with persistent cookie jar
        self.session = requests.Session()
        self.session.headers.update(self.browser_profile["headers"])
        self.session.headers['User-Agent'] = self.browser_profile["user_agent"]
        self.session.max_redirects = MAX_REDIRECTS
        # Enable persistent cookies for anti-detection
        self.session.cookies = requests.cookies.RequestsCookieJar()
        
        # HTTPX client with HTTP/2 support (Primary 2025) + Persistent cookies
        try:
            self.httpx_client = httpx.Client(
                http2=True,  # Critical for modern sites
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                follow_redirects=True,
                headers=self.browser_profile["headers"],
                cookies=httpx.Cookies()  # Persistent cookie jar for session management
            )
            self.http2_available = True
        except Exception as e:
            print(f"WARNING: HTTP/2 not available: {str(e)}")
            print("📦 Install missing dependency: pip install httpx[http2] h2")
            print("INFO: Falling back to HTTP/1.1...")
            self.httpx_client = httpx.Client(
                http2=False,  # Fallback to HTTP/1.1
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                follow_redirects=True,
                headers=self.browser_profile["headers"],
                cookies=httpx.Cookies()
            )
            self.http2_available = False
        
        # JavaScript rendering setup
        self.js_rendering_enabled = JS_RENDERING_ENABLED
        self.js_session = None  # Will be initialized if needed
        
        print(f"INFO: WebContentFetcher initialized with Profile: {self.browser_profile['profile_name']}")
        print(f"INFO: User-Agent: {self.browser_profile['user_agent'][:50]}...")
        print(f"INFO: HTTP/2: {'ENABLED' if self.http2_available else 'DISABLED (fallback to HTTP/1.1)'}")
        print(f"INFO: Persistent cookies: ENABLED")
        print(f"INFO: Retry strategy: {retry_strategy}")
        if self.js_rendering_enabled:
            print("INFO: JavaScript rendering: ENABLED")

    def _get_domain_session(self, url: str) -> requests.Session:
        """
        Get domain-specific session for intelligent cookie management (2025 Enhancement)
        
        Args:
            url: Target URL to extract domain from
            
        Returns:
            requests.Session: Domain-specific session with persistent cookies
        """
        domain = urlparse(url).netloc
        
        # Create new session for this domain if doesn't exist
        if domain not in self.session_pool:
            new_session = requests.Session()
            new_session.headers.update(self.browser_profile["headers"])
            new_session.headers['User-Agent'] = self.browser_profile["user_agent"]
            new_session.max_redirects = MAX_REDIRECTS
            new_session.cookies = requests.cookies.RequestsCookieJar()
            self.session_pool[domain] = new_session
            print(f"🆕 Created new session for domain: {domain}")
        
        self.current_session_domain = domain
        return self.session_pool[domain]

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate smart retry delay based on strategy (2025 Enhancement)
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            float: Delay in seconds
        """
        base_delay = RETRY_DELAY
        
        if self.retry_strategy == "exponential_backoff":
            # 2s, 4s, 8s, 16s, 32s
            delay = base_delay * (2 ** attempt)
        elif self.retry_strategy == "linear_progression":
            # 2s, 4s, 6s, 8s, 10s
            delay = base_delay * (attempt + 1)
        elif self.retry_strategy == "fibonacci_sequence":
            # 2s, 3s, 5s, 8s, 13s
            fib_sequence = [1, 1, 2, 3, 5, 8, 13, 21, 34]
            multiplier = fib_sequence[min(attempt, len(fib_sequence) - 1)]
            delay = base_delay * multiplier
        elif self.retry_strategy == "random_jitter":
            # Add randomness to prevent thundering herd
            base = base_delay * (attempt + 1)
            jitter = random.uniform(-base * 0.3, base * 0.3)
            delay = max(1, base + jitter)  # Minimum 1 second
        else:
            # Default to exponential backoff
            delay = base_delay * (2 ** attempt)
        
        # Cap maximum delay at 60 seconds
        return min(delay, 60)

    def _is_retriable_error(self, exception: Exception, response: Optional[Union[requests.Response, httpx.Response]] = None) -> bool:
        """
        Determine if error/response is worth retrying (2025 Smart Logic)
        
        Args:
            exception: Exception that occurred
            response: Response object if available
            
        Returns:
            bool: True if should retry
        """
        # Check response status codes
        if response and hasattr(response, 'status_code'):
            if response.status_code in RETRIABLE_STATUS_CODES:
                return True
        
        # Check exception types
        exception_name = type(exception).__name__
        if exception_name in RETRIABLE_EXCEPTIONS:
            return True
            
        # Check exception message for specific patterns
        error_msg = str(exception).lower()
        retriable_patterns = [
            "connection", "timeout", "ssl", "certificate", "network",
            "temporary", "unavailable", "overloaded", "retry"
        ]
        
        for pattern in retriable_patterns:
            if pattern in error_msg:
                return True
        
        return False

    def _needs_javascript_rendering(self, content: str) -> bool:
        """
        Enhanced JavaScript detection with reduced false positives (2025 Algorithm)
        
        Args:
            content: HTML content to analyze
            
        Returns:
            bool: True if JS rendering is likely needed
        """
        if not content or len(content.strip()) < 300:  # More conservative threshold
            return True  # Very short content might be JS-rendered
            
        content_lower = content.lower()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Enhanced pattern detection with weighting
        js_indicators = 0
        
        # Strong indicators (weight: 2)
        strong_patterns = [
            "__next_data__", "window.__nuxt__", "data-reactroot", 
            "ng-app", "v-app", "<div id=\"root\"></div>", "<div id=\"app\"></div>"
        ]
        for pattern in strong_patterns:
            if pattern in content_lower:
                js_indicators += 2
                
        # Medium indicators (weight: 1)
        medium_patterns = [
            "this page requires javascript", "please enable javascript",
            "javascript is required", "loading...", "please wait..."
        ]
        for pattern in medium_patterns:
            if pattern in content_lower:
                js_indicators += 1
        
        # Content analysis - more sophisticated check
        text_content = soup.get_text().strip()
        visible_text_length = len(text_content)
        html_length = len(content)
        
        # Calculate text-to-HTML ratio (healthy content has good ratio)
        if html_length > 0:
            text_ratio = visible_text_length / html_length
            if text_ratio < 0.05:  # Less than 5% actual text
                js_indicators += 2
            elif text_ratio < 0.1:  # Less than 10% actual text
                js_indicators += 1
        
        # Check for empty body or minimal content structures
        body = soup.find('body')
        if body:
            body_children = body.find_all(recursive=False)
            if len(body_children) <= 3 and visible_text_length < 500:
                js_indicators += 1
        
        # Decision threshold (require at least 2 indicators to trigger JS rendering)
        return js_indicators >= 2

    def _render_with_javascript(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Enhanced JavaScript rendering with Playwright + requests-html fallback (2025 Algorithm)
        
        Args:
            url: URL to render
            retry_count: Internal retry counter
            
        Returns:
            str: Rendered HTML content or None if failed
        """
        # Try Playwright first (2025 recommended)
        playwright_result = self._render_with_playwright(url, retry_count)
        if playwright_result:
            return playwright_result
            
        # Fallback to requests-html
        return self._render_with_requests_html(url, retry_count)
    
    def _render_with_playwright(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Render with Playwright (2025 Modern Solution)
        """
        try:
            from playwright.sync_api import sync_playwright
            from playwright_stealth import stealth
            
            print(f"INFO: Playwright rendering: {url} (attempt {retry_count + 1})")
            
            with sync_playwright() as p:
                # Launch browser with stealth mode
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                
                # Create context with real browser fingerprint
                context = browser.new_context(
                    user_agent=self.browser_profile["user_agent"],
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US'
                )
                
                page = context.new_page()
                
                # Apply stealth patches
                stealth(page)
                
                # Set additional headers
                page.set_extra_http_headers(self.browser_profile["headers"])
                
                # Navigate and wait for load
                timeout = (JS_RENDERING_TIMEOUT + retry_count * 5) * 1000  # Convert to ms
                page.goto(url, timeout=timeout, wait_until='networkidle')
                
                # Wait for dynamic content
                page.wait_for_timeout(2000 + retry_count * 1000)
                
                # Scroll to trigger lazy loading
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(1000)
                
                # Get rendered content
                content = page.content()
                browser.close()
                
                print(f"SUCCESS: Playwright rendering successful: {len(content)} chars")
                return content
                
        except ImportError:
            print("WARNING: Playwright not available, trying fallback...")
            return None
        except Exception as e:
            print(f"ERROR: Playwright ERROR: {type(e).__name__}: {str(e)}")
            if retry_count < 1:
                print(f"WARNING: Playwright failed: {str(e)}, retrying...")
                time.sleep(2)
                return self._render_with_playwright(url, retry_count + 1)
            else:
                print(f"ERROR: Playwright failed after retries: {str(e)}")
                return None
    
    def _render_with_requests_html(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fallback render with requests-html (Legacy Support)
        """
        try:
            from requests_html import HTMLSession
            
            if self.js_session is None:
                self.js_session = HTMLSession()
                self.js_session.headers.update(self.browser_profile["headers"])
                self.js_session.headers['User-Agent'] = self.browser_profile["user_agent"]
                print("INFO: Fallback: requests-html session initialized")
            
            print(f"INFO: Fallback rendering: {url} (attempt {retry_count + 1})")
            
            timeout = JS_RENDERING_TIMEOUT + (retry_count * 5)
            response = self.js_session.get(url, timeout=timeout)
            response.raise_for_status()
            
            original_length = len(response.text)
            
            render_options = {
                'timeout': timeout,
                'wait': 2 + retry_count,
                'scrolldown': min(3 + retry_count, 10),
                'sleep': 1
            }
            
            response.html.render(**render_options)
            rendered_content = response.html.html
            
            if len(rendered_content) > original_length * 1.1:
                print(f"SUCCESS: Fallback rendering successful: {len(rendered_content)} chars")
                return rendered_content
            else:
                print(f"WARNING: Fallback rendering minimal improvement: {len(rendered_content)} chars")
                return rendered_content
            
        except ImportError:
            print("ERROR: requests-html not available, skipping JavaScript rendering")
            return None
        except Exception as e:
            if retry_count < 1:
                print(f"WARNING: Fallback failed: {str(e)}, retrying...")
                time.sleep(2)
                return self._render_with_requests_html(url, retry_count + 1)
            else:
                print(f"ERROR: Fallback failed after retries: {str(e)}")
                return None

    def _fetch_with_httpx(self, url: str) -> httpx.Response:
        """
        Fetch URL using HTTPX client with HTTP/2 support (2025 Standard)
        
        Args:
            url: Target URL to fetch
            
        Returns:
            httpx.Response: Response object
        """
        try:
            print(f"INFO: Fetching with HTTP/2: {url}")
            response = self.httpx_client.get(url)
            response.raise_for_status()
            print(f"SUCCESS: HTTP/2 fetch successful: {response.status_code}")
            return response
        except Exception as e:
            print(f"ERROR: HTTP/2 fetch failed: {str(e)}")
            # Fall back to requests session
            print("INFO: Falling back to requests session...")
            raise

    def _fetch_with_requests(self, url: str) -> requests.Response:
        """
        Fallback fetch using domain-specific requests session (2025 Enhancement)
        
        Args:
            url: Target URL to fetch
            
        Returns:
            requests.Response: Response object
        """
        print(f"INFO: Fetching with requests (fallback): {url}")
        # Use domain-specific session for better cookie management
        domain_session = self._get_domain_session(url)
        response = domain_session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        print(f"INFO: Used session for domain: {self.current_session_domain}")
        return response

    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from URL
        
        Args:
            url: Target URL to fetch content from
            
        Returns:
            Dict containing extracted content and metadata
        """
        
        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")
        
        # Attempt fetch with retries using HTTP/2 first (2025 Anti-Detection)
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                # Try HTTP/2 first, then fallback to requests
                try:
                    response = self._fetch_with_httpx(url)
                    print("SUCCESS: Using HTTP/2 response for processing")
                except Exception:
                    response = self._fetch_with_requests(url)
                    print("SUCCESS: Using requests response for processing")
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not self._is_supported_content_type(content_type):
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                # Check content size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_CONTENT_SIZE:
                    raise ValueError(f"Content too large: {content_length} bytes")
                
                # Extract content based on type
                if 'text/html' in content_type:
                    return self._extract_html_content(response, url)
                elif 'application/json' in content_type:
                    return self._extract_json_content(response, url)
                else:
                    return self._extract_plain_content(response, url)
                    
            except (requests.exceptions.RequestException, httpx.RequestError) as e:
                # Smart retry logic (2025 Enhancement)
                if attempt < MAX_RETRY_ATTEMPTS - 1 and self._is_retriable_error(e):
                    # Calculate smart delay based on strategy
                    delay = self._calculate_retry_delay(attempt)
                    
                    # Track retry attempt for learning
                    retry_info = {
                        "attempt": attempt + 1,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "delay": delay,
                        "strategy": self.retry_strategy
                    }
                    self.retry_attempt_history.append(retry_info)
                    
                    # Switch to new complete browser profile for retry (enhanced anti-detection)
                    new_profile = get_random_browser_profile()
                    
                    # Clear all existing sessions to prevent cookie conflicts (2025 Enhancement)
                    self.session_pool.clear()
                    print("🧹 Cleared all domain sessions (cookie reset)")
                    
                    # Update fallback requests session
                    self.session.headers.clear()
                    self.session.headers.update(new_profile["headers"])
                    self.session.headers['User-Agent'] = new_profile["user_agent"]
                    self.session.cookies.clear()  # Clear cookies
                    
                    # Update httpx client with new profile (2025 Enhancement)
                    new_headers = new_profile["headers"].copy()
                    new_headers['User-Agent'] = new_profile["user_agent"]
                    self.httpx_client.headers.clear()
                    self.httpx_client.headers.update(new_headers)
                    self.httpx_client.cookies.clear()  # Clear httpx cookies
                    
                    self.browser_profile = new_profile
                    print(f"INFO: Attempt {attempt + 1} failed: {type(e).__name__}")
                    print(f"🆔 Switching to Profile: {new_profile['profile_name']}")
                    print(f"INFO: Smart delay ({self.retry_strategy}): {delay:.1f}s")
                    time.sleep(delay)
                    continue
                elif not self._is_retriable_error(e):
                    print(f"ERROR: Non-retriable error: {type(e).__name__} - {str(e)}")
                    break
                raise Exception(f"Failed to fetch URL after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}")
        
        raise Exception("Unexpected error in fetch_content")



    def _extract_html_content(self, response: Union[requests.Response, httpx.Response], url: str) -> Dict[str, Any]:
        """Extract content from HTML response with JavaScript rendering support"""
        # Use response.text for automatic charset detection and decompression
        try:
            original_content = response.text
            print(f"INFO: Original content length: {len(original_content)} chars")
        except (UnicodeDecodeError, LookupError):
            # Fallback to UTF-8 with error handling if auto-detection fails
            original_content = response.content.decode('utf-8', errors='ignore')
            print(f"INFO: Fallback content length: {len(original_content)} chars")
        
        rendered_with_js = False
        
        # Check if JavaScript rendering might be needed
        needs_js = self._needs_javascript_rendering(original_content)
        
        # Debug: Check patterns in current content
        from .constants import JS_DETECTION_PATTERNS
        patterns_found = [p for p in JS_DETECTION_PATTERNS if p.lower() in original_content.lower()]
        print(f"INFO: JS Rendering Check: enabled={self.js_rendering_enabled}, needs_js={needs_js}")
        print(f"INFO: JS patterns found in {len(original_content)} chars: {patterns_found}")
        if self.js_rendering_enabled and needs_js:
            print("INFO: Detected potential JavaScript-rendered content")
            
            # Try JavaScript rendering
            js_rendered_content = self._render_with_javascript(url)
            if js_rendered_content:
                original_content = js_rendered_content
                rendered_with_js = True
                print("SUCCESS: Using JavaScript-rendered content")
            else:
                print("WARNING: JavaScript rendering failed, using original content")
        
        soup = BeautifulSoup(original_content, 'html.parser')
        
        # Remove ALL non-content elements for maximum context efficiency
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'iframe', 'video', 'audio', 'canvas',
                           'svg', 'form', 'button', 'input', 'select']):
            element.decompose()
        
        # Remove ads and tracking elements
        for ad_element in soup.find_all(attrs={'class': lambda x: x and any(
            keyword in str(x).lower() for keyword in ['ad', 'advertisement', 'sponsor', 'banner', 'popup', 'cookie', 'gdpr']
        )}):
            ad_element.decompose()
        
        # Extract basic metadata
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        
        # Extract main content
        main_content = self._extract_main_text(soup)
        
        # Extract links if enabled
        links = []
        if EXTRACT_LINKS:
            links = self._extract_links(soup, url)
        
        # Determine final status
        status = 'success'
        if rendered_with_js:
            status = 'success_js_rendered'
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': main_content,
            'content_type': 'text/html',
            'links': links,
            'word_count': len(main_content.split()) if main_content else 0,
            'status': status,
            'javascript_rendered': rendered_with_js
        }

    def _extract_json_content(self, response: Union[requests.Response, httpx.Response], url: str) -> Dict[str, Any]:
        """Extract content from JSON response"""
        try:
            json_data = response.json()
            
            # Convert JSON to readable text
            import json
            content = json.dumps(json_data, indent=2, ensure_ascii=False)
            
            return {
                'url': url,
                'title': f"JSON Content from {urlparse(url).netloc}",
                'description': 'JSON data content',
                'content': content[:MAX_EXTRACTED_TEXT_LENGTH],
                'content_type': 'application/json',
                'links': [],
                'word_count': len(content.split()),
                'status': 'success'
            }
        except Exception as e:
            raise ValueError(f"Invalid JSON content: {str(e)}")

    def _extract_plain_content(self, response: Union[requests.Response, httpx.Response], url: str) -> Dict[str, Any]:
        """Extract content from plain text response"""
        try:
            content = response.text[:MAX_EXTRACTED_TEXT_LENGTH]
        except (UnicodeDecodeError, LookupError):
            # Fallback if auto-detection fails
            content = response.content.decode('utf-8', errors='ignore')[:MAX_EXTRACTED_TEXT_LENGTH]
        
        return {
            'url': url,
            'title': f"Text Content from {urlparse(url).netloc}",
            'description': 'Plain text content',
            'content': content,
            'content_type': response.headers.get('content-type', 'text/plain'),
            'links': [],
            'word_count': len(content.split()),
            'status': 'success'
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "No title found"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ""

    def _extract_main_text(self, soup: BeautifulSoup) -> str:
        """Extract main readable text content"""
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '[role="main"]', '.content', '.post-content',
            '.entry-content', '.article-content', '#content', '.main-content'
        ]
        
        main_element = None
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                break
        
        # Fallback to body if no main content found
        if not main_element:
            main_element = soup.find('body') or soup
        
        # Extract PURE TEXT with optimal formatting for AI processing
        text_content = main_element.get_text(separator=' ', strip=True)
        
        # Clean up excessive whitespace for context efficiency
        import re
        text_content = re.sub(r'\s+', ' ', text_content)  # Multiple spaces → single space
        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)  # Multiple newlines → double newline
        
        # Limit text length
        if len(text_content) > MAX_EXTRACTED_TEXT_LENGTH:
            text_content = text_content[:MAX_EXTRACTED_TEXT_LENGTH] + "... [content truncated]"
        
        return text_content

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list:
        """Extract links from the page"""
        links = []
        
        for link in soup.find_all('a', href=True)[:100]:  # Extract ALL links for complete documentation mapping
            href = link['href']
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            if text and absolute_url.startswith(('http://', 'https://')):
                links.append({
                    'url': absolute_url,
                    'text': text[:200]  # Longer link text for better context
                })
        
        return links

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

    def _is_supported_content_type(self, content_type: str) -> bool:
        """Check if content type is supported - flexible matching"""
        # Support most text-based content types
        return any(supported in content_type for supported in SUPPORTED_CONTENT_TYPES) or \
               content_type.startswith('text/') or \
               'json' in content_type or \
               'xml' in content_type


# Main function for external use
def fetch_web_content(url: str) -> Dict[str, Any]:
    """
    Main function to fetch web content from URL
    
    Args:
        url: Target URL to fetch content from
        
    Returns:
        Dict with extracted content and metadata
    """
    try:
        fetcher = WebContentFetcher()
        return fetcher.fetch_content(url)
    except ValueError as e:
        # Client errors (invalid URL, unsupported content, etc.)
        raise e
    except Exception as e:
        # Server/network errors
        raise Exception(f"Failed to fetch content: {str(e)}")


# Test function
if __name__ == "__main__":
    # Test URL fetch
    try:
        result = fetch_web_content("https://httpbin.org/html")
        print(f"Title: {result['title']}")
        print(f"Content length: {len(result['content'])}")
        print(f"Word count: {result['word_count']}")
    except Exception as e:
        print(f"Test error: {e}")
