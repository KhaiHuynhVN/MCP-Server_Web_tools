from mcp.server.fastmcp import FastMCP

# Import Web Search tool
from tools.mcp_web_search.core import web_search_tool, get_tool_description as get_web_search_description

# Import Web Fetch tool
from tools.mcp_web_fetch.core import web_fetch_tool, get_tool_description as get_web_fetch_description

# Tạo MCP server
mcp = FastMCP("Web Tools MCP Server")

# Add tools
web_search_desc = get_web_search_description()
mcp.add_tool(web_search_tool, description=web_search_desc["description"])
# Add web fetch tool
web_fetch_desc = get_web_fetch_description()
mcp.add_tool(web_fetch_tool, description=web_fetch_desc["description"])

if __name__ == "__main__":
    # Chạy server với transport=stdio
    mcp.run(transport="stdio")