import json
from langchain_core.documents import Document
from typing import List


def load_documents_from_jsonl(jsonl_path: str) -> List[Document]:
    documents = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            documents.append(
                Document(
                    page_content=data["content"],
                    metadata={k: v for k, v in data.items() if k != "content"},
                )
            )
    return documents
