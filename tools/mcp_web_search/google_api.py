"""
Google Custom Search API Implementation for MCP Web Search Tool
"""

import requests
from typing import Dict, Any, List, Optional
from .constants import GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID, MAX_RESULTS_PER_REQUEST, MAX_API_REQUESTS


class GoogleCustomSearchAPI:
    """Google Custom Search API client"""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.search_engine_id = search_engine_id or GOOGLE_SEARCH_ENGINE_ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or self.api_key == "your_google_api_key_here":
            raise ValueError("Google API key not configured in constants.py")
        if not self.search_engine_id or self.search_engine_id == "your_search_engine_id_here":
            raise ValueError("Google Search Engine ID not configured in constants.py")

    def search(self, query: str, num_results: int = 15, language: str = "en") -> List[Dict[str, str]]:
        """
        Tìm kiếm Google và trả về danh sách kết quả
        
        Args:
            query: Từ khóa tìm kiếm
            num_results: Số lượng kết quả mong muốn (max 10 per request)
            language: Ngôn ngữ tìm kiếm
            
        Returns:
            List[Dict]: Danh sách kết quả với format tương thích với existing tool
        """
        
        # Google Custom Search API chỉ cho phép max results per request (từ config)
        # Nếu cần nhiều hơn, phải gọi multiple requests với start parameter
        all_results = []
        requests_needed = min((num_results + MAX_RESULTS_PER_REQUEST - 1) // MAX_RESULTS_PER_REQUEST, MAX_API_REQUESTS)
        
        for request_num in range(requests_needed):
            start_index = request_num * MAX_RESULTS_PER_REQUEST + 1
            current_limit = min(MAX_RESULTS_PER_REQUEST, num_results - len(all_results))
            
            if current_limit <= 0:
                break
                
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': current_limit,
                'start': start_index,
                'lr': f'lang_{language}' if language != 'en' else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if 'error' in data:
                    error_msg = data['error'].get('message', 'Unknown API error')
                    raise Exception(f"Google API error: {error_msg}")
                
                # Process results
                if 'items' in data:
                    for item in data['items']:
                        all_results.append({
                            'title': item.get('title', 'No title'),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', 'No description'),
                            'source': item.get('displayLink', self._extract_domain(item.get('link', '')))
                        })
                
                # If we got fewer results than requested, stop
                if len(data.get('items', [])) < current_limit:
                    break
                    
            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error: {str(e)}")
            except Exception as e:
                raise Exception(f"Search error: {str(e)}")
        
        return all_results[:num_results]

    def _extract_domain(self, url: str) -> str:
        """Extract domain từ URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"


def search_google_api(query: str, num_results: int = 15) -> List[Dict[str, str]]:
    """
    Main function để search Google thông qua API
    
    Args:
        query: Search query
        num_results: Số lượng kết quả mong muốn
        
    Returns:
        List of search results compatible với existing format
    """
    try:
        api_client = GoogleCustomSearchAPI()
        return api_client.search(query, num_results)
    except ValueError as e:
        # Missing API credentials
        raise Exception(f"Google API not configured: {str(e)}")
    except Exception as e:
        # Other errors
        raise e


# Test function
if __name__ == "__main__":
    # Test API
    try:
        results = search_google_api("Python programming tutorial", 5)
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Source: {result['source']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
    except Exception as e:
        print(f"Error: {e}")
