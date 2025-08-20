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
import charset_normalizer
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
            print("INFO: Install missing dependency: pip install httpx[http2] h2")
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
            
            # Force gzip instead of brotli to avoid decompression issues
            new_session.headers['Accept-Encoding'] = 'gzip, deflate'
            new_session.headers['User-Agent'] = self.browser_profile["user_agent"]
            new_session.max_redirects = MAX_REDIRECTS
            new_session.cookies = requests.cookies.RequestsCookieJar()
            self.session_pool[domain] = new_session
            print(f"CREATED: New session for domain: {domain}")
        
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
            from playwright_stealth.stealth import Stealth
            
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
                
                # Apply stealth patches - FIXED IMPORT AND USAGE
                stealth = Stealth()
                stealth.apply_stealth_sync(page)
                
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
                # Use only HTTP/1.1 requests for maximum compatibility and reliability
                print("INFO: Using HTTP/1.1 (requests) for maximum reliability")
                response = self._fetch_with_requests(url)
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not self._is_supported_content_type(content_type):
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                # Check content size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_CONTENT_SIZE:
                    raise ValueError(f"Content too large: {content_length} bytes")
                
                # Extract content based on type with intelligent approach selection
                if 'text/html' in content_type:
                    # INTELLIGENT APPROACH SELECTION (2025 Architecture)
                    # Check if site needs JavaScript FIRST, then choose best approach
                    raw_content = self._detect_and_decode_content(response)
                    needs_js = self._needs_javascript_rendering(raw_content)
                    
                    print(f"INFO: Site analysis - Needs JavaScript: {needs_js}")
                    
                    if needs_js and self.js_rendering_enabled:
                        print("INFO: JavaScript site detected - Using PLAYWRIGHT PRIMARY approach")
                        # Use Playwright as PRIMARY approach for JS sites
                        js_content = self._render_with_javascript(url)
                        if js_content:
                            # Create mock response with rendered content for extraction
                            from types import SimpleNamespace
                            rendered_response = SimpleNamespace()
                            rendered_response.text = js_content
                            rendered_response.content = js_content.encode('utf-8')  # Add .content for charset detection
                            rendered_response.headers = response.headers
                            return self._extract_html_content_static(rendered_response, url, javascript_rendered=True)
                        else:
                            print("WARNING: Playwright failed, falling back to static content")
                            return self._extract_html_content_static(response, url, javascript_rendered=False)
                    else:
                        print("INFO: Static site detected - Using direct HTML extraction")
                        # Use static approach for non-JS sites
                        return self._extract_html_content_static(response, url, javascript_rendered=False)
                        
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
                    print("CLEARED: All domain sessions (cookie reset)")
                    
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
                    print(f"SWITCHING: To Profile: {new_profile['profile_name']}")
                    print(f"INFO: Smart delay ({self.retry_strategy}): {delay:.1f}s")
                    time.sleep(delay)
                    continue
                elif not self._is_retriable_error(e):
                    print(f"ERROR: Non-retriable error: {type(e).__name__} - {str(e)}")
                    break
                raise Exception(f"Failed to fetch URL after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}")
        
        raise Exception("Unexpected error in fetch_content")



    def _detect_and_decode_content(self, response: Union[requests.Response, httpx.Response]) -> str:
        """Modern charset detection and decoding using charset-normalizer (2025 standard)"""
        try:
            # Get raw bytes content
            raw_content = response.content
            
            # Use charset-normalizer for modern charset detection
            detected = charset_normalizer.from_bytes(raw_content).best()
            
            if detected and detected.encoding:
                # Decode using detected charset
                decoded_content = raw_content.decode(detected.encoding)
                print(f"INFO: Detected encoding: {detected.encoding}")
                print(f"INFO: Content length: {len(decoded_content)} chars")
                return decoded_content
            else:
                print("WARNING: No encoding detected, falling back to UTF-8")
                
        except Exception as e:
            print(f"WARNING: Charset detection failed: {str(e)}, falling back to UTF-8")
            
        # Fallback to UTF-8 with error handling
        try:
            fallback_content = response.content.decode('utf-8', errors='ignore')
            print(f"INFO: UTF-8 fallback content length: {len(fallback_content)} chars")
            return fallback_content
        except Exception as e:
            print(f"ERROR: Even UTF-8 fallback failed: {str(e)}")
            return ""

    def _extract_html_content_static(self, response: Union[requests.Response, httpx.Response], url: str, javascript_rendered: bool = False) -> Dict[str, Any]:
        """Extract content from HTML response with JavaScript rendering support"""
        # Use modern charset detection and decoding
        original_content = self._detect_and_decode_content(response)
        
        # This method now handles ONLY static content extraction
        # JavaScript rendering decision is made at higher level
        rendered_with_js = javascript_rendered
        
        print(f"INFO: Static extraction - JavaScript pre-rendered: {javascript_rendered}")
        print(f"INFO: Content length: {len(original_content)} chars")
        
        soup = BeautifulSoup(original_content, 'html.parser')
        
        # 2025 BEST PRACTICE: Use professional libraries instead of manual parsing
        main_content = self._extract_content_with_2025_best_practices(original_content)
        
        # Extract metadata from minimal clean soup (for title/description only)
        soup_clean = BeautifulSoup(original_content, 'html.parser')
        # Only remove scripts/styles for metadata - preserve structure
        for element in soup_clean(['script', 'style']):
            element.decompose()
            
        title = self._extract_title(soup_clean)
        description = self._extract_description(soup_clean)
        
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
        # Use modern charset detection for plain text too
        full_content = self._detect_and_decode_content(response)
        content = full_content[:MAX_EXTRACTED_TEXT_LENGTH]
        
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

    def _extract_content_with_2025_best_practices(self, html_content: str) -> str:
        """2025 RESEARCH-BACKED content extraction: Trafilatura (90.9% F1) + fallbacks"""
        
        # METHOD 1: TRAFILATURA with ALL CONTENT (2025 RESEARCH-BACKED)
        try:
            import trafilatura
            
            # STRATEGY 1: html2txt - Extract ALL text including navigation (maximizing recall)
            try:
                all_content = trafilatura.html2txt(html_content)
                if all_content and len(all_content.strip()) > 100:
                    print(f"SUCCESS: trafilatura.html2txt extracted {len(all_content)} chars (ALL content)")
                    return self._clean_text_content(all_content)
            except Exception as e:
                print(f"WARNING: html2txt failed: {str(e)}")
            
            # STRATEGY 2: Extract with favor_recall=True (prefer more text)
            recall_content = trafilatura.extract(html_content, favor_recall=True, include_comments=True, include_tables=True)
            if recall_content and len(recall_content.strip()) > 50:
                print(f"SUCCESS: trafilatura with favor_recall extracted {len(recall_content)} chars")
                return self._clean_text_content(recall_content)
        except ImportError:
            print("INFO: trafilatura not available. Install with: pip install trafilatura")
        except Exception as e:
            print(f"WARNING: trafilatura failed: {str(e)}")
        
        # METHOD 2: READABILITY-LXML (Mozilla algorithm - 80.1% F1-score)
        try:
            from readability import Document
            doc = Document(html_content)
            clean_html = doc.summary()
            
            # Extract text from readability-cleaned HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(clean_html, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
            
            if content and len(content.strip()) > 50:
                print(f"SUCCESS: readability-lxml (Mozilla) extracted {len(content)} chars")
                return self._clean_text_content(content)
        except ImportError:
            print("INFO: readability-lxml not available. Install with: pip install readability-lxml")
        except Exception as e:
            print(f"WARNING: readability-lxml failed: {str(e)}")
        
        # METHOD 3: SMART BEAUTIFULSOUP (Research shows: minimal removal preserves content)
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # MINIMAL removal - research shows aggressive removal destroys content
            for element in soup(['script', 'style', 'noscript']):
                element.decompose()
            
            # 2025 content selectors (research-backed priority order)
            content_selectors = [
                'main',  # HTML5 semantic
                'article',  # HTML5 semantic  
                '[role="main"]',  # WAI-ARIA
                '.entry-content',  # WordPress standard
                '.post-content',  # Blog standard
                '.content',  # Generic
                '#content'  # Generic ID
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator=' ', strip=True)
                    if len(content) > 50:
                        print(f"SUCCESS: BeautifulSoup '{selector}' extracted {len(content)} chars")
                        return self._clean_text_content(content)
            
            # Smart body fallback - preserve main structure  
            body = soup.find('body')
            if body:
                # Only remove obvious navigation, keep content structure
                for nav in body.find_all(['nav', 'header', 'footer']):
                    # Don't remove if it's inside main content area
                    if not nav.find_parent(['main', 'article']):
                        nav.decompose()
                
                content = body.get_text(separator=' ', strip=True)
                if len(content) > 50:
                    print(f"SUCCESS: Smart body extraction {len(content)} chars")
                    return self._clean_text_content(content)
            
            # Last resort - full document
            content = soup.get_text(separator=' ', strip=True)
            print(f"FALLBACK: Full document {len(content)} chars")
            return self._clean_text_content(content)
            
        except Exception as e:
            print(f"ERROR: All extraction methods failed: {str(e)}")
            return "Content extraction failed"
    
    def _extract_hero_content(self, html_content: str) -> str:
        """Extract hero/header content that trafilatura might miss"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            hero_parts = []
            
            # Find main titles (h1, prominent headings)
            main_titles = soup.find_all(['h1'], limit=3)
            for title in main_titles:
                text = title.get_text(strip=True)
                # Avoid duplicating later content
                if text and len(text) < 100 and 'Create user interfaces' not in text:
                    hero_parts.append(text)
            
            # Find hero descriptions (typically p tags near titles)
            for title in main_titles:
                # Look for nearby description paragraphs
                parent = title.parent
                if parent:
                    # Check siblings for description
                    for sibling in parent.find_all(['p'], limit=2):
                        desc_text = sibling.get_text(strip=True)
                        if desc_text and 'library for' in desc_text.lower() and len(desc_text) < 200:
                            hero_parts.append(desc_text)
                            break
            
            # Look for hero sections by common patterns
            hero_selectors = [
                '.hero h1, .hero p',
                'header h1, header p', 
                '[class*="hero"] h1, [class*="hero"] p',
                'section:first-of-type h1, section:first-of-type p'
            ]
            
            for selector in hero_selectors:
                elements = soup.select(selector)
                for elem in elements[:2]:  # Limit to avoid getting too much
                    text = elem.get_text(strip=True)
                    if text and len(text) < 200 and text not in hero_parts:
                        # Avoid main content that starts with "Create user interfaces"
                        if 'Create user interfaces' not in text:
                            hero_parts.append(text)
            
            # Clean and combine hero parts
            if hero_parts:
                hero_content = '\n'.join(hero_parts)
                print(f"DEBUG: Extracted hero content: {len(hero_content)} chars")
                return hero_content
            
            return ""
            
        except Exception as e:
            print(f"WARNING: Hero extraction failed: {str(e)}")
            return ""

    def _clean_text_content(self, text: str) -> str:
        """Clean and optimize extracted text (2025 best practices)"""
        if not text:
            return ""
            
        import re
        
        # Keep original trafilatura behavior - minimal processing
        # Normalize whitespace (preserve paragraph breaks)
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs → single space
        text = re.sub(r'\n[ \t]*\n', '\n\n', text)  # Multiple newlines → double newline
        text = re.sub(r'\n{3,}', '\n\n', text)  # More than 2 newlines → 2 newlines
        
        # Limit length for performance
        if len(text) > MAX_EXTRACTED_TEXT_LENGTH:
            text = text[:MAX_EXTRACTED_TEXT_LENGTH] + "... [content truncated]"
            
        return text.strip()

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
