# Processing addresspoints for CT


import geopandas as gpd
import pandas as pd
import shapely
from shapely import speedups
import matplotlib.pyplot as plt
import re
speedups.enable()

def expandSuffix(text):
    suffixDb = {
    "Av": "Avenue",
    "Ave": "Avenue",
    "Avenu": "Avenue",
    "Aven": "Avenue",
    "Apts": "Apartment",
    "Aly": "Alley",
    "Blvd": "Boulevard",
    "Bl": "Boulevard",
    "Blv": "Boulevard", 
    "Bch": "Beach",
    "Blf": "Bluff",
    "Bnd": "Bend",
    "Br": "Brach",
    "Brg": "Bridge",
    "Brk": "Brook",
    "Cir": "Circle",
    "Ci": "Circle",
    "Cl": "Close",
    "Clf": "Cliff",
    "Cmn": "Common",
    "Cmns": "Commons",
    "Conn": "Connector",
    "Cor": "Corner",
    "Cres": "Crescent",
    "Curv": "Curve",
    "Crt": "Court",
    "Crk": "Creek",
    "Cswy": "Causeway",
    "Ct": "Court",
    "Cour": "Court",
    "Cr": "Crossing",
    "Crsng": "Crossing",
    "Ctr": "Center",
    "Crst": "Crest",
    "Cv": "Cove",
    "Cp": "Camp",
    "Crse": "Course",
    "Prof": "Professional",
    "Pro": "Professional",
    "Div": "Diversion",
    "Dr": "Drive",
    "Dl": "Dale",
    "D": "Drive",
    "Drve": "Drive",
    "Drs": "Drive South",
    "E": "East",
    "Est": "Estates",
    "Fld": "Field",
    "Flds": "Fields",
    "Gdn": "Garden",
    "Gdns": "Gardens",
    "Gr": "Grove",
    "Grv": "Grove",
    "Gln": "Glen",
    "Grn": "Green",
    "Hbr": "Harbor",
    "Hwy": "Highway",
    "Hghwy": "Highway",
    "Hgwy": "Highway",
    "Hl": "Hill",
    "Hls": "Hills",
    "Hlw": "Hollow",
    "Holw": "Hollow",
    "Hts": "Heights",
    "Hgts": "Heights",
    "Lane": "Lane",
    "La": "Lane",
    "Ln": "Lane",
    "Lndg": "Landing",
    "Mnr": "Manor",
    "Mtn": "Mountain",
    "Mt": "Mountain",
    "Ml": "Mill",
    "Mdws": "Meadows",
    "Mdw": "Meadow",
    "Tl": "Trail",
    "Trce": "Trace",
    "N": "North",
    "No": "North",
    "Orch": "Orchard",
    "Pkwy": "Parkway",
    "Pky": "Parkway",
    "Ptwy": "Pentway",
    "Pl": "Place",
    "Plac": "Place",
    "Plz": "Plaza",
    "Pt": "Point",
    "Ptwy": "Pathway",
    "Pnes": "Pines",
    "Rd": "Road",
    "Rwy": "Railway",
    "Riv": "River",
    "S": "South",
    "So": "South",
    "Shr": "Shore",
    "Shrs": "Shores",
    "Spg": "Springs",
    "Spgs": "Springs",
    "Sq": "Square",
    "St": "Saint",
    "Sta": "Station",
    "Sw": "South West",
    "Trl": "Trail",
    "W": "West",
    "Is": "Island",
    "Wy": "Way",
    "Tr": "Terrace",
    "Te": "Terrace",
    "Ter": "Terrace",
    "Terr": "Terrace",
    "Pk": "Park",
    "Pz": "Plaza",
    "Tpke": "Turnpike",
    "Tpk": "Turnpike",
    "Trnpke": "Turnpike",
    "Tnpk": "Turnpike",
    "Turnpi": "Turnpike",
    "Up": "Upper",
    "Wy": "Way",
    "Ex": "Extension",
    "Ext": "Extension",
    "Ext.": "Extension",
    "Knl": "Knoll",
    "Knls": "Knolls",
    "Lk": "Lake",
    "Rdg": "Ridge",
    "Rt": "Route",
    "Rte": "Route",
    "Roughrd": "Rough Road",
    "Vis": "Vista",
    "Vlg": "Village",
    "Vly": "Valley",
    "Xing": "Crossing",
    "Rd(1)": "Road",
    "Rd(2)": "Road",
    "Rd(3)": "Road",
    "Grounds(1)": "Grounds",
    "Grounds(2)": "Grounds",
    "Grounds(2)(2)": "Grounds",
    "Ave(1)": "Avenue",
    "Ave(2)": "Avenue",
    "Ave(Rear)": "Avenue",
    "Dr(Rear)": "Drive",
    "Rd(Rear)": "Road",
    "Gate(2)": "Gate",
    "Ln(1)": "Lane",
    "Ln(2)": "Lane",
    "Ln(Rear)": "Lane",
    "St(Rear)": "Street",
    "Gate(3)": "Gate",
    "Rd.": "Road",
    "Ro": "Road",
    "Roa": "Road",
    "Str": "Street",
    "Hi": "Highway",
    "Lot": "",
    "(REAR)": "",
    "(Rear)": "",
    "Rear)": "",
    "Rea": ""
    }
    for k, v in suffixDb.items():
        if text == None:
            break
        if text == "DR MARTIN LUTHER KING JR":
            text = text.title()
            break
        text = ' '.join(v if word == k else word for word in text.title().split())
    return(text)

# Parse LOCATION tag
def parseLocation(text):
    out = [None] * 4
    #[0] : House number
    #[1] : Unit
    #[2] : Street
    #[3] : City
    # Catch irregular exceptions
    if text == None:
        return(out)
    if text == "LANTERN HL (FKA 137)":
        out[0] = "665"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 133)":
        out[0] = "663"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 131)":
        out[0] = "659"
        out[2] = "Lantern Hill"
        return(out) 
    elif text == "LANTERN HL (FKA 130)":
        out[0] = "658"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 129)":
        out[0] = "657"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 125)":
        out[0] = "663"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 123)":
        out[0] = "651"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 121)":
        out[0] = "649"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 119)":
        out[0] = "647"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 133A)":
        out[0] = "661"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "LANTERN HL (FKA 11 R M)":
        out[0] = "586A"
        out[2] = "Lantern Hill"
        return(out)
    elif text == "9 - 11  A-D High St":
        out[0] = "9-11"
        out[2] = "A-D High Street"
        return(out)
    elif text == "Farm View Dr (Norwich)":
        out[2] = "Farm View Drive"
        out[3] = "Norwich"
        return(out)
    elif text == "Rte 66 S (Lot 6)":
        out[0] = "6"
        out[2] = "Route 66 South"
        return(out)
    elif text == "Rte 66 S (Lot 1)":
        out[0] = "1"
        out[2] = "Route 66 South"
        return(out)
    elif text == "Rt 66 S (Lot 2)":
        out[0] = "2"
        out[2] = "Route 66 South"
        return(out)
    elif text == "Rt 66 S (Lot 3)":
        out[0] = "3"
        out[2] = "Route 66 South"
        return(out)
    elif text == "Rt 87 W (Lot 3)":
        out[0] = "3"
        out[2] = "Route 87 West"
        return(out)
    elif text == "DEPOT ST (REAR)":
        out[2] = "Depot Street"
        return(out)
    elif text == "SOUTH C ST 1/2-4 1/2":
        out[0] = "1/2-4 1/2"
        out[2] = "South C Street"
        return(out)
    elif text == "SOUTH C ST 1/2-8 1/2":
        out[0] = "1/2-8 1/2"
        out[2] = "South C Street"
        return(out)   
    x = text.title().split()
    # House number
    ## For numbers 000023 --> 23
    if x[0].isnumeric():
        out[0] = str(int(x[0]))
        x.pop(0)
    ## For hyphen numbers 1-24
    elif (x[0].find('-') != -1):
        if any(map(str.isdigit, x[0])): ## To exclude A-G Hill Street cases
            out[0] = x[0]
            x.pop(0)
    ## For number-letter conbinations 0002A --> 2A
    elif any(map(str.isdigit, x[0])):
        y = re.split(r'(\d+)', x[0])
        y[1] = str(int(y[1]))
        out[0] = ''.join(y)
        x.pop(0)
    #Unit/apartment number
    if len(x) > 0 :
        if x[0] in {'Rt', 'Rte', 'Route', 'RTE', 'RT', 'ROUTE'}:
            if x[-1].isnumeric() and len(x) > 2:
                if out[0] != None:
                    out[1] = str(int(x[-1]))
                else:
                    out[0] = str(int(x[-1]))
                x.pop(-1)
            elif any(map(str.isdigit, x[-1])) and len(x) > 2:
                if out[0] != None:
                    out[1] = x[-1]
                else:
                    out[0] = x[-1]
                x.pop(-1)
        elif x[-1].isnumeric():
            if out[0] != None:
                out[1] = str(int(x[-1]))
            else:
                out[0] = str(int(x[-1]))
            x.pop(-1)
        elif any(map(str.isdigit, x[-1])):
            if out[0] != None:
                out[1] = x[-1]
            else:
                out[0] = x[-1]
            x.pop(-1)
        elif (x[-1].find('-') != -1):
            if out[0] != None:
                out[1] = x[-1]
            else:
                out[0] = x[-1]
            x.pop(-1)
    out[2] = ' '.join(x)     
    return(out)



# Read data    
address = gpd.read_file("/Buildigns_footprints_testing/Address/Connecticut_Buildings_with_Addresses_experimental.shp")
address.crs = "EPSG:4326"


# Calculate area of buildings
address['area'] = address.geometry.area

# Calculate centroid of the building and set it as address associated geometry
address['geometry'] = address.geometry.centroid


# Remove westCOG towns
# Note: Weston, Ridgefield, New Fairfield are not part of dataset
address = address.loc[ ~address['TOWN_NO'].isin([9, 16, 18, 34, 35, 57, 90, 96, 97, 103, 117, 127, 135, 158, 161]) ]
address = address.reset_index()

# Remove extra columns
address = address.drop(columns=['OBJECTID', 'FID_Parcel', 'Join_Count', 'TARGET_FID', 'TOWN_NO', 'MBL', 'PIN', 'ACRES', 'SeparatorE', 'StreetNa_7', 'Subaddre_2',
  'Subaddre_5', 'Subaddre_8', 'Subaddre_9', 'Subaddre10', 'Subaddre11', 'Subaddre12', 'Subaddre13', 'Subaddre14', 'Subaddre15', 'Subaddre16', 
  'Subaddre17', 'StateName', 'ESN', 'AddressID', 'RelatedAdd', 'AddressRel', 'AddressPar', 'AddressP_1', 'AddressXCo', 'AddressYCo', 'AddressEle',
  'AddressCla', 'AddressLif', 'OfficialSt', 'AddressAno', 'AddressSta', 'AddressEnd', 'AddressDir', 'NeedsRevie', 'Point_ID', 'FID_Buildi', 'CircleBuil',
  'ShapeSTLen', 'ShapeSTAre', 'index', 'Community_', 'USPS_Place', 'County_Pla', 'AddressAut', 'E911_Place', 'AddressLon', 'AddressLat', 'AddressFea',
  'LandmarkNa'])


# Convert address values
address.loc[:,'addr:street'] = [expandSuffix(item) for item in address.loc[:,'CompleteSt']]
address.loc[:,'addr:housenumber'] = address.loc[:,'CompleteAd']
address.loc[:,'addr:postcode'] = address.loc[:,'ZipCode']
address.loc[:,'addr:zip4'] = address.loc[:,'ZipPlus4']

address.loc[address['Municipal_'].notnull(), 'addr:city'] = address.loc[address['Municipal_'].notnull(), 'Municipal_'].apply(lambda x: x.title())
address.loc[address['Municipal_'].isnull(), 'addr:city'] = address.loc[address['Municipal_'].isnull(), 'TOWN']

# If CompleteAd is empty then use AddressN_1, StreetNa_3, StreetNa_4
address.loc[address['addr:housenumber'].isnull() & address['AddressN_1'].notnull() & (address['AddressN_1'] != 0.0), 'addr:housenumber'] = address.loc[address['addr:housenumber'].isnull() & address['AddressN_1'].notnull() & (address['AddressN_1'] != 0.0), 'AddressN_1'].apply(lambda x: int(x))
address.loc[address['addr:street'].isnull(), 'addr:street'] = address.loc[address['addr:street'].isnull(), ['StreetName', 'StreetNa_1', 'StreetNa_2', 'StreetNa_3', 'StreetNa_4', 'StreetNa_5', 'StreetNa_6']].apply(lambda x: ' '.join(filter(lambda y: y not in {None, 'OM', 'M', 'LP', 'Rear', 'GAR', 'REAR'}, x)).title() if x.notnull().any() else None, axis = 1)
address.loc[address['addr:street'].isnull() & address['StreetName'].isin({'OM', 'M', 'LP'}), 'addr:street'] = address.loc[address['addr:street'].isnull() & address['StreetName'].isin({'OM', 'M', 'LP'}), ['StreetNa_1', 'StreetNa_2', 'StreetNa_3', 'StreetNa_4', 'StreetNa_5', 'StreetNa_6', 'StreetName']].apply(lambda x: ' '.join(filter(lambda y: y not in {None, 'Rear', 'GAR', 'REAR'}, x)).title() if x.notnull().any() else None, axis = 1)

address.loc[:,'addr:street'] = [expandSuffix(item) for item in address.loc[:,'addr:street']]

# Parse and use LocationDescription
address.loc[:,['temp_number', 'temp_unit', 'temp_street', 'temp_city']] = [parseLocation(item) for item in address.loc[:,'LocationDe']]
address.loc[:,'temp_street'] = [expandSuffix(item) for item in address.loc[:,'temp_street']]
address.loc[address['addr:housenumber'].isnull(), 'addr:housenumber'] = address.loc[address['addr:housenumber'].isnull(), 'temp_number']
address.loc[address['addr:street'].isnull(), 'addr:street'] = address.loc[address['addr:street'].isnull(), 'temp_street']
address.loc[:,'addr:unit'] = address.loc[:, 'temp_unit']

# Parse and use LOCATION 
address.loc[:,['temp_number', 'temp_unit', 'temp_street', 'temp_city']] = [parseLocation(item) for item in address.loc[:,'LOCATION']]
address.loc[:,'temp_street'] = [expandSuffix(item) for item in address.loc[:,'temp_street']]
address.loc[address['addr:street'].isnull(), 'addr:street'] = address.loc[address['addr:street'].isnull(), 'temp_street'] 
address.loc[address['addr:housenumber'].isnull(), 'addr:housenumber'] = address.loc[address['addr:housenumber'].isnull(), 'temp_number'] 
address.loc[address['addr:street'] == 'Road', 'addr:street'] = address.loc[address['addr:street'] == 'Road', 'temp_street']
address.loc[address['addr:unit'].isnull(), 'addr:unit'] = address.loc[address['addr:unit'].isnull(), 'temp_unit'] 


# Parse and use Comments
address.loc[:,['temp_number', 'temp_unit', 'temp_street', 'temp_city']] = [parseLocation(item) for item in address.loc[:,'Comments']]
address.loc[:,'temp_street'] = [expandSuffix(item) for item in address.loc[:,'temp_street']]
address.loc[address['addr:street'].isnull(), 'addr:street'] = address.loc[address['addr:street'].isnull(), 'temp_street']
address.loc[address['addr:housenumber'].isnull(), 'addr:housenumber'] = address.loc[address['addr:housenumber'].isnull(), 'temp_number']
address.loc[address['addr:unit'].isnull(), 'addr:unit'] = address.loc[address['addr:unit'].isnull(), 'temp_unit'] 


# Units
address.loc[(address['Subaddress'] == 'Unit') & address['Subaddre_1'].notnull() & address['addr:unit'].isnull(), 'addr:unit'] = address.loc[(address['Subaddress'] == 'Unit') & address['Subaddre_1'].notnull() & address['addr:unit'].isnull(), 'Subaddre_1']
address.loc[(address['Subaddress'] == 'Apartment') & address['Subaddre_1'].notnull(), 'addr:flats'] = address.loc[(address['Subaddress'] == 'Apartment') & address['Subaddre_1'].notnull(), 'Subaddre_1']
address.loc[(address['Subaddress'] == 'Building') & address['Subaddre_1'].notnull(), 'addr:building'] = address.loc[(address['Subaddress'] == 'Building') & address['Subaddre_1'].notnull(), 'Subaddre_1']
address.loc[address['Subaddress'] == 'Floor', 'addr:floor'] = address.loc[address['Subaddress'] == 'Floor', 'Subaddre_1']

address.loc[(address['Subaddre_3'] == 'Unit') & address['addr:unit'].isnull(), 'addr:unit'] = address.loc[(address['Subaddre_3'] == 'Unit') & address['addr:unit'].isnull(), 'Subaddre_4']
address.loc[address['Subaddre_3'].isin(['FLOOR', 'Floor', 'FLR', 'LEVEL']) & address['addr:floor'].isnull(), 'addr:floor'] = address.loc[address['Subaddre_3'].isin(['FLOOR', 'Floor', 'FLR']) & address['addr:floor'].isnull(), 'Subaddre_4']


address.loc[(address['Subaddre_6'] == 'SUITE') & address['addr:flats'].isnull(), 'addr:flats'] = address.loc[(address['Subaddre_6'] == 'SUITE') & address['addr:flats'].isnull(), 'Subaddre_7']
address.loc[(address['Subaddre_6'] == 'UNIT') & address['addr:unit'].isnull(), 'addr:unit'] = address.loc[(address['Subaddre_6'] == 'UNIT') & address['addr:unit'].isnull(), 'Subaddre_7']
address.loc[(address['Subaddre_6'] == 'APT') & address['addr:flats'].isnull(), 'addr:flats'] = address.loc[(address['Subaddre_6'] == 'APT') & address['addr:flats'].isnull(), 'Subaddre_7']


# Fixes
address.loc[address['addr:housenumber'].isin(['Vac-Unbld', 'Vac-Poten','2-Family', '1-Family', 'Mdl-96', '3-Family', '4-Family', 'Land-Undevl', '0', 'In-Law']), 'addr:housenumber'] = None

address.loc[address['addr:floor'].isin(['2FL', '2nd', '2ND']), 'addr:floor'] = "2"
address.loc[address['addr:floor'] == '1ST', 'addr:floor'] = "1"
address.loc[address['addr:floor'] == 'BSMT', 'addr:floor'] = "basement"

address.loc[address['addr:flats'].isin(['2ND FLR', '2ND FL', '2FL']), ['addr:flats','addr:floor']] = [None, "2"]
address.loc[address['addr:flats'] == '3FL#5', ['addr:flats','addr:floor']] = ["5", "3"]
address.loc[address['addr:flats'] == '1 2FL', ['addr:flats','addr:floor']] = ["1", "2"]
address.loc[address['addr:flats'] == '#3', 'addr:flats'] = "3"
address.loc[address['addr:flats'] == '3FL', ['addr:flats','addr:floor']] = [None, "3"]
address.loc[address['addr:flats'] == '1FL', ['addr:flats','addr:floor']] = [None, "1"]


address.loc[address['addr:unit'].isin(['Rd-Church', 'Rd-Firehouse', 'Lane-Rear', '4/5/2013.', '0']), 'addr:unit'] = None
address.loc[address['addr:unit'].notnull(), 'addr:unit'] = address.loc[address['addr:unit'].notnull(), 'addr:unit'].apply(lambda x: re.sub('[)(#)]', '', x))
address.loc[address['addr:unit'].notnull(), 'addr:unit'] = address.loc[address['addr:unit'].notnull(), 'addr:unit'].apply(lambda x: re.sub('Road', '', x))



# Remove no address buildings (those without housenumber and street name)
address = address.loc[address['addr:housenumber'].notnull() | address['addr:street'].notnull(), ]
address = address.reset_index()


# Remove unwanted columns
address = address.drop(columns=['TOWN', 'LOCATION', 'AddressNum', 'AddressN_1', 'AddressN_2',
       'StreetName', 'StreetNa_1', 'StreetNa_2', 'StreetNa_3', 'StreetNa_4',
       'StreetNa_5', 'StreetNa_6', 'Subaddress', 'Subaddre_1', 'Subaddre_3',
       'Subaddre_4', 'Subaddre_6', 'Subaddre_7', 'Municipal_', 'ZipCode',
       'ZipPlus4', 'LocationDe', 'Comments', 'CompleteAd', 'CompleteSt',
       'Source_Joi', 'Source_J_1', 'Source_J_2', 'temp_number', 'temp_unit', 
       'temp_street', 'temp_city', 'index'])


# Export unduplicated
address.to_file('/Buildigns_footprints_testing/Address/CTAddressAll-parsed.geojson', driver='GeoJSON')


## Deduplicate addresses by assigning unique address to the larges building
# Adresses are duplicated: All buildings on one parcel are tagged with the same address
# For buildings witch address countains housenumber remove duplicates by keeping only that building that has the largest area (most probably the main house on the parcel)
# First convert None to "none" otherwise groupby throws an error (groupby converts None to 'nan', which it can't later find in the grouping index)
address_dedup = address.fillna("none")
# Deduplicate addresses with houssenumber
address_dedup = address_dedup.loc[ address['addr:housenumber'].notnull() ].groupby(['addr:street', 'addr:housenumber', 'addr:postcode', 'addr:city', 'addr:unit', 'addr:building', 'addr:zip4', 'addr:flats', 'addr:floor'], dropna = False).apply(func = lambda x: x.loc[ x['area'] == x['area'].max() ])
address_remain = address.loc[address['addr:housenumber'].isnull()]
# Convert "none" back to None
address_dedup = address_dedup.replace(to_replace={'none': None}, value=None, method=None)

# Combine deduplicated addresses with those that don't have house number
address_dedup = pd.concat([address_remain, address_dedup]).pipe(gpd.GeoDataFrame)
address_dedup = address_dedup.reset_index()
address_dedup = address_dedup.drop(columns=['index', 'area'])
address_dedup.crs = "EPSG:4326"
address_dedup.to_file('/Buildigns_footprints_testing/Address/CTAddressDedup-parsed.geojson', driver='GeoJSON')
