"""
MCP Web Fetch Tool - Core Implementation
Tool chính để fetch và extract content từ URLs
"""

import json
import time
from typing import List, Dict, Any, Union
from .fetch_api import fetch_web_content


def web_fetch_tool(url: Union[str, List[str]], extract_links: bool = True) -> str:
    """
    Web Fetch Tool - Fetch và extract content từ URL(s)
    
    Tool này fetch content từ một hoặc nhiều URLs, extract readable text,
    metadata và trả về structured data. Có thể sử dụng standalone hoặc
    kết hợp với web_search_tool để lấy content chi tiết.
    
    Args:
        url (str|List[str]): URL hoặc danh sách URLs để fetch content
        extract_links (bool): Có extract links từ page không (default: True)
    
    Returns:
        str: JSON string chứa extracted content theo format:
        {
            "total_urls": 1,
            "results": [
                {
                    "url": "https://example.com",
                    "title": "Page Title",
                    "description": "Meta description...",
                    "content": "Main text content...",
                    "content_type": "text/html",
                    "word_count": 250,
                    "links": [...],
                    "status": "success"
                }
            ],
            "status": "success"
        }
    
    Example Usage:
        web_fetch_tool("https://example.com/article")
        web_fetch_tool(["https://site1.com", "https://site2.com"])
        web_fetch_tool("https://example.com", extract_links=False)
    """
    
    try:
        # Normalize input to list
        urls = [url] if isinstance(url, str) else url
        
        # Validate inputs
        if not urls or not all(isinstance(u, str) for u in urls):
            return json.dumps({
                "total_urls": 0,
                "results": [],
                "status": "error",
                "message": "URL không hợp lệ. Vui lòng cung cấp URL hoặc danh sách URLs."
            }, ensure_ascii=False, indent=2)
        
        # MASSIVE URL limit - for comprehensive documentation research
        MAX_URLS_PER_REQUEST = 50  # MASSIVE increase for documentation batch processing
        if len(urls) > MAX_URLS_PER_REQUEST:
            return json.dumps({
                "total_urls": len(urls),
                "results": [],
                "status": "error", 
                "message": f"Quá nhiều URLs. Tối đa {MAX_URLS_PER_REQUEST} URLs mỗi request."
            }, ensure_ascii=False, indent=2)
        
        pass  # Fetching content
        
        # Process each URL
        results = []
        successful_fetches = 0
        
        for url_to_fetch in urls:
            try:
                pass  # Processing URL
                
                # Fetch content
                content_data = fetch_web_content(url_to_fetch.strip())
                
                # Apply extract_links setting with safety checks
                try:
                    if not extract_links and 'links' in content_data:
                        content_data['links'] = []
                    
                    # Ensure links field always exists and is valid
                    if 'links' not in content_data:
                        content_data['links'] = []
                    elif not isinstance(content_data['links'], list):
                        pass  # Invalid links format
                        content_data['links'] = []
                        
                except Exception as e:
                    pass  # Error processing links
                    content_data['links'] = []
                
                results.append(content_data)
                successful_fetches += 1
                
            except ValueError as e:
                # Client-side errors (invalid URL, unsupported content, etc.)
                results.append({
                    "url": url_to_fetch,
                    "title": "",
                    "description": "",
                    "content": "",
                    "content_type": "",
                    "word_count": 0,
                    "links": [],
                    "status": "error",
                    "error": str(e),
                    "error_type": "client_error",
                    "error_details": {
                        "timestamp": str(time.time()),
                        "error_category": "validation"
                    }
                })
                
            except Exception as e:
                # Server/network errors
                results.append({
                    "url": url_to_fetch,
                    "title": "",
                    "description": "",
                    "content": "",
                    "content_type": "",
                    "word_count": 0,
                    "links": [],
                    "status": "error",
                    "error": f"Không thể truy cập URL: {str(e)}",
                    "error_type": "network_error",
                    "error_details": {
                        "timestamp": str(time.time()),
                        "error_category": "connection",
                        "original_error": str(e)
                    }
                })
        
        # Prepare response
        response = {
            "total_urls": len(urls),
            "successful_fetches": successful_fetches,
            "results": results,
            "status": "success" if successful_fetches > 0 else "error"
        }
        
        # Add summary message
        if successful_fetches > 0:
            total_words = sum(r.get('word_count', 0) for r in results if r.get('status') == 'success')
            response["message"] = f"Thành công fetch {successful_fetches}/{len(urls)} URLs. Tổng cộng {total_words} từ."
        else:
            response["message"] = f"Không thể fetch content từ bất kỳ URL nào trong {len(urls)} URLs."
            response["status"] = "error"
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        # Comprehensive top-level error response
        return json.dumps({
            "total_urls": len(urls) if 'urls' in locals() else 0,
            "successful_fetches": 0,
            "results": [],
            "status": "error",
            "error": str(e),
            "error_type": "tool_error",
            "error_details": {
                "timestamp": str(time.time()),
                "error_category": "tool_failure",
                "function": "web_fetch_tool",
                "original_error": str(e)
            },
            "message": f"Tool execution failed: {str(e)}"
        }, ensure_ascii=False, indent=2)


def get_tool_description() -> Dict[str, Any]:
    """
    Trả về tool description cho MCP server registration
    """
    return {
        "name": "web_fetch_tool",
        "description": """**Web Fetch Tool** - Fetch và extract content từ URLs

**Chức năng chính:**
- Fetch content từ một hoặc nhiều URLs
- Extract readable text, title, description từ HTML
- Support multiple content types (HTML, JSON, plain text)
- Extract links từ pages (optional)
- Error handling robust cho failed requests

**Use Cases:**
- Lấy nội dung chi tiết từ URLs tìm được qua web_search_tool
- Extract text content từ articles, blogs, documentation
- Batch processing multiple URLs cùng lúc
- Content analysis và research

**Output Format:**
Trả về JSON với extracted content cho mỗi URL, bao gồm title, 
description, main content, word count, và links (nếu enabled).""",

        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": ["string", "array"],
                    "description": "URL hoặc danh sách URLs để fetch content. Max 5 URLs per request. Ví dụ: 'https://example.com' hoặc ['https://site1.com', 'https://site2.com']",
                    "items": {
                        "type": "string"
                    }
                },
                
                "extract_links": {
                    "type": "boolean", 
                    "description": "Có extract links từ pages không. Default: true. Set false để chỉ lấy content chính.",
                    "default": True
                }
            },
            "required": ["url"]
        }
    }


# Test function
if __name__ == "__main__":
    # Test single URL
    test_url = "https://httpbin.org/html"
    result = web_fetch_tool(test_url)
    
    print("Single URL Test Result:")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test multiple URLs
    test_urls = ["https://httpbin.org/json", "https://httpbin.org/html"]
    result_multi = web_fetch_tool(test_urls, extract_links=False)
    
    print("Multiple URLs Test Result:")
    print(result_multi)
