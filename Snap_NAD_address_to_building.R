#!/usr/bin/env Rscript

library(tidyverse)
library(data.table)
library(sf)
library(osmdata)

# Iterative approach of snapping address points to the nearest building within 100 m radius.
# Note: Name of own have to be manually changes in 'townName'

townName <- "Harwinton"

addrnodes <- st_read("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/CT-address.geojson") %>%
                filter(addr.city == townName) %>%
                mutate(addr_id = 1:nrow(.))

st_write(addrnodes, paste0("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/CT-address-", townName, ".geojson"))


buildings <-  opq(paste0(townName, " Connecticut")) %>%
                add_osm_feature(key="building") %>%
                osmdata_sf()

# Remove garages and shed that are typically < 70 m^2
build <- buildings$osm_polygons %>%
            bind_rows(buildings$osm_multipolygon) %>%
            select(geometry) %>%
            mutate(geometry = st_make_valid(geometry)) %>%
            filter(st_area(geometry) > units::set_units(70, m^2)) %>%
            mutate(build_id = 1:nrow(.),
                   centroid = st_centroid(geometry))


# Match addresses with buildings
match_table <- st_join(addrnodes, build, join = st_intersects, left = TRUE)

# find out number of addresspoints inside each building
match_table <- match_table %>%
                 group_by(build_id) %>% 
                 mutate(n_overlaps = n()) %>%
                 ungroup() %>% mutate(n_overlaps = if_else(is.na(build_id), 0, as.numeric(n_overlaps)))
    # NOTE: I should deduplicate so we don't double addresses in case one overlaps with multiple buildings

# 1) If there are multiple address points in one building => keep those points untouched               
addr_final <- match_table %>% 
                    filter(n_overlaps > 1) %>%
                    select(1:10) 

# 2) If there is only a single address in one building => move point to centroid
addr_final <- addr_final %>%
                add_row(match_table %>% 
                            filter(n_overlaps == 1) %>%
                            mutate(geometry = centroid) %>%
                            select(1:10)
                        )                    


# Collect unmatched addresses and unmatched buildings
addr_remain <- addrnodes %>% filter(!addr_id %in% addr_final$addr_id)
build_remain <- build %>% filter(!build_id %in% addr_final$build_id)


# 3) Match address to the closest largest building
# Iteratively increase distance in case a building already has a matched address node

for (dist in c(1:20 * 5)) {
    # Refresh building index
    build_remain <- build_remain %>%
                        mutate(build_id = 1:nrow(.))
    # Flush nearest building id records in addr_final
    #addr_remain$nearest_id <- 0
    addr_final$build_id <- 0
    
    # Calculate distance between address nodes and closest buildings
    addr_remain <- addr_remain %>% 
                        mutate(nearest_id = build_remain[st_nearest_feature(geometry, build_remain), ] %>% pull("build_id"),
                               nearest_dist = st_distance(geometry, build_remain[nearest_id, ], by_element = TRUE)) %>%
                        mutate(centroid = build_remain$centroid[.$nearest_id])
    
    # To a building, assign only the most closest address  (keep the rest for the next round of matching)
    addr_final <- addr_final %>% 
                    add_row(addr_remain %>% 
                                filter(nearest_dist < units::set_units(dist, m)) %>%
                                mutate(geometry = centroid) %>%
                                group_by(nearest_id) %>% 
                                filter(nearest_dist == min(nearest_dist)) %>% 
                                ungroup() %>%
                                mutate(build_id = nearest_id) %>%
                                select(1:10,14)
                            )
    
    # Update remaining addresses and buildings
    addr_remain <- addr_remain %>% filter(!addr_id %in% addr_final$addr_id)
    build_remain <- build_remain %>% filter(!build_id %in% addr_final$build_id)
    
}

addr_final <- addr_final %>% 
                add_row(addr_remain %>% 
                            select(1:10))


# Turn house numbers like "257 -59" into "257;559"
    addr_final <- addr_final %>% 
                        rowwise() %>% 
                        mutate(addr.housenumber = if_else(str_detect(addr.housenumber, " -"), 
                                                          paste0(unlist(str_split(addr.housenumber, " ")), collapse = "") , 
                                                          addr.housenumber))


    for (row in 1:nrow(addr_final)) {
        if (str_detect(addr_final$addr.housenumber[row], "-") & !str_detect(addr_final$addr.housenumber[row], "[^0-9-]+")) {
            vals <- str_split(addr_final$addr.housenumber[row], "-") %>% unlist()

            back <- str_sub(vals[1], -nchar(vals[2]), -1)
            if (back < vals[2]){
                front <- str_sub(vals[1], 0, -nchar(vals[2]) - 1)
                new <- paste0(vals[1], ";", front, vals[2])
                addr_final$addr.housenumber[row] <- new
            }
            if (back > vals[2]){
                front <- str_sub(vals[1], 0, -nchar(vals[2]) - 1)
                front <- as.numeric(front) + 1
                new <- paste0(vals[1], ";", front, vals[2])
                addr_final$addr.housenumber[row] <- new
            }
        }
    }

# Remove duplicates
addr_final <- addr_final %>% 
                distinct() %>%
                select(-addr_id, -build_id) %>%
                dplyr::rename(`addr:building` = addr.building, `addr:postcode` = addr.postcode, `addr:housenumber` = addr.housenumber,
                       `addr:city` = addr.city, `addr:state` = addr.state, `addr:street` = addr.street, `addr:unit` = addr.unit,
                       `addr:floor` = addr.floor)



st_write(addr_final, paste0("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/CT-address-", townName, "-IterSnapped.geojson"))

