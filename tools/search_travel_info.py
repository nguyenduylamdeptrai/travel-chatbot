from typing import Optional, List, Dict
import unicodedata
import os
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
from travel_vectorstore.storage import TravelVectorStorage


def _run_web_search(query: str) -> List[Dict[str, str]]:
    """Run Tavily web search (best effort). Returns list of {title,url,content}."""
    try:
        from langchain_tavily import TavilySearch
    except Exception as e:
        print(f"Web search unavailable (missing langchain_tavily): {e}")
        return []

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("Web search skipped: TAVILY_API_KEY not set.")
        return []

    try:
        search = TavilySearch(api_key=api_key)
        resp = search.run(query)
        results = resp.get("results", []) if isinstance(resp, dict) else resp
        formatted = []
        for res in results[:3]:
            formatted.append(
                {
                    "title": res.get("title", ""),
                    "url": res.get("url", ""),
                    "content": res.get("content", ""),
                }
            )
        print(f"Web search returned {len(formatted)} results")
        return formatted
    except Exception as e:
        print(f"Web search error: {type(e).__name__}: {e}")
        return []


def _norm_text(s: str) -> str:
    """Lowercase + strip accents for accent-insensitive matching."""
    if not s:
        return ""
    return (
        unicodedata.normalize("NFD", s)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


@tool("search_travel_info")
def search_travel_info(query: str, location: Optional[str] = None) -> str:
    """
    Tìm kiếm thông tin du lịch từ cơ sở dữ liệu nội bộ.

    Sử dụng khi người dùng hỏi về địa điểm du lịch, địa danh nổi tiếng, nơi nên đi chơi, cảnh đẹp, nghỉ dưỡng, ẩm thực hoặc bất kỳ thông tin du lịch nào.

    Args:
        query (str): câu hỏi của người dùng
        location (Optional[str], optional): Địa điểm mà người dùng nhắc tới nếu có. Defaults to None.

    Returns:
        str: các đề xuất kết quả dựa trên truy vấn
    """
    print("=" * 50)
    print("Using search tool...")
    print(f"Query: {query}, Location: {location}")
    print("=" * 50)

    try:
        storage = TravelVectorStorage()
        norm_loc = _norm_text(location) if location else None

        # First, try semantic search without location filter to avoid accent/variant issues.
        results = storage.search(query=query, location=None)
        print(f"Found {len(results)} results (no location filter)")

        if location:
            filtered_results = []
            for doc in results:
                meta_loc = _norm_text(doc.metadata.get("location", "") if doc.metadata else "")
                content_norm = _norm_text(doc.page_content)

                if meta_loc == norm_loc or (norm_loc and norm_loc in content_norm):
                    filtered_results.append(doc)

            if filtered_results:
                print(f"Found {len(filtered_results)} results matching location '{location}' (accent-insensitive)")
                results = filtered_results
            else:
                print(f"WARNING: No results matching location '{location}'. Returning top general results.")
                results = results[:10]  # Limit to avoid overly long responses

        if not results:
            print("WARNING: No results found")
            return f"ERROR: Không tìm thấy thông tin phù hợp với yêu cầu '{query}'" + (f" tại địa điểm '{location}'" if location else "")
        
        content = "\n\n".join([doc.page_content for doc in results])

        # Also fetch web results (best effort)
        web_results = _run_web_search(query)
        if web_results:
            web_section_lines = ["\n\n[Web search results]"]
            for i, res in enumerate(web_results, 1):
                title = res.get("title", "")
                url = res.get("url", "")
                snippet = res.get("content", "")
                web_section_lines.append(f"{i}. {title}\n   {url}\n   {snippet}")
            content = content + "\n" + "\n".join(web_section_lines)

        print(f"SUCCESS: Returning {len(content)} characters of content (including web search if available)")
        return content
    except Exception as e:
        error_msg = f"Đã xảy ra lỗi khi tìm kiếm thông tin: {str(e)}"
        print(f"ERROR in search_travel_info: {type(e).__name__}: {e}")
        return f"ERROR: {error_msg}"


if __name__ == "__main__":
    query = "DI tích lịch sử ở Hà Nội"
    res = search_travel_info.invoke({"query": query, "location": "Hà Nội"})
    print(res)
