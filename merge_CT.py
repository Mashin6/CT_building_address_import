# Merge all datasets

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import Polygon
from shapely import speedups
import numpy as np
speedups.enable()


# Load all orthogonalized fragments and merge
buildings = None

for f in range(0,30):
    part = gpd.read_file("/Buildigns_footprints_testing/Processed1/Processed_good/BuildCT_ortho_" + str(f) + ".geojson")
    part.crs = "EPSG:4326"
    buildings = pd.concat([buildings, part]).pipe(gpd.GeoDataFrame)

# Reset index and drop columns unnecessary columns
buildings = buildings.reset_index()
buildings = buildings.drop(columns=['objectid', 'shape_area', 'shape_leng', 'perc.change', 'index'])
buildings.crs = "EPSG:4326"

# Tag as Building
buildings['building'] = "yes"


# Cut out Hartford buildings
boundHartford = gpd.read_file("/Buildigns_footprints_testing/boundaries/Hartford.geojson")
boundHartford.crs = "EPSG:4326"

buildings['centroid'] = buildings.centroid
buildings = buildings.set_geometry('centroid')

boundHartfordUnion = boundHartford.geometry.unary_union
noHartford = buildings[~buildings.geometry.within(boundHartfordUnion)]
noHartford = noHartford.set_geometry('geometry')

# Load Hartford data and merge
hartford = gpd.read_file("/Buildigns_footprints_testing/Hartford/Building-shp/Hartford_buildings_parsedSimp1.geojson")
hartford.crs = "EPSG:4326"
buildingsFull = pd.concat([noHartford, hartford]).pipe(gpd.GeoDataFrame)
buildingsFull['centroid'] = buildingsFull.centroid

# Load Addresses and merge
address = gpd.read_file("/Buildigns_footprints_testing/Address/CTAddressDedup-parsed.geojson")
address.crs = "EPSG:4326"
address['centroid'] = address['geometry']

#buildingsAddress = pd.concat([buildingsFull, address]).pipe(gpd.GeoDataFrame)
buildingsAddress = pd.concat([buildingsFull, address_dedup]).pipe(gpd.GeoDataFrame)
buildingsAddress.crs = "EPSG:4326"

# Save all Buildings and all addresses for safekeeping
buildingsAddress.drop(columns=['centroid']).to_file('/Buildigns_footprints_testing/CTBuildingsAddressAll.geojson', driver='GeoJSON')

# Cut out WestCOG
boundCTnoWestCOG = gpd.read_file("/Buildigns_footprints_testing/boundaries/CTnoWestCOG.geojson")
boundCTnoWestCOG.crs = "EPSG:4326"

boundCTnoWestCOGUnion = boundCTnoWestCOG.geometry.unary_union

buildingsAddress = buildingsAddress.set_geometry('centroid')
buildingsAddressFinal = buildingsAddress[buildingsAddress.geometry.within(boundCTnoWestCOGUnion)]


# Save the final version of the data
buildingsAddressFinal = buildingsAddressFinal.set_geometry('geometry')
buildingsAddressFinal = buildingsAddressFinal.reset_index()
buildingsAddressFinal = buildingsAddressFinal.drop(columns=['centroid', 'index'])
buildingsAddressFinal.to_file('/Buildigns_footprints_testing/Buildigns_footprints_testing/CTBuildingsAddressFinal.geojson', driver='GeoJSON')
# 1,968,644 objects


## Split data into square grid 


# Get BBOX of westCOG polygon
xmin,ymin,xmax,ymax =  boundCTnoWestCOG.total_bounds

# We want grid of 22x41 squares
rows = 20 # 41
cols = 23 # 46
width = ((xmax-xmin) / cols)
height = ((ymax-ymin) / rows)

# Set Orin square
XleftOrigin = xmin
XrightOrigin = xmin + width
YtopOrigin = ymax
YbottomOrigin = ymax - height

# Make sqaures
polygons = []
for i in range(cols):
    Ytop = YtopOrigin
    Ybottom = YbottomOrigin
    for j in range(rows):
        polygons.append(Polygon([(XleftOrigin, Ytop), (XrightOrigin, Ytop), (XrightOrigin, Ybottom), (XleftOrigin, Ybottom)])) 
        Ytop = Ytop - height
        Ybottom = Ybottom - height
    XleftOrigin = XleftOrigin + width
    XrightOrigin = XrightOrigin + width

grid = gpd.GeoDataFrame({'geometry':polygons})
grid.crs = "EPSG:4326"

# Load high population areas for smaller grids
hiPop = gpd.read_file("/Buildigns_footprints_testing/boundaries/HighDensityAreas.geojson")
hiPop.crs = "EPSG:4326"
hiPopdUnion = hiPop.geometry.unary_union
gridHiPop = grid[~grid.geometry.disjoint(hiPopdUnion)]

# Split each square into 8 smaller squares
splitPolygons = []
for i in gridHiPop.index:
    xmin,ymin,xmax,ymax =  gridHiPop.loc[i:i].total_bounds
    width = (xmax-xmin) / 4
    height = (ymax-ymin) / 4
    for c in range(0,4):
        for r in range(0,4): 
            splitPolygons.append(Polygon([(xmin + c*width,     ymin + r*height), 
                                          (xmin + c*width,     ymin + (r+1)*height), 
                                          (xmin + (c+1)*width, ymin + (r+1)*height), 
                                          (xmin + (c+1)*width, ymin + r*height)]))

splitPolygons = gpd.GeoDataFrame({'geometry': splitPolygons})

# Merge nonsplitted with splitted squares
completeGrid = pd.concat([grid[grid.geometry.disjoint(hiPopdUnion)], splitPolygons]).pipe(gpd.GeoDataFrame)


# Filter grid for sqaures inside CT
completeGrid = completeGrid[~completeGrid.geometry.disjoint(boundCTnoWestCOGUnion)]
completeGrid = completeGrid.reset_index()
completeGrid = completeGrid.drop(columns=['index'])


# Create tags for URL
for i in range(0, len(completeGrid)):
    completeGrid.loc[i:i, 'name'] = "Fragment_" + str(i+1)
    completeGrid.loc[i:i, 'URL'] = "https://storage.cloud.com/ct-import-bucket/Parts/" + completeGrid.loc[i]['name'] + ".geojson"


# Save grid
completeGrid.to_file('/Buildigns_footprints_testing/grid.geojson', driver='GeoJSON')


# Split data according to the grid
buildingsAddressFinal['centroid'] = buildingsAddressFinal.centroid
buildingsAddressFinal = buildingsAddressFinal.set_geometry('centroid')

drop = []
for i in range(0, len(completeGrid)):
    square = buildingsAddressFinal[buildingsAddressFinal.geometry.within(completeGrid.loc[i:i].geometry.unary_union)]
    if len(square) == 0:
        print("part row" + str(i) +  "is empty")
        drop.append(i)
        continue
    square = square.set_geometry('geometry')
    square = square.drop(columns=['centroid'])
    path = '/Buildigns_footprints_testing/Parts/' + completeGrid['name'].iloc[i] + '.geojson'
    square.to_file(path, driver='GeoJSON')


# Remove squares that were empty
completeGrid.drop(drop, inplace=True)
completeGrid.to_file('/Buildigns_footprints_testing/gridFinal.geojson', driver='GeoJSON')






