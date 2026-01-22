#!/usr/bin/env python3
"""
II-Researcher MCP Client Wrapper

A simple command-line client for the II-Researcher MCP server.
Provides an easy interface to perform deep research queries.

Usage:
    python research_client.py "What is quantum computing?" --report-type advanced
    python research_client.py --question "Machine learning basics" --type basic
    python research_client.py --help

Environment Variables:
    MCP_SERVER_URL - URL of the MCP server (default: http://localhost:8765)
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.client.sse import sse_client
from mcp import ClientSession


class ResearchClient:
    """Client wrapper for II-Researcher MCP server."""

    def __init__(self, server_url: str = "http://localhost:8765"):
        """Initialize the research client.

        Args:
            server_url: URL of the MCP server (default: http://localhost:8765)
        """
        self.server_url = server_url.rstrip('/')
        self.sse_url = f"{self.server_url}/sse"

    async def connect_and_research(
        self,
        question: str,
        report_type: str = "advanced",
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """Connect to MCP server and perform research.

        Args:
            question: The research question
            report_type: Type of report ("basic" or "advanced")
            timeout_seconds: Timeout for the research operation

        Returns:
            Research results dictionary
        """
        print(f"🔍 Connecting to II-Researcher MCP server at {self.server_url}")
        print(f"📝 Research question: {question}")
        print(f"📊 Report type: {report_type}")
        print("-" * 60)

        try:
            # Connect to MCP server
            async with sse_client(self.sse_url) as (read, write):
                async with ClientSession(read, write) as session:
                    print("⏳ Initializing session...")
                    await session.initialize()
                    print("✅ Session initialized")

                    # Call deep_research tool
                    print("🚀 Starting deep research...")
                    start_time = datetime.now()

                    result = await session.call_tool("deep_research", {
                        "question": question,
                        "report_type": report_type
                    })

                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    if result.content:
                        research_data = json.loads(result.content[0].text)

                        # Add execution metadata
                        research_data["client_metadata"] = {
                            "server_url": self.server_url,
                            "execution_time_seconds": duration,
                            "timestamp": end_time.isoformat(),
                        }

                        return research_data
                    else:
                        return {
                            "error": "No response content from server",
                            "question": question,
                            "report_type": report_type,
                        }

        except Exception as e:
            error_msg = f"Research failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "question": question,
                "report_type": report_type,
            }

    def print_results(self, results: Dict[str, Any]) -> None:
        """Print research results in a nice format.

        Args:
            results: Research results dictionary
        """
        if "error" in results:
            print("❌ ERROR:")
            print(f"   {results['error']}")
            return

        print("✅ RESEARCH COMPLETED")
        print("-" * 60)

        # Metadata
        metadata = results.get("metadata", {})
        if metadata:
            duration = metadata.get("duration_seconds", 0)
            turns = metadata.get("turns", 0)
            print("📊 METADATA:")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Research turns: {turns}")
            print(f"   Timestamp: {metadata.get('timestamp', 'N/A')}")
            print()

        # Sources
        sources = results.get("sources", {})
        visited_urls = sources.get("visited_urls", [])
        search_queries = sources.get("search_queries", [])

        if visited_urls or search_queries:
            print("🔗 SOURCES:")
            if search_queries:
                print(f"   Search queries: {len(search_queries)}")
                for i, query in enumerate(search_queries[:3], 1):
                    print(f"     {i}. {query}")
                if len(search_queries) > 3:
                    print(f"     ... and {len(search_queries) - 3} more")
            if visited_urls:
                print(f"   URLs visited: {len(visited_urls)}")
                for i, url in enumerate(visited_urls[:3], 1):
                    print(f"     {i}. {url}")
                if len(visited_urls) > 3:
                    print(f"     ... and {len(visited_urls) - 3} more")
            print()

        # Report
        report = results.get("report", "")
        if report:
            print("📄 RESEARCH REPORT:")
            print("-" * 60)

            # Print report with line wrapping
            lines = report.split('\n')
            for line in lines:
                # Handle very long lines
                if len(line) > 120:
                    # Try to wrap at word boundaries
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) > 120:
                            print(current_line)
                            current_line = word
                        else:
                            current_line += " " + word if current_line else word
                    if current_line:
                        print(current_line)
                else:
                    print(line)

            print("-" * 60)
            print(f"📏 Report length: {len(report)} characters")
        else:
            print("⚠️  No report content generated")

    async def research_and_print(
        self,
        question: str,
        report_type: str = "advanced",
        timeout_seconds: int = 300
    ) -> None:
        """Perform research and print results.

        Args:
            question: Research question
            report_type: Report type ("basic" or "advanced")
            timeout_seconds: Timeout in seconds
        """
        results = await self.connect_and_research(question, report_type, timeout_seconds)
        self.print_results(results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="II-Researcher MCP Client - Perform deep research queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research_client.py "What is quantum computing?"
  python research_client.py --question "Machine learning basics" --type basic
  python research_client.py "Python programming" --server http://localhost:8765
  python research_client.py "AI ethics" --timeout 600

Environment Variables:
  MCP_SERVER_URL - URL of the MCP server (default: http://localhost:8765)
        """
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Research question (can also use --question)"
    )

    parser.add_argument(
        "--question",
        "-q",
        help="Research question"
    )

    parser.add_argument(
        "--type",
        "--report-type",
        choices=["basic", "advanced"],
        default="advanced",
        help="Report type (default: advanced)"
    )

    parser.add_argument(
        "--server",
        "--server-url",
        default=os.getenv("MCP_SERVER_URL", "http://localhost:8765"),
        help="MCP server URL (default: http://localhost:8765)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of formatted text"
    )

    args = parser.parse_args()

    # Get the question from positional arg or --question flag
    question = args.question or args.q
    if not question:
        parser.error("Question is required. Use positional argument or --question flag.")

    # Create client
    client = ResearchClient(args.server)

    # Run research
    try:
        if args.json:
            # JSON output mode
            results = asyncio.run(client.connect_and_research(question, args.type, args.timeout))
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            # Formatted output mode
            asyncio.run(client.research_and_print(question, args.type, args.timeout))

    except KeyboardInterrupt:
        print("\n🛑 Research interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
