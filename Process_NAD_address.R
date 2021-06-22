#!/usr/bin/env Rscript

library(tidyverse)
library(data.table)
library(sf)

addr <- fread("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/NAD_r6_CT_header.csv", colClasses = list(character=c("Zip_Code", "Plus_4")))

addr <- st_as_sf(addr, coords = c("Longitude", "Latitude"), crs = 4326) 

addr <- addr %>% select(Unit, Building, AddNum_Suf, Add_Number, AddNum_Pre, StN_PosMod, StN_PosDir, StN_PreDir, StN_PosTyp, StN_PreTyp, Zip_Code, Post_Comm, StreetName, geometry)
            
addr <- addr %>% 
        mutate(`addr:housenumber` = paste(AddNum_Pre, Add_Number, AddNum_Suf, sep = " "),
               `addr:housenumber` = str_trim(`addr:housenumber`, side = c("both")),
               `addr:city` = str_to_title(Post_Comm),
               `addr:state` = "CT") %>%
        mutate(StreetName = str_replace_all(StreetName, c("\\(Rear\\)" = "", "\\(CITY\\)" = "", "\\(MYSTIC\\)" = "", "\\(NOANK\\)" = "", "\\(GLP\\)" = "", "\\(WEST SIDE\\)" = "", "\\(2\\)" = " 2", "\\(1\\)" = " 1", "\\(3\\)" = " 3", "\\(6\\)" = " 6", "\\(OCCUM\\)" = "", "\\(SOWIND\\)" = "")),
               StreetName = str_replace_all(StreetName, c("\\bAve\\b" = "Avenue", "\\bSt\\b" = "Street", "\\bDr\\b" = "Drive", "\\bTrl\\b" = "Trail", "\\bLn\\b" = "Lane", "\\bPl\\b" = "Place", "\\bLk\\b" = "Lake", 
                "\\bRd\\b" = "Road", "\\bHl\\b" = "Hill", "\\bE\\b" = "East", "\\bW\\b" = "West", "\\bN\\b" = "North", "\\bS\\b" = "South", "\\bTr\\b" = "Trail", "\\bTerr\\b" = "Terrace", "\\bTpke\\b" = "Turnpike", "\\bNB\\b" = "Northbound", "\\bSB\\b" = "Southbound", 
                "\\bCt\\b" = "Court", "\\bPt\\b" = "Point", "\\bExt\\b" = "Extension", "\\bPk\\b" = "Park")),
               `addr:street` = if_else(StN_PreTyp != "", paste(StN_PreTyp, str_to_title(StreetName), StN_PosMod, sep = " "), NA_character_),
               `addr:street` = if_else(StN_PreTyp == "", paste(StN_PreDir, str_to_title(StreetName), StN_PosTyp, StN_PosDir, sep = " "), `addr:street`),
               `addr:street` = str_squish(`addr:street`)) %>%
        mutate(`addr:city` = str_replace_all(`addr:city`, c("E " = "East ", "W " = "West ", "No " = "North ", "So " = "South " ))) %>%
        rename(`addr:building` = Building,
               `addr:postcode` = Zip_Code) %>%
        mutate(`addr:unit` = case_when(
                                str_detect(Unit, "Unit") ~ str_replace(Unit, "^Unit ", ""),
                                str_detect(Unit, "UNIT") ~ str_replace(Unit, "^UNIT ", ""),
                                str_detect(Unit, "Apartment") ~ str_replace(Unit, "^Apartment ", ""),
                                str_detect(Unit, "Suite") ~ str_replace(Unit, "^Suite ", ""),
                                str_detect(Unit, "Room") ~ str_replace(Unit, "^Room ", ""),
                                str_detect(Unit, "#") ~ str_replace(Unit, "^#", ""),
                                str_detect(Unit, "-") ~ str_replace(Unit, "^-", ""),
                                str_detect(Unit, "^UN") ~ str_replace(Unit, "^UN", ""),
                                TRUE ~ Unit )) %>%
        select(-StreetName, -StN_PosTyp, -AddNum_Pre, -Add_Number, -AddNum_Suf, -Post_Comm, -StN_PreTyp, -StN_PosMod, -StN_PosTyp, -StN_PosDir, -StN_PreDir)


# Fixing individual cases of Unit values
addr <- addr %>% mutate(`addr:unit` = case_when(
                                Unit == "Floor 1, Unit 1" ~ "1",
                                Unit == "Floor 1, Unit Right" ~ "Right",
                                Unit == "Floor 1, Unit Left" ~ "Left",
                                Unit == "3FL#5" ~ "5",
                                Unit == "1, 2FL" ~ "1",
                                Unit == "1FL" ~ NA_character_,
                                Unit == "2FL" ~ NA_character_,
                                Unit == "3FL" ~ NA_character_,
                                Unit == "1ST" ~ NA_character_,
                                str_detect(Unit, "Lot") ~ NA_character_,
                                Unit == "Apartment" ~ NA_character_,
                                Unit == "Suite" ~ NA_character_,
                                Unit == "Level 1, Suite 101" ~ "101",
                                Unit == "Floor 1, Suite 3" ~ "3",
                                Unit == "Level 2, Suite 202" ~ "202",
                                Unit == "Level 2, Suite 203" ~ "203",
                                Unit == "Floor 2, Suite 5" ~ "5",
                                Unit == "Level 1, Suite 102" ~ "102",
                                Unit == "Level 1, Suite 103" ~ "103",
                                Unit == "Level 1, Suite 104" ~ "104",
                                Unit == "Floor 1, Suite 8" ~ "8",
                                Unit == "Floor 1" ~ NA_character_,
                                Unit == "Floor 2" ~ NA_character_,
                                Unit == "Floor 1ST" ~ NA_character_,
                                Unit == "Floor 2ND" ~ NA_character_,
                                Unit == "Main Bldg" ~ NA_character_,
                                Unit == "Rear Bldg" ~ NA_character_,
                                Unit == "Building RR" ~ NA_character_,
                                str_detect(Unit, "Bsmt") ~ NA_character_,
                                Unit == "Basement" ~ NA_character_,
                                Unit == "Bsmnt" ~ NA_character_,
                                Unit == "1ST FL" ~ NA_character_,
                                Unit == "2ND FL" ~ NA_character_,
                                Unit == "2NDFL" ~ NA_character_,
                                Unit == "3ND FL" ~ NA_character_,
                                Unit == "Laundry Building" ~ NA_character_,
                                Unit == "Rear Shop" ~ NA_character_,
                                Unit == "Cottage" ~ NA_character_,
                                Unit == "Floor 3" ~ NA_character_,
                                Unit == "2RD F" ~ NA_character_,
                                Unit == "3RD F" ~ NA_character_,
                                Unit == "3RD" ~ NA_character_,
                                Unit == "3RD FL" ~ NA_character_,
                                Unit == "BLD A15" ~ NA_character_,
                                Unit == "2 FL" ~ NA_character_,
                                Unit == "A5 3FL" ~ "A5",
                                Unit == "2ND FLR" ~ NA_character_,
                                Unit == "Floor 2 2W" ~ "2W",
                                Unit == "2ND" ~ NA_character_,
                                Unit == "?" ~ NA_character_,
                                Unit == "3FL#5" ~ "5",
                                Unit == "Unit" ~ NA_character_,
                                Unit == "2FLR" ~ NA_character_,
                                Unit == "1FL N" ~ "N",
                                Unit == "1FL REAR" ~ "Rear",
                                Unit == "1ST FLR" ~ NA_character_,
                                Unit == "1, 2FL" ~ "1",
                                Unit == "2FLR SM" ~ "SM",
                                str_detect(Unit, "Building ") ~ NA_character_,
                                Unit == "Building" ~ NA_character_,
                                str_detect(Unit, "Bldg ") ~ NA_character_,
                                Unit == "Med Arts Bldg" ~ NA_character_,
                                Unit == "Level 1, Suite 101" ~ "101",
                                Unit == "Floor 1, Suite 3" ~ "3",
                                Unit == "Level 2, Suite 202" ~ "202",
                                Unit == "Level 2, Suite 203" ~ "203",
                                str_detect(Unit, "Condo") ~ NA_character_,
                                Unit == "Level 2, Suite 5" ~ "5",
                                Unit == "Level 1, Suite 102" ~ "102",
                                Unit == "Level 1, Suite 102" ~ "103",
                                Unit == "Level 1, Suite 104" ~ "104",
                                Unit == "2nd Floor" ~ NA_character_,
                                Unit == "FL1" ~ NA_character_,
                                Unit == "FL2" ~ NA_character_,
                                Unit == "MAIN" ~ NA_character_,
                                Unit == "+ 206 (BETWEEN" ~ "206",
                                Unit == "(8" ~ "8",
                                Unit == "U #101" ~ "101",
                                Unit == "[REAR]" ~ "Rear",
                                Unit == "Garage" ~ NA_character_,
                                Unit == "Sprinkler Rm" ~ "Sprinkler Room",
                                TRUE ~ `addr:unit`
                                ))



addr <-addr %>% mutate(`addr:floor` = case_when(
                                Unit == "Floor 1, Unit 1" ~ "1",
                                Unit == "Floor Bsmt" ~ "Basement",
                                Unit == "Floor 1, Unit Right" ~ "1",
                                Unit == "Floor 1, Unit Left" ~ "1",
                                Unit == "3FL#5" ~ "3",
                                Unit == "1, 2FL" ~ "2",
                                Unit == "1FL" ~ "1",
                                Unit == "2FL" ~ "2",
                                Unit == "3FL" ~ "3",
                                Unit == "1ST" ~ "1",
                                Unit == "Level 1, Suite 101" ~ "1",
                                Unit == "Floor 1, Suite 3" ~ "1",
                                Unit == "Level 2, Suite 202" ~ "2",
                                Unit == "Level 2, Suite 203" ~ "2",
                                Unit == "Floor 2, Suite 5" ~ "2",
                                Unit == "Level 1, Suite 102" ~ "1",
                                Unit == "Level 1, Suite 103" ~ "1",
                                Unit == "Level 1, Suite 104" ~ "1",
                                Unit == "Floor 1, Suite 8" ~ "1",
                                Unit == "Floor 1" ~ "1",
                                Unit == "Floor 2" ~ "2",
                                Unit == "Floor 1ST" ~ "1",
                                Unit == "Floor 2ND" ~ "2",
                                Unit == "Floor Bsmt" ~ "Basement",
                                Unit == "Bsmnt" ~ "Basement",
                                Unit == "Basement" ~ "Basement",
                                Unit == "1ST FL" ~ "1",
                                Unit == "2ND FL" ~ "2",
                                Unit == "2NDFL" ~ "2",
                                Unit == "3ND FL" ~ "3",
                                Unit == "Floor 3" ~ "3",
                                Unit == "2RD F" ~ "2",
                                Unit == "3RD F" ~ "3",
                                Unit == "3RD" ~ "3",
                                Unit == "3RD FL" ~ "3",
                                Unit == "2 FL" ~ "2",
                                Unit == "A5 3FL" ~ "3",
                                Unit == "2ND FLR" ~ "2",
                                Unit == "Floor 2 2W" ~ "2",
                                Unit == "2ND" ~ "2",
                                Unit == "3FL#5" ~ "3",
                                Unit == "2FLR" ~ "2",
                                Unit == "1FL N" ~ "1",
                                Unit == "1FL REAR" ~ "1",
                                Unit == "1ST FLR" ~ "1",
                                Unit == "1, 2FL" ~ "2",
                                Unit == "2FLR SM" ~ "2",
                                Unit == "Level 1, Suite 101" ~ "1",
                                Unit == "Floor 1, Suite 3" ~ "1",
                                Unit == "Level 2, Suite 202" ~ "2",
                                Unit == "Level 2, Suite 203" ~ "2",
                                Unit == "Level 2, Suite 5" ~ "2",
                                Unit == "Level 1, Suite 102" ~ "1",
                                Unit == "Level 1, Suite 102" ~ "1",
                                Unit == "Level 1, Suite 104" ~ "1",
                                Unit == "2nd Floor" ~ "2",
                                Unit == "FL1" ~ "1",
                                Unit == "FL2" ~ "2"
                                ))

addr <- addr %>% mutate(`addr:building` = case_when(
                                str_detect(Unit, "Lot") ~ Unit,
                                Unit == "Main Bldg" ~ "Main Building",
                                Unit == "Rear Bldg" ~ "Rear Building",
                                Unit == "Building RR" ~ "Building RR",
                                Unit == "Laundry Building" ~ "Laundry Building",
                                Unit == "Rear Shop" ~ "Rear Shop",
                                Unit == "Cottage" ~ "Cottage",
                                Unit == "BLD A15" ~ "A15",
                                str_detect(Unit, "Building ") ~ str_replace(Unit, "^Building ", NA_character_),
                                str_detect(Unit, "Bldg ") ~ str_replace(Unit, "^Bldg ", NA_character_),
                                Unit == "Med Arts Bldg" ~ "Med Arts Bldg",
                                str_detect(Unit, "Condo") ~ Unit,
                                Unit == "MAIN" ~ "Main",
                                Unit == "Garage" ~ Unit,
                                TRUE ~ `addr:building`
                                ))

addr <- addr %>% select(-Unit) %>%
                 mutate(across(everything(), ~na_if(.x , "") ))

# Add missing zipcodes, fix East Hampton which had only 1 zipcode, correct Windham Zipcode 02814 -> NA_character_
# https://data.ct.gov/Government/Zip-Code-Tabulation-Area-Boundaries/n7kw-xx5z
# https://data.ct.gov/api/geospatial/n7kw-xx5z?method=export&format=GeoJSON
zipArea <- st_read("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/Zip Code Tabulation Area Boundaries.geojson") %>% 
            select(zcta5ce10)       

addr <- st_join(addr, zipArea, join = st_intersects, left = TRUE) %>% 
                    mutate(`addr:postcode` = if_else(is.na(`addr:postcode`), zcta5ce10, `addr:postcode`),
                           `addr:postcode` = if_else(`addr:city` == "East Hampton", zcta5ce10, `addr:postcode`),
                           `addr:postcode` = if_else(str_detect(`addr:postcode`, "028"), NA_character_, `addr:postcode`)) %>%
                    select(-zcta5ce10)    
                        


st_write(addr, "~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/CT-address.geojson")





