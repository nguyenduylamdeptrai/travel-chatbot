#!/usr/bin/env python3
"""
Script to rebuild travel_data_scraped.jsonl with corrected location data
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.build_scraped_corpus import build_scraped_jsonl, ROOT

def main():
    print("="*80)
    print("FIXING LOCATION DATA IN SCRAPED CORPUS")
    print("="*80)
    
    output_path = ROOT / "data" / "travel_data_scraped.jsonl"
    
    # Backup existing file if it exists
    if output_path.exists():
        backup_path = output_path.with_suffix('.jsonl.backup')
        print(f"\nBacking up existing file to: {backup_path}")
        import shutil
        shutil.copy2(output_path, backup_path)
        print("✓ Backup created")
    
    # Rebuild with corrected location extraction
    print(f"\nRebuilding scraped corpus with location extraction...")
    build_scraped_jsonl(output_path)
    
    print("\n" + "="*80)
    print("REBUILD COMPLETE")
    print("="*80)
    print(f"\nOutput file: {output_path}")
    print("\nNext steps:")
    print("1. Rebuild the vectorstore to include corrected locations:")
    print("   python -c 'from travel_vectorstore.storage import TravelVectorStorage; TravelVectorStorage(reset=True)'")
    print("\n2. Or run the preload script:")
    print("   python scripts/preload_models.py")

if __name__ == "__main__":
    main()

