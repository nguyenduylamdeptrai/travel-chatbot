#!/usr/bin/env python3
"""
Test script for web search tool
"""
import sys
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv(override=True)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from tools.web_search import web_search
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Cannot import web_search tool: {e}")
    print("   Please install langchain-tavily: pip install langchain-tavily")
    WEB_SEARCH_AVAILABLE = False
    web_search = None

def test_web_search_tool():
    """Test web search tool with various queries"""
    if not WEB_SEARCH_AVAILABLE:
        print("\n⚠️  Skipping web search tests - tool not available")
        return
    
    print("\n" + "="*80)
    print("TESTING WEB SEARCH TOOL")
    print("="*80)
    
    test_cases = [
        "món ăn ngon tại Hà Nội",
        "địa điểm du lịch Đà Nẵng",
        "thời tiết Hà Nội hôm nay",
        "chùa Keo Thái Bình",
        "bãi biển Nha Trang",
        "khách sạn Sapa",
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Query: '{query}'")
        print("-" * 80)
        
        try:
            result = web_search.invoke({"query": query})
            
            if not result:
                print("✗ NO RESULTS: Empty list returned")
            elif isinstance(result, list):
                print(f"✓ SUCCESS: Found {len(result)} results")
                for j, res in enumerate(result, 1):
                    print(f"\n  Result {j}:")
                    print(f"    Title: {res.get('title', 'N/A')[:80]}...")
                    print(f"    URL: {res.get('url', 'N/A')[:80]}...")
                    content_preview = res.get('content', 'N/A')[:150]
                    print(f"    Content: {content_preview}...")
                    print(f"    Content length: {len(res.get('content', ''))} characters")
            else:
                print(f"✗ UNEXPECTED RESULT TYPE: {type(result)}")
                print(f"  Result: {result}")
        except Exception as e:
            print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        print()

def test_web_search_detailed():
    """Test web search with detailed output"""
    if not WEB_SEARCH_AVAILABLE:
        print("\n⚠️  Skipping detailed web search test - tool not available")
        return
    
    print("\n" + "="*80)
    print("DETAILED WEB SEARCH TEST")
    print("="*80)
    
    query = "món ăn ngon tại Hà Nội"
    print(f"\nQuery: '{query}'")
    print("-" * 80)
    
    try:
        result = web_search.invoke({"query": query})
        
        if result:
            print(f"\n✓ Found {len(result)} results")
            print("\n" + "="*80)
            print("FULL JSON OUTPUT:")
            print("="*80)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("✗ No results returned")
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WEB SEARCH TOOL TESTING SCRIPT")
    print("="*80)
    
    # Check if TAVILY_API_KEY is set
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: TAVILY_API_KEY not found in environment variables")
        print("   The web search tool requires a Tavily API key to work.")
        print("   Please set TAVILY_API_KEY in your .env file")
    else:
        print(f"\n✓ TAVILY_API_KEY found (length: {len(api_key)} characters)")
    
    if WEB_SEARCH_AVAILABLE:
        # Run basic tests
        test_web_search_tool()
        
        # Run detailed test
        test_web_search_detailed()
    else:
        print("\n" + "="*80)
        print("INSTALLATION REQUIRED")
        print("="*80)
        print("To test the web search tool, please install the required package:")
        print("  pip install langchain-tavily")
        print("\nAlso ensure you have TAVILY_API_KEY set in your .env file")
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)

