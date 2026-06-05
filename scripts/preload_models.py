from transformers import AutoModel, AutoTokenizer
from pathlib import Path

from travel_vectorstore.storage import TravelVectorStorage
from utils.build_scraped_corpus import build_scraped_jsonl, ROOT as PROJECT_ROOT

# Force model cache to live inside the project so it can be reused
CACHE_DIR = PROJECT_ROOT / "travel_vectorstore" / "model_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def preload():
    # Tải trước model embedding HuggingFace
    model_name = "VoVanPhuc/sup-SimCSE-VietNamese-phobert-base"
    cache_dir = str(CACHE_DIR)
    print(f"Downloading model: {model_name} -> cache: {cache_dir}")
    AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
    AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    print("Model downloaded and cached.")

    # Build corpus scrape (nếu có dữ liệu crawler)
    scraped_out = PROJECT_ROOT / "data" / "travel_data_scraped.jsonl"
    print("Building scraped corpus (ShopeeFood + Traveloka) nếu dữ liệu có sẵn...")
    build_scraped_jsonl(scraped_out)

    # Build / refresh FAISS vectorstore (sẽ tự load cả corpus gốc + scraped)
    print("Building / refreshing FAISS vectorstore...")
    TravelVectorStorage(reset=True)
    print("Vectorstore built successfully.")


if __name__ == "__main__":
    preload()
