"""
HTTP Client for Web Fetch Tool - Content fetching and extraction
"""

import requests
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from .constants import (
    REQUEST_TIMEOUT, MAX_CONTENT_SIZE, MAX_REDIRECTS, DEFAULT_HEADERS,
    MAX_EXTRACTED_TEXT_LENGTH, EXTRACT_LINKS, SUPPORTED_CONTENT_TYPES,
    MAX_RETRY_ATTEMPTS, RETRY_DELAY
)


class WebContentFetcher:
    """HTTP client for fetching and extracting web content"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.max_redirects = MAX_REDIRECTS

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
        
        # Attempt fetch with retries
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                response = self._fetch_with_session(url)
                
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
                    
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Progressive delay
                    continue
                raise Exception(f"Failed to fetch URL after {MAX_RETRY_ATTEMPTS} attempts: {str(e)}")
        
        raise Exception("Unexpected error in fetch_content")

    def _fetch_with_session(self, url: str) -> requests.Response:
        """Fetch URL with configured session"""
        response = self.session.get(
            url, 
            timeout=REQUEST_TIMEOUT,
            stream=True,  # Stream for large content handling
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Read content with size limit
        content_chunks = []
        total_size = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            total_size += len(chunk)
            if total_size > MAX_CONTENT_SIZE:
                raise ValueError(f"Content size exceeds limit: {MAX_CONTENT_SIZE} bytes")
            content_chunks.append(chunk)
        
        response._content = b''.join(content_chunks)
        return response

    def _extract_html_content(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Extract content from HTML response"""
        soup = BeautifulSoup(response.content, 'html.parser')
        
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
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': main_content,
            'content_type': 'text/html',
            'links': links,
            'word_count': len(main_content.split()) if main_content else 0,
            'status': 'success'
        }

    def _extract_json_content(self, response: requests.Response, url: str) -> Dict[str, Any]:
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

    def _extract_plain_content(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Extract content from plain text response"""
        content = response.text[:MAX_EXTRACTED_TEXT_LENGTH]
        
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
