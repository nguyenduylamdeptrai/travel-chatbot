import os
from typing import List, Optional, Dict

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from travel_vectorstore.loader import load_documents_from_jsonl
from utils.common import singleton
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Get root path of project (parent directory of travel_vectorstore)
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_all_corpus_documents() -> list[Document]:
    """
    Load cả corpus gốc và corpus scrape (nếu có).
    """
    docs: list[Document] = []

    base_jsonl = os.path.join(ROOT_PATH, "data", "travel_data.jsonl")
    if not os.path.exists(base_jsonl):
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu: {base_jsonl}\n"
            f"Vui lòng đảm bảo file travel_data.jsonl tồn tại trong thư mục data/\n"
            f"Working directory hiện tại: {os.getcwd()}"
        )
    docs.extend(load_documents_from_jsonl(base_jsonl))

    scraped_jsonl = os.path.join(ROOT_PATH, "data", "travel_data_scraped.jsonl")
    if os.path.exists(scraped_jsonl):
        print("Loading scraped corpus from travel_data_scraped.jsonl...")
        docs.extend(load_documents_from_jsonl(scraped_jsonl))
    else:
        print("Không tìm thấy travel_data_scraped.jsonl, chỉ sử dụng corpus gốc.")

    return docs


@singleton
class TravelVectorStorage(object):
    def __init__(self, cache: str = None, reset: bool = False):
        # Default cache path in travel_vectorstore directory
        if cache is None:
            cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faiss_cache")
        self.vectorstore = None
        # Ensure embedding model is cached inside project to avoid repeated downloads
        model_cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_cache")
        os.makedirs(model_cache, exist_ok=True)
        self.embedding = HuggingFaceEmbeddings(
            model_name="VoVanPhuc/sup-SimCSE-VietNamese-phobert-base",
            cache_folder=model_cache,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300, chunk_overlap=50, separators=["\n\n", "\n", "."]
        )

        if reset and os.path.exists(cache):
            import shutil

            shutil.rmtree(cache)

        os.makedirs(cache, exist_ok=True)

        self.cache_path = cache
        self.index_file = os.path.join(cache, "index.faiss")
        self.pkl_file = os.path.join(cache, "index.pkl")

        if (
            os.path.exists(self.index_file)
            and os.path.exists(self.pkl_file)
            and not reset
        ):
            print("Loading FAISS vectorstore from cache...")
            self.vectorstore = FAISS.load_local(
                cache, self.embedding, allow_dangerous_deserialization=True
            )
        else:
            print("Building new FAISS vectorstore from JSONL...")
            docs = _load_all_corpus_documents()
            split_docs = self.text_splitter.split_documents(docs)
            self.vectorstore = FAISS.from_documents(split_docs, self.embedding)
            self.vectorstore.save_local(cache)

    def search(
        self, query: str, k: int = 40, location: Optional[str] = None
    ) -> List[Document]:
        """Finding relevant travel info, optionally filtered by location.

        Args:
            query (str): user query
            k (int, optional): top-k results. Defaults to 40.
            location (Optional[str], optional): Location filter. Defaults to None.

        Returns:
            List[Document]: Relevant documents
        """
        results = self.vectorstore.similarity_search(query, k=k)

        if location:
            location_lower = location.lower()
            filtered = [
                doc
                for doc in results
                if (doc_location := doc.metadata.get("location")) and doc_location.lower() == location_lower
            ]
            return filtered

        return results