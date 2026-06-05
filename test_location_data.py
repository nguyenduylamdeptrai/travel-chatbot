#!/usr/bin/env python3
"""
Test script to verify location data is correctly loaded from JSONL files
"""
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from travel_vectorstore.loader import load_documents_from_jsonl

def test_location_data():
    """Test if location data is correctly loaded"""
    print("="*80)
    print("TESTING LOCATION DATA IN JSONL FILES")
    print("="*80)
    
    # Test scraped data
    scraped_path = Path("data/travel_data_scraped.jsonl")
    if scraped_path.exists():
        print(f"\n1. Testing {scraped_path}")
        print("-" * 80)
        
        # Count locations
        location_counts = {}
        hanoi_restaurants = []
        
        with open(scraped_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    loc = data.get("location", "N/A")
                    location_counts[loc] = location_counts.get(loc, 0) + 1
                    
                    # Collect Hanoi restaurants
                    if loc == "Hà Nội" and data.get("type") == "restaurant":
                        hanoi_restaurants.append({
                            "line": i,
                            "name": data.get("raw", {}).get("name", "N/A"),
                            "address": data.get("raw", {}).get("address", "N/A"),
                            "location": loc
                        })
                except:
                    pass
        
        print(f"Total lines: {i}")
        print(f"\nLocation distribution:")
        for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {loc}: {count}")
        
        print(f"\nHanoi restaurants found: {len(hanoi_restaurants)}")
        if hanoi_restaurants:
            print("\nFirst 5 Hanoi restaurants:")
            for r in hanoi_restaurants[:5]:
                print(f"  Line {r['line']}: {r['name'][:50]}...")
                print(f"    Address: {r['address'][:60]}...")
                print(f"    Location: {r['location']}")
        
        # Test loading as documents
        print(f"\n2. Testing document loading...")
        print("-" * 80)
        docs = load_documents_from_jsonl(str(scraped_path))
        print(f"Total documents loaded: {len(docs)}")
        
        # Check metadata
        hanoi_docs = [d for d in docs if d.metadata.get("location") == "Hà Nội"]
        print(f"Documents with location='Hà Nội': {len(hanoi_docs)}")
        
        if hanoi_docs:
            print("\nFirst 3 Hanoi document metadata:")
            for d in hanoi_docs[:3]:
                print(f"  Location: {d.metadata.get('location')}")
                print(f"  Source: {d.metadata.get('source')}")
                print(f"  Type: {d.metadata.get('type')}")
                print(f"  Content preview: {d.page_content[:80]}...")
                print()
        
        # Test search simulation
        print(f"3. Testing location filter simulation...")
        print("-" * 80)
        query_location = "Hà Nội"
        matching_docs = [
            d for d in docs 
            if d.metadata.get("location") and d.metadata.get("location").lower() == query_location.lower()
        ]
        print(f"Documents matching location='{query_location}': {len(matching_docs)}")
        
        if matching_docs:
            print("\nFirst 3 matching documents:")
            for d in matching_docs[:3]:
                print(f"  Location: {d.metadata.get('location')}")
                print(f"  Content: {d.page_content[:100]}...")
                print()
        else:
            print("⚠️  WARNING: No documents match the location filter!")
            print("   This means the vectorstore cache needs to be rebuilt.")
    else:
        print(f"✗ File not found: {scraped_path}")

if __name__ == "__main__":
    test_location_data()

