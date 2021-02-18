### Processing of Hartford building dataset


import geopandas as gpd
import pandas as pd
import shapely
from shapely import speedups
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely import affinity
import matplotlib.pyplot as plt
import math
import statistics
speedups.enable()

# Load data
buildings = gpd.read_file('/Buildigns_footprints_testing/Hartford/Building-shp/Building.shp')

# Drop unwanted columns
buildings = buildings.drop(columns=['OBJECTID', 'Source', 'Date_Added', 'ShapeSTAre', 'ShapeSTLen'])

# Remove unwannted structures
buildings = buildings.drop(buildings.query('CODE == "Cement Pad"').index)
buildings = buildings.drop(buildings.query('CODE == "Patio"').index)
buildings = buildings.reset_index()

# Label buildigns with OSM tags
buildings.loc[buildings['CODE'].isnull(), 'building'] = "yes"
buildings.loc[buildings['CODE'] == 'Building', 'building'] = "yes"
buildings.loc[buildings['CODE'] == 'Foundation', 'building'] = "yes"
buildings.loc[buildings['CODE'] == 'Ruins', 'building'] = "ruins"
buildings.loc[buildings['CODE'] == 'Greenhouse', 'building'] = "greenhouse"
buildings.loc[buildings['CODE'] == 'Deck', 'building:part'] = "deck"

## For buildings with decks turn all connected ways to building:parts and create building outline
decks = buildings.loc[buildings['CODE'] == 'Deck', ]
validBuilds = buildings.loc[buildings.is_valid,]
#notvalidBuilds = buildings.loc[ ~buildings.is_valid,]

# Find indexes of polygons that touch decks
touching = []
for j in range(1, len(decks)):
    indx = validBuilds[ validBuilds['geometry'].intersects(decks.iloc[j]['geometry']) ].index.tolist()
    touching.append(indx)
# Remove empty values 
touching = list(filter(None, touching))
# Flatten
touching = [item for items in touching for item in items]
# Remove duplicates
touching = list(set(touching))

# Get decks + touching parts
decks2 = validBuilds.loc[touching, ]
# Convert to building parts
decks2.loc[decks2['building'] == 'yes', 'building:part'] = 'yes'
decks2 = decks2.drop(columns=['building'])
# Get buildings that don't have attached Deck
nonDeckBuildsIndex = list(set(buildings.index) - set(decks2.index))
nonDeckBuilds = buildings.loc[ nonDeckBuildsIndex, ]

# Combine Deck shapes and touching parts into outlines
decks_u = gpd.GeoDataFrame(geometry=list(decks2.unary_union))
# Tag as buildings
decks_u.loc[:, 'building'] = 'yes'


# Merge Deck shapes and touching parts with their outlines
decks_comb = pd.concat([decks2, decks_u]).pipe(gpd.GeoDataFrame)

# Fix those decks that were not touching any buildings and now they have a duplicate outline
# Re-tag building:part ->  building
decks_comb.loc[ decks_comb.duplicated(subset='geometry', keep='last'), ['building:part', 'building'] ] = [ None , 'deck']
# Remove duplicate outlines
decks_comb = decks_comb.drop_duplicates(subset='geometry', keep='first')


# Recreate the full data set (deck-containing buildings + non-deck builsgins)
buildings_comb = pd.concat([nonDeckBuilds, decks_comb]).pipe(gpd.GeoDataFrame)

# Clean up unwanted parts
buildings_comb = buildings_comb.drop(columns=['index', 'CODE'])

# Simplify to remove extra nodes
#buildings_comb = buildings_comb.drop(buildings_comb.query('geometry == None').index)
#buildings_comb['geometry'] = buildings_comb['geometry'].simplify(0.000001, preserve_topology=True)


# Set coord system
buildings_comb.crs = "EPSG:4326"

# Save output to shape file
buildings_comb.to_file('/Buildigns_footprints_testing/Hartford/Building-shp/Hartford_buildings_parsedSimp1.geojson', driver='GeoJSON')

