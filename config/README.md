# Scraper Locations Configuration

This directory contains the configuration file for all scrapers in the project.

## File: `scraper_locations.json`

This JSON file defines which locations/routes each scraper should process.

### Structure

```json
{
  "hotels": {
    "places": ["location1", "location2", ...]
  },
  "planes": {
    "routes": ["FROM.TO", ...]
  },
  "coaches": {
    "routes": ["route_param1", ...]
  },
  "shopeefood": {
    "cities": ["city1", "city2", ...],
    "base_url_template": "https://shopeefood.vn/{city}/food/deals"
  }
}
```

### How to Add New Locations

#### Hotels (`hotels.places`)
- Format: `PLACE_ID.City%20Name` (URL-encoded)
- Example: `"10010498.Nha%20Trang"` for Nha Trang
- To find place IDs, check Traveloka URLs when searching for hotels in a city

#### Flights (`planes.routes`)
- Format: `FROM.TO` (airport codes)
- Example: `"SGN.DAD"` for Ho Chi Minh → Da Nang
- Common codes:
  - `SGN` = Ho Chi Minh City
  - `DAD` = Da Nang
  - `CXR` = Cam Ranh (Nha Trang)
  - `HAN` = Ha Noi
  - `HPH` = Hai Phong

#### Coaches (`coaches.routes`)
- Format: URL-encoded route parameters from Traveloka
- Example: `"a10010498&stt=CITY_GEO.CITY_GEO&stn=Ho%20Chi%20Minh%20City.Nha%20Trang&"`
- To find route parameters, inspect Traveloka coach search URLs

#### ShopeeFood (`shopeefood.cities`)
- Format: City name in URL format (lowercase, hyphenated)
- Example: `"ho-chi-minh"` for Ho Chi Minh City
- The URL template will automatically format: `https://shopeefood.vn/{city}/food/deals`

### Example: Adding a New City

To add Phu Quoc hotels:

1. Find the Traveloka place ID for Phu Quoc (check URL when searching)
2. Add to `hotels.places`:
   ```json
   "hotels": {
     "places": [
       ...existing places...,
       "PLACE_ID.Phú%20Quốc"
     ]
   }
   ```

3. Run the scraper:
   ```bash
   python -m scripts.run_traveloka_scrapers
   ```

### Fallback Behavior

If the configuration file is missing or corrupted, each scraper will fall back to its default hardcoded locations. This ensures the scrapers continue to work even without the config file.

### Notes

- All scrapers read from this single configuration file
- Changes to the config file take effect the next time you run the scrapers
- The config file uses UTF-8 encoding to support Vietnamese characters
- URL encoding is required for some fields (use `%20` for spaces, etc.)

