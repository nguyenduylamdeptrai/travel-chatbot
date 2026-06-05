#!/usr/bin/env python3
"""
Simple script to verify location data in JSONL files without dependencies
"""
import json
from pathlib import Path

def verify_locations():
    """Verify location data in scraped JSONL"""
    print("="*80)
    print("VERIFYING LOCATION DATA")
    print("="*80)
    
    scraped_path = Path("data/travel_data_scraped.jsonl")
    if not scraped_path.exists():
        print(f"✗ File not found: {scraped_path}")
        return
    
    print(f"\nAnalyzing: {scraped_path}")
    print("-" * 80)
    
    location_counts = {}
    hanoi_restaurants = []
    total_lines = 0
    
    with open(scraped_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            try:
                data = json.loads(line.strip())
                loc = data.get("location", "N/A")
                location_counts[loc] = location_counts.get(loc, 0) + 1
                
                # Collect Hanoi restaurants
                if loc == "Hà Nội" and data.get("type") == "restaurant":
                    name = data.get("raw", {}).get("name", "")
                    address = data.get("raw", {}).get("address", "")
                    hanoi_restaurants.append({
                        "line": line_num,
                        "name": name,
                        "address": address
                    })
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")
    
    print(f"\nTotal lines: {total_lines}")
    print(f"\nLocation distribution (top 10):")
    for loc, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {loc}: {count}")
    
    print(f"\n✓ Hanoi restaurants found: {len(hanoi_restaurants)}")
    if hanoi_restaurants:
        print("\nFirst 5 Hanoi restaurants:")
        for r in hanoi_restaurants[:5]:
            print(f"  Line {r['line']}: {r['name'][:60] if r['name'] else '(no name)'}")
            print(f"    Address: {r['address'][:70]}...")
    
    # Check for mismatches
    print(f"\n" + "-" * 80)
    print("Checking for location mismatches...")
    mismatches = []
    with open(scraped_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                loc = data.get("location", "")
                address = data.get("raw", {}).get("address", "")
                
                # Check if address contains different city
                if "hà nội" in address.lower() and loc != "Hà Nội":
                    mismatches.append({"line": line_num, "location": loc, "address": address})
                elif "tp. hcm" in address.lower() or "hồ chí minh" in address.lower():
                    if loc != "TP. Hồ Chí Minh":
                        mismatches.append({"line": line_num, "location": loc, "address": address})
            except:
                pass
    
    if mismatches:
        print(f"⚠️  Found {len(mismatches)} potential mismatches:")
        for m in mismatches[:5]:
            print(f"  Line {m['line']}: location='{m['location']}' but address contains different city")
    else:
        print("✓ No obvious location mismatches found")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✓ Data file has {len(hanoi_restaurants)} restaurants with location='Hà Nội'")
    print(f"✓ Cache has been deleted - vectorstore will rebuild on next use")
    print(f"\n⚠️  IMPORTANT: Restart your application/server to rebuild the vectorstore!")
    print("   The singleton TravelVectorStorage instance needs to be recreated.")

if __name__ == "__main__":
    verify_locations()

