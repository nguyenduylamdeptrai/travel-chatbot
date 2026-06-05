import json
from typing import Optional
import os

def append_to_jsonl_file(
    content: str,
    location: Optional[str] = None,
    file_path: str = "/data/travel_data.jsonl",
):
    # Build dictionary từ input
    data = {"content": content, "location": None}
    if location:
        data["location"] = location

    # Thay \n trong chuỗi bằng \\n để giữ 1 dòng JSON
    def escape_newlines(obj):
        if isinstance(obj, dict):
            return {k: escape_newlines(v) for k, v in obj.items()}
        elif isinstance(obj, str):
            return obj.replace("\n", "\\n")
        else:
            return obj

    escaped_data = escape_newlines(data)

    # Ghi vào file JSONL
    with open(file_path, "a", encoding="utf-8") as f:
        json_line = json.dumps(escaped_data, ensure_ascii=False)
        f.write(json_line + "\n")


crawl_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "/crawl/data/travel_data.jsonl")
with open(crawl_file, "r", encoding="utf-8") as f:
    print(f"Reading from {crawl_file}")
    for line in f:
        # print(f"Processing line: {line.strip()}")
        try:
            item = json.loads(line)
            # print(f"Processing item: {item}")
            name = item.get("name", "")
            address = item.get("address", None)
            content_raw = item.get("content", "")
            # print(f"Processing item: {name} at {address} has content: {content_raw}")
            # if isinstance(content_raw, list):
            #     content_str = "\n".join(content_raw)
            # else:
            #     content_str = str(content_raw)
            # if not content_str.strip():
            #     continue
            new_content = f"{name}\n{content_raw}" if name else content_raw
            # print('a')
            append_to_jsonl_file(content=new_content, location=address)
            # print(f"Appended content for {name} at {address}")
            # break
        except Exception as e:
            # Bỏ qua dòng lỗi
            continue

