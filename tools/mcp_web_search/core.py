"""
MCP Web Search Tool - Core Implementation
Tool chính để tìm kiếm web và trả về danh sách URLs cho user
"""

import json
from typing import List, Dict, Any
from .google_api import search_google_api
from .constants import DEFAULT_NUM_RESULTS


def web_search_tool(query: str, language: str = "en") -> str:
    """
    Web Search Tool - Tìm kiếm Google và trả về danh sách URLs
    
    Tool này hoạt động như Google Search, trả về danh sách ~15 URLs đầu tiên
    cùng với title, snippet và source domain cho mỗi kết quả.
    
    Args:
        query (str): Từ khóa tìm kiếm (bắt buộc)
        language (str): Ngôn ngữ tìm kiếm - 'en', 'vi', etc. (default: 'en')
    
    Returns:
        str: JSON string chứa danh sách kết quả tìm kiếm theo format:
        {
            "query": "từ khóa tìm kiếm",
            "total_results": 15,
            "results": [
                {
                    "rank": 1,
                    "title": "Tiêu đề trang web",
                    "url": "https://example.com/page",
                    "snippet": "Mô tả ngắn gọn về nội dung trang...",
                    "source": "example.com"
                }
            ],
            "status": "success"
        }
    
    Example Usage:
        web_search_tool("CSS accessibility guidelines")
        web_search_tool("React virtual scrolling performance")
        web_search_tool("Python machine learning tutorials", "en")
    """
    
    try:
        # Validate inputs
        if not query or not isinstance(query, str):
            return json.dumps({
                "query": query,
                "total_results": 0,
                "results": [],
                "status": "error",
                "message": "Query khong hop le. Vui long cung cap tu khoa tim kiem."
            }, ensure_ascii=False, indent=2)
        
        # Use configured default number of results  
        num_results = DEFAULT_NUM_RESULTS
        
        # Validate language
        if not isinstance(language, str):
            language = "en"
        
        pass  # Searching Google
        
        # Perform search using Google Custom Search API
        raw_results = search_google_api(query, num_results)
        
        # Format results
        formatted_results = []
        for rank, result in enumerate(raw_results, 1):
            formatted_results.append({
                "rank": rank,
                "title": result["title"],
                "url": result["url"],
                "snippet": result["snippet"],
                "source": result["source"]
            })
        
        # Prepare response
        response = {
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "status": "success"
        }
        
        # Add metadata if we have results
        if formatted_results:
            pass  # Found results
            response["message"] = f"Tìm thấy {len(formatted_results)} kết quả cho '{query}'"
        else:
            pass  # No results
            response["message"] = f"Không tìm thấy kết quả nào cho '{query}'"
            response["status"] = "no_results"
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        pass  # Error logged
        
        return json.dumps({
            "query": query,
            "total_results": 0,
            "results": [],
            "status": "error",
            "message": str(e)
        }, ensure_ascii=False, indent=2)


def get_tool_description() -> Dict[str, Any]:
    """
    Trả về tool description cho MCP server registration
    """
    return {
        "name": "web_search_tool",
        "description": """**Web Search Tool** - Tim kiem Google va tra ve danh sach URLs

**Chức năng chính:**
- Tìm kiếm trên Google với từ khóa được cung cấp
- Trả về ~15 URLs đầu tiên kèm theo title, snippet và source
- Hoạt động như Google Search thông thường
- Hỗ trợ nhiều ngôn ngữ tìm kiếm

**Use Cases:**
- Tìm kiếm thông tin, bài viết, tutorials
- Research về topics cụ thể  
- Tìm documentation, coding guides
- Lấy danh sách sources để đọc thêm

**Output Format:**
Trả về JSON với danh sách kết quả ranked theo thứ tự relevance, 
mỗi kết quả có title, URL, snippet và source domain.""",

        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Từ khóa tìm kiếm (bắt buộc). Ví dụ: 'CSS accessibility guidelines', 'React performance optimization'"
                },

                "language": {
                    "type": "string",
                    "description": "Ngôn ngữ tìm kiếm: 'en' (English), 'vi' (Vietnamese), 'ja' (Japanese), etc. (default: 'en')",
                    "default": "en"
                }
            },
            "required": ["query"]
        }
    }


# Test function
if __name__ == "__main__":
    # Test tool
    test_query = "CSS prefers-contrast high prefers-reduced-motion reduce accessibility"
    result = web_search_tool(test_query)
    
    print("Test Result:")
    print(result)
