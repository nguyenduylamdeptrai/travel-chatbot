#!/usr/bin/env python3
"""
Script to rebuild the FAISS vectorstore with corrected location data
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from travel_vectorstore.storage import TravelVectorStorage

def main():
    print("="*80)
    print("REBUILDING FAISS VECTORSTORE WITH CORRECTED LOCATIONS")
    print("="*80)
    
    print("\nThis will:")
    print("1. Delete the existing FAISS cache")
    print("2. Rebuild the vectorstore from travel_data.jsonl and travel_data_scraped.jsonl")
    print("3. Include all corrected location data")
    print("\nThis may take a few minutes...")
    
    try:
        # Reset and rebuild the vectorstore
        print("\n" + "-"*80)
        print("Rebuilding vectorstore...")
        print("-"*80)
        storage = TravelVectorStorage(reset=True)
        print("\n✓ Vectorstore rebuilt successfully!")
        print("\nThe corrected location data is now available in the vectorstore.")
        print("You can now search for food in Hanoi and it should work correctly.")
        
    except Exception as e:
        print(f"\n✗ Error rebuilding vectorstore: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

