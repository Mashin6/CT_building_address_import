import geopandas as gpd
import pandas as pd
import shapely
from shapely import speedups
import matplotlib.pyplot as plt
import re
speedups.enable()


building = gpd.read_file("/Users/Desktop/Buildings/Stonington/stonington-buildings.shp")
building.crs = "EPSG:4326"

building = building.loc[ building['TYPE'].isin(["FOUNDATION", "DECK"]) == False,]
building['building'] = "yes"
building = building.drop(columns=['TYPE', 'OBJECTID', 'Shape_Area', 'Shape_Leng', 'SOURCE', 'DATE_LOC'])
building.to_file('/Users/Desktop/Buildings/Stonington/Stonington-parsed.geojson', driver='GeoJSON')
