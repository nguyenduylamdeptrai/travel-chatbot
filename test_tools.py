#!/usr/bin/env python3
"""
Test script for weather and search travel info tools
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tools.get_weather import get_weather
from tools.search_travel_info import search_travel_info
import json

def test_weather_tool():
    """Test weather tool with explicit values"""
    print("\n" + "="*80)
    print("TESTING WEATHER TOOL")
    print("="*80)
    
    test_cases = [
        {"location": "Hà Nội", "days": 1},
        {"location": "Ho Chi Minh City", "days": 1},
        {"location": "Đà Nẵng", "days": 3},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Location: {test_case['location']}, Days: {test_case['days']}")
        print("-" * 80)
        
        try:
            result = get_weather.invoke(test_case)

            if isinstance(result, str):
                # The tool now returns a friendly string summary on success
                if result.startswith("ERROR:"):
                    print(f"✗ ERROR: {result}")
                else:
                    print("✓ SUCCESS: Weather data summary")
                    print(result)
            elif isinstance(result, dict):
                # Fallback if tool returns dict
                print("✓ SUCCESS: Weather data retrieved (dict)")
                print(f"  Location: {result.get('location', 'N/A')}")
                print(f"  Status: {result.get('status', 'N/A')}")
                print(f"  Temperature: {result.get('temperature_c', 'N/A')}°C")
                print(f"  Feels like: {result.get('feels_like_c', 'N/A')}°C")
                print(f"  Humidity: {result.get('humidity', 'N/A')}%")
                print(f"  Wind: {result.get('wind_kph', 'N/A')} km/h")
                print(f"  Forecast days: {len(result.get('forecast_days', []))}")
            else:
                print(f"✗ UNEXPECTED RESULT TYPE: {type(result)}")
                print(f"  Result: {result}")
        except Exception as e:
            print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
        
        print()

def test_search_travel_info_tool():
    """Test search travel info tool with explicit values"""
    print("\n" + "="*80)
    print("TESTING SEARCH TRAVEL INFO TOOL")
    print("="*80)
    
    test_cases = [
        {"query": "món ăn ngon", "location": "Hà Nội"},
        {"query": "di tích lịch sử", "location": "Hà Nội"},
        {"query": "địa điểm du lịch nổi tiếng", "location": "Hà Nội"},
        {"query": "chùa nổi tiếng", "location": "Thái Bình"},
        {"query": "bãi biển đẹp", "location": "Nha Trang"},
        {"query": "món ăn ngon", "location": None},  # Test without location
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Query: '{test_case['query']}'")
        print(f"Location: {test_case['location'] if test_case['location'] else 'None'}")
        print("-" * 80)
        
        try:
            result = search_travel_info.invoke(test_case)
            
            # Check if result is an error
            if isinstance(result, str):
                if result.startswith("ERROR:"):
                    print(f"✗ ERROR: {result}")
                else:
                    # Success - show preview
                    lines = result.split('\n')
                    preview = '\n'.join(lines[:5])  # First 5 lines
                    print(f"✓ SUCCESS: Found content ({len(result)} characters)")
                    print(f"  Preview (first 5 lines):")
                    print(f"  {preview}")
                    if len(lines) > 5:
                        print(f"  ... ({len(lines) - 5} more lines)")
            else:
                print(f"✗ UNEXPECTED RESULT TYPE: {type(result)}")
                print(f"  Result: {result}")
        except Exception as e:
            print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        print()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TOOL TESTING SCRIPT")
    print("="*80)
    
    # Test weather tool
    test_weather_tool()
    
    # Test search travel info tool
    test_search_travel_info_tool()
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)

