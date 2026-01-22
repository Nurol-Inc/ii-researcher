#!/usr/bin/env python3
"""
Test client for II-Researcher MCP Server

This script tests the MCP server using the standard MCP Python client.
It can be used to verify that the server is working correctly.

Usage:
    # Test against stdio server (requires server to be running)
    python test_client.py stdio
    
    # Test against HTTP server
    python test_client.py http http://localhost:8765
    
    # Quick test with default settings
    python test_client.py
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Try to import MCP client
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("Warning: mcp package not installed. Install with: pip install mcp")

# Try to import httpx for HTTP testing
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


async def test_stdio_server():
    """Test the MCP server via stdio transport."""
    if not HAS_MCP:
        print("Error: mcp package required for stdio testing")
        return False
    
    print("\n" + "="*60)
    print("Testing II-Researcher MCP Server (stdio)")
    print("="*60)
    
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp.enhanced_server"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env={
            **os.environ,
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "empty"),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", "http://192.168.10.86:8000/v1"),
            "SEARCH_PROVIDER": os.getenv("SEARCH_PROVIDER", "duckduckgo"),
            "SCRAPER_PROVIDER": os.getenv("SCRAPER_PROVIDER", "bs"),
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Test 1: List available tools
            print("\n[Test 1] Listing available tools...")
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Test 2: Get server status
            print("\n[Test 2] Getting server status...")
            result = await session.call_tool("get_server_status", {})
            print(f"Server status: {json.dumps(result.content[0].text, indent=2) if result.content else 'No response'}")
            
            # Test 3: Web search
            print("\n[Test 3] Testing web search...")
            result = await session.call_tool("web_search", {
                "queries": ["Python programming language"],
                "max_results": 3
            })
            if result.content:
                search_result = json.loads(result.content[0].text)
                print(f"Search provider: {search_result.get('provider')}")
                print(f"Results count: {search_result.get('results', [{}])[0].get('count', 0)}")
            
            print("\n" + "="*60)
            print("All stdio tests completed!")
            print("="*60)
            return True


async def test_http_server(base_url: str = "http://localhost:8765"):
    """Test the MCP server via HTTP transport."""
    if not HAS_HTTPX:
        print("Error: httpx package required for HTTP testing. Install with: pip install httpx")
        return False
    
    print("\n" + "="*60)
    print(f"Testing II-Researcher MCP Server (HTTP: {base_url})")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Test 1: Health check
        print("\n[Test 1] Health check...")
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Health check: {response.status_code}")
        except Exception as e:
            print(f"Health check failed: {e}")
        
        # Test 2: List tools via MCP
        print("\n[Test 2] Listing tools via MCP...")
        try:
            response = await client.post(
                f"{base_url}/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                }
            )
            if response.status_code == 200:
                data = response.json()
                tools = data.get("result", {}).get("tools", [])
                print(f"Available tools: {[t['name'] for t in tools]}")
        except Exception as e:
            print(f"List tools failed: {e}")
        
        # Test 3: Call get_server_status
        print("\n[Test 3] Getting server status...")
        try:
            response = await client.post(
                f"{base_url}/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "get_server_status",
                        "arguments": {}
                    },
                    "id": 2
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Server status: {json.dumps(data.get('result', {}), indent=2)}")
        except Exception as e:
            print(f"Get status failed: {e}")
        
        # Test 4: Web search
        print("\n[Test 4] Testing web search...")
        try:
            response = await client.post(
                f"{base_url}/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "web_search",
                        "arguments": {
                            "queries": ["Python programming"],
                            "max_results": 3
                        }
                    },
                    "id": 3
                },
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                print(f"Search completed: {json.dumps(result, indent=2)[:500]}...")
        except Exception as e:
            print(f"Web search failed: {e}")
        
        print("\n" + "="*60)
        print("All HTTP tests completed!")
        print("="*60)
        return True


async def test_deep_research_http(base_url: str = "http://localhost:8765"):
    """Test deep research via HTTP (longer running test)."""
    if not HAS_HTTPX:
        print("Error: httpx package required")
        return False
    
    print("\n" + "="*60)
    print("Testing Deep Research (this may take several minutes)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        start_time = datetime.now()
        
        print("\nStarting deep research on: 'What is quantum computing?'")
        try:
            response = await client.post(
                f"{base_url}/mcp/",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "deep_research",
                        "arguments": {
                            "question": "What is quantum computing and what are its main applications?",
                            "report_type": "basic"
                        }
                    },
                    "id": 10
                }
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                
                if isinstance(result, list) and len(result) > 0:
                    # Handle MCP content array format
                    content = result[0].get("text", "")
                    result = json.loads(content) if isinstance(content, str) else content
                
                print(f"\nResearch completed in {duration:.1f} seconds")
                print(f"Report length: {len(result.get('report', '')) if isinstance(result, dict) else 'N/A'} characters")
                
                if isinstance(result, dict) and result.get('report'):
                    print("\n--- Report Preview (first 1000 chars) ---")
                    print(result['report'][:1000])
                    print("\n--- End Preview ---")
            else:
                print(f"Research failed with status: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Deep research failed: {e}")
            import traceback
            traceback.print_exc()
    
    return True


def main():
    """Main entry point."""
    args = sys.argv[1:]
    
    if not args or args[0] == "help":
        print(__doc__)
        return
    
    transport = args[0] if args else "http"
    
    if transport == "stdio":
        asyncio.run(test_stdio_server())
    elif transport == "http":
        base_url = args[1] if len(args) > 1 else "http://localhost:8765"
        asyncio.run(test_http_server(base_url))
    elif transport == "research":
        base_url = args[1] if len(args) > 1 else "http://localhost:8765"
        asyncio.run(test_deep_research_http(base_url))
    else:
        print(f"Unknown transport: {transport}")
        print("Use 'stdio', 'http', or 'research'")


if __name__ == "__main__":
    main()

