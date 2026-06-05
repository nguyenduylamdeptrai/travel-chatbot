import pandas as pd
from pathlib import Path
from Crawl_Traveloka.Hotel_Traveloka_WithDef import processing_data

root = Path("Crawl_Traveloka")  # instead of Processed_Data_Hotel

hotel_by_place = {}
for csv in root.glob("Hotel_*_Traveloka.csv"):
    place = csv.stem.replace("Hotel_", "").replace("_Traveloka", "")
    df = pd.read_csv(csv)
    hotel_by_place[place] = df

processed = processing_data(hotel_by_place)