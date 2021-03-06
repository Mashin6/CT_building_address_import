# Script from https://github.com/Mashin6/orthogonalize-polygon

import geopandas as gpd
import pandas as pd
import shapely
from shapely import speedups
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely import affinity
import math
import statistics
speedups.enable()


def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.

    The formulae used is the following:
        θ = atan2(sin(Δlong).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))

    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees

    :Returns:
      The bearing in degrees

    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")
    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])
    diffLong = math.radians(pointB[1] - pointA[1])
    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))
    initial_bearing = math.atan2(x, y)
    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing


def calculate_segment_angles(polySimple, maxAngleChange = 45):
    """
    Calculates angles of all polygon segments to cardinal directions.

    :Parameters:
      - `polySimple: shapely polygon object containing simplified building.
      - `maxAngleChange: angle (0,45> degrees. Sets the maximum angle when 
                         the segment is still considered to continue in the 
                         same direction as the previous segment.

    :Returns:
      - orgAngle: Segments bearing
      - corAngle: Segments angles to closest cardinal direction
      - dirAngle: Segments direction [N, E, S, W] as [0, 1, 2, 3]

    :Returns Type:
      list
    """
    # Convert limit angle to angle for subtraction
    maxAngleChange = 45 - maxAngleChange
    # Get points Lat/Lon
    simpleX = polySimple.exterior.xy[0]
    simpleY = polySimple.exterior.xy[1]
    # Calculate angle to cardinal directions for each segment of polygon
    orgAngle = [] # Original angles
    corAngle = [] # Correction angles used for rotation
    dirAngle = [] # 0,1,2,3 = N,E,S,W
    limit = [0] * 4
    for i in range(0, (len(simpleX) - 1)):
        point1 = (simpleY[i], simpleX[i])
        point2 = (simpleY[i+1], simpleX[i+1])
        angle = calculate_initial_compass_bearing(point1, point2)
        if angle > (45 + limit[1]) and angle <= (135 - limit[1]):
            orgAngle.append(angle)
            corAngle.append(angle - 90)
            dirAngle.append(1)
        elif angle > (135 + limit[2]) and angle <= (225 - limit[2]):
            orgAngle.append(angle)
            corAngle.append(angle - 180)
            dirAngle.append(2)
        elif angle > (225 + limit[3]) and angle <= (315 - limit[3]):
            orgAngle.append(angle)
            corAngle.append(angle - 270)
            dirAngle.append(3)
        elif angle > (315 + limit[0]) and angle <= 360:
            orgAngle.append(angle)
            corAngle.append(angle - 360)
            dirAngle.append(0)
        elif angle >= 0 and angle <= (45 - limit[0]):
            orgAngle.append(angle)
            corAngle.append(angle)
            dirAngle.append(0)
        limit = [0] * 4
        limit[ dirAngle[i] ] = maxAngleChange               # Set angle limit for the current direction
        limit[ (dirAngle[i] + 1) % 4 ] = -maxAngleChange    # Extend the angles for the adjacent directions
        limit[ (dirAngle[i] - 1) % 4 ] = -maxAngleChange
    return orgAngle, corAngle, dirAngle



def rotate_polygon(polySimple, angle):
    """
    Rotates polygon around its centroid for given angle.

    :Parameters:
      - `polySimple: shapely polygon object containing simplified building.
      - `angle: angle of rotation in decimal degrees.  
                Positive = counter-clockwise, Negative = clockwise 

    :Returns:
      - bSR: rotated polygon

    :Returns Type:
      shapely polygon
    """
    # Create WGS84 referenced GeoSeries
    bS = gpd.GeoDataFrame({'geometry':[polySimple]})
    bS.crs = "EPSG:4326"
    # Temporary reproject to Merkator and rotate by median angle
    bSR = bS.to_crs('epsg:3857')
    bSR = bSR.rotate(angle, origin='centroid', use_radians=False) 
    bSR = bSR.to_crs('epsg:4326')
    # Extract only shapely polygon object
    bSR = bSR[0]
    return bSR


def orthogonalize_polygon(polygon):
    """
    Master function that makes all angles in polygon 90 or 180 degrees.
    Idea adapted from JOSM function orthogonalize
    1) Calculate bearing [0-360 deg] of each polygon segment
    2) From bearing determine general direction [N, E, S ,W] and calculate angle from nearest cardinal direction for each segment
    3) Rotate polygon by median angle (mean migth be better for polygons with few segments) to align segments with xy coord axes
    4) For vertical segments replace X coordinates of the points with their mean value
       For horizontal segments replace Y coordinates of the points with their mean value
    5) Rotate back

    :Parameters:
      - `polygon: shapely polygon object containing simplified building.

    :Returns:
      - polyOrthog: orthogonalized shapely polygon where all angles are 90 or 180 degrees

    :Returns Type:
      shapely polygon
    """
    # Check if polygon has inner rings that we want to orthogonalize as well
    rings = [ Polygon(polygon.exterior) ]
    for inner in list(polygon.interiors):
        rings.append(Polygon(inner))
    polyOrthog = [] 
    for polySimple in rings:
        # Get angles from cardinal directions of all segments
        orgAngle, corAngle, dirAngle = calculate_segment_angles(polySimple)
        # Calculate median angle that will be used for rotation
        if statistics.stdev(corAngle) < 30:
            medAngle = statistics.median(corAngle)
            #avAngle = statistics.mean(corAngle)
        else:
            medAngle = 45  # Account for cases when building is at ~45˚ and we can't decide if to turn clockwise or anti-clockwise
        # Rotate polygon to align its edges to cardinal directions
        polySimpleR = rotate_polygon(polySimple, medAngle)
        # Get directions of rotated polygon segments
        orgAngle, corAngle, dirAngle = calculate_segment_angles(polySimpleR, 15)
        # Account for 180 degree turns
        dirAngleRotated = dirAngle[1:] + dirAngle[0:1]
        dirAngle = [ dirAngle[i-1] if abs(dirAngle[i]-dirAngleRotated[i])==2 else dirAngle[i] for i in range(len(dirAngle)) ] 
        # Get Lat/Lon of rotated polygon points
        rotatedX = polySimpleR.exterior.xy[0].tolist()
        rotatedY = polySimpleR.exterior.xy[1].tolist()
        # Scan backwards to check if starting segment is a continuation of straight region in the same direction
        shift = 0
        for i in range(1, len(dirAngle)):
            if dirAngle[0] == dirAngle[-i]:
                shift = i
            else:
                break
        # If the first segment is part of continuing straight region then reset the index to it's beginning
        if shift != 0:
            dirAngle  = dirAngle[-shift:] + dirAngle[:-shift]
            orgAngle  = orgAngle[-shift:] + orgAngle[:-shift]
            rotatedX = rotatedX[-shift-1:-1] + rotatedX[:-shift]    # First and last points are the same in closed polygons
            rotatedY = rotatedY[-shift-1:-1] + rotatedY[:-shift]
        # Cycle through all segments
        # Adjust points coodinates by taking the average of points in segment
        dirAngle.append(dirAngle[0]) # Append dummy value
        orgAngle.append(orgAngle[0]) # Append dummy value
        segmentBuffer = []
        for i in range(0, len(dirAngle) - 1):
            if orgAngle[i] % 90 > 30 and orgAngle[i] % 90 < 60:
                continue
            segmentBuffer.append(i) 
            if dirAngle[i] == dirAngle[i + 1]: # If next segment is of same orientation, we need 180 deg angle for straight line. Keep checking.
                if orgAngle[i + 1] % 90 > 30 and orgAngle[i + 1] % 90 < 60:
                    pass
                else:
                    continue
            if dirAngle[i] in {0, 2}:   # for N,S segments avereage x coordinate
                tempX = statistics.mean( rotatedX[ segmentBuffer[0]:segmentBuffer[-1]+2 ] )
                # Update with new coordinates
                rotatedX[ segmentBuffer[0]:segmentBuffer[-1]+2 ] = [tempX] * (len(segmentBuffer) + 1)  # Segment has 2 points therefore +1
            elif dirAngle[i] in {1, 3}:  # for E,W segments avereage y coordinate 
                tempY = statistics.mean( rotatedY[ segmentBuffer[0]:segmentBuffer[-1]+2 ] )
                # Update with new coordinates
                rotatedY[ segmentBuffer[0]:segmentBuffer[-1]+2 ] = [tempY] * (len(segmentBuffer) + 1)   
            if 0 in segmentBuffer:  # Copy change in first point to its last point so we don't lose it during Reverse shift
                rotatedX[-1] = rotatedX[0]
                rotatedY[-1] = rotatedY[0]
            segmentBuffer = []
        # Reverse shift so we get polygon with the same start/end point as before
        if shift != 0:
            rotatedX = rotatedX[shift:] + rotatedX[1:shift+1]    # First and last points are the same in closed polygons
            rotatedY = rotatedY[shift:] + rotatedY[1:shift+1]
        else:
            rotatedX[0] = rotatedX[-1]    # Copy updated coordinates to first node
            rotatedY[0] = rotatedY[-1]
        # Create polygon from new points
        polyNew = Polygon(zip(rotatedX, rotatedY))
        # Rotate polygon back
        polyNew = rotate_polygon(polyNew, -medAngle)
        # Add to list of finihed rings
        polyOrthog.append(polyNew)
    # Recreate the original object
    polyOrthog = Polygon(polyOrthog[0].exterior, [inner.exterior for inner in polyOrthog[1:]])
    return polyOrthog


#### Main Part

import fiona
import sys
import numpy


shpfile = fiona.open('/Buildigns_footprints_testing/geo_export_98ca6254-03aa-48e1-8931-a446a182959c.shp')
args = sys.argv
sliceNo = int(args[1])
buildings = gpd.GeoDataFrame.from_features(shpfile[ sliceNo*50000 : (sliceNo+1)*50000 ])

buildings.crs = "EPSG:4326"
buildings.to_file('/Buildigns_footprints_testing/raw/BuildCT_raw_' + str(sliceNo) + '.geojson', driver='GeoJSON')

buildings['geometry'] = buildings['geometry'].simplify(0.000005, preserve_topology=True)

for i in range(0, len(buildings)):
    build = buildings.loc[i, 'geometry']
    if build.type == 'MultiPolygon':
        multipolygon = []
        # For multipolygons process all polygon rings one-by-one
        for poly in build:
            buildOrtho = orthogonalize_polygon(poly)
            x = gpd.overlay(gpd.GeoDataFrame({'geometry':[buildOrtho]}, crs="EPSG:4326").loc[0:0], gpd.GeoDataFrame({'geometry':[poly]}, crs="EPSG:4326").loc[0:0], how='intersection')
            if len(x) > 0:
                buildings.loc[i, 'perc.change'] = round( x.loc[0, 'geometry'].area/buildings.loc[i, 'geometry'].area, 3)
                if buildings.loc[i, 'perc.change'] < 0.95:
                    orgAngle, corAngle, dirAngle = calculate_segment_angles(poly)
                    if statistics.stdev(corAngle) > 9:
                        multipolygon.append(poly)
                        continue 
            else:
                multipolygon.append(poly)
                continue
            multipolygon.append(buildOrtho)
        buildings.loc[i, 'geometry'] = gpd.GeoSeries(MultiPolygon(multipolygon)).values # Workaround for Pandas/Geopandas bug
        # buildings.loc[i, 'geometry'] = MultiPolygon(multipolygon)   # Does not work
    else:    
        # Orthogonalize
        buildOrtho = orthogonalize_polygon(build)
        x = gpd.overlay(gpd.GeoDataFrame({'geometry':[buildOrtho]}, crs="EPSG:4326").loc[0:0], buildings.loc[i:i], how='intersection')
        if len(x) > 0:
            buildings.loc[i, 'perc.change'] = round( x.loc[0, 'geometry'].area/buildings.loc[i, 'geometry'].area, 3)
            if buildings.loc[i, 'perc.change'] < 0.95:
                orgAngle, corAngle, dirAngle = calculate_segment_angles(build)
                if statistics.stdev(corAngle) > 9:
                    continue       
            buildings.loc[i, 'geometry'] = buildOrtho
    

buildings['geometry'] = buildings['geometry'].simplify(0.000001, preserve_topology=True)

buildings.to_file('/Buildigns_footprints_testing/ortho/BuildCT_ortho_' + str(sliceNo) + '.geojson', driver='GeoJSON')


