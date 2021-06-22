import geopandas as gpd
import pandas as pd
import shapely
from shapely import speedups
import matplotlib.pyplot as plt
import re
speedups.enable()

building = gpd.read_file("/Users/Desktop/Buildings/Glastonbury/Glastonbury Buildings.geojson")

building.crs = "EPSG:4326"

building = building.drop(columns=['building'])

building.loc[(building['TYPE'].isin(["BLDG", "OUT-BLDG", "FOUNDATION", "CONSTRUCT", "MOBILE"])), ['building']] = "yes"
building.loc[(building['TYPE'] == "RUIN"), ['abandoned:building']] = "yes"
building['ele'] = (round(building['BASE_ELEV'].astype(float) / 3.28084))
building['height'] = round((building['ELEV_SL'].astype(float) - building['BASE_ELEV'].astype(float)) / 3.28084)

building = building.drop(columns=['TYPE', 'BASE_ELEV', 'ELEV_SL', 'OBJECTID', 'SHAPE_Area', 'SHAPE_Leng', 'type'])

building.loc[(building['ele'].notnull()), ['ele']] = building.loc[(building['ele'].notnull()), ['ele']].astype(int)

building.to_file('/Users/Desktop/Buildings/Glastonbury/Glastonbury-parsed.geojson', driver='GeoJSON')