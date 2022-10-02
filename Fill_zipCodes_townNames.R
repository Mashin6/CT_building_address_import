library(tidyverse)
library(data.table)
library(sf)
library(osmdata)

q <- "[out:xml][timeout:2500];
rel[\"name\"=\"Connecticut\"][admin_level=4];
map_to_area->.a;
nwr[\"addr:housenumber\"][!\"addr:postcode\"](area.a);
(._; >;);
out body;
"
op_addresses <- osmdata_sf(q)

osm_addresses <- op_addresses$osm_polygons |>
    bind_rows(op_addresses$osm_multipolygon) |>
    bind_rows(op_addresses$osm_points) |>
    filter(!is.na(addr.housenumber), is.na(addr.postcode)) |>
    select(osm_id, addr.city, addr.housenumber, addr.street, addr.postcode, addr.unit, geometry) |>
    mutate(geometry = st_make_valid(geometry)) |>
    mutate(geometry = st_centroid(geometry))


zipArea <- st_read("~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/Zip Code Tabulation Area Boundaries.geojson") |> 
    select(zcta5ce10)       

osm_addresses <- st_join(osm_addresses, zipArea, join = st_intersects, left = TRUE) |>
    mutate(addr.postcode = zcta5ce10) |>
    select(-zcta5ce10)    


tq <-"[out:xml][timeout:2500];
rel[\"name\"=\"Connecticut\"][admin_level=4];
map_to_area->.a;
rel[boundary=administrative][admin_level=8](area.a);
(._; >;);
out body;
"
op_towns <- osmdata_sf(tq)

osm_towns <- op_towns$osm_multipolygons |>
                select(name) |>
                rename(town_name = "name")

osm_addresses <- st_join(osm_addresses, osm_towns, join = st_intersects, left = TRUE) |>
    mutate(addr.city = if_else(is.na(addr.city), town_name, addr.city)) |>
    select(-town_name) 

osm_addresses <- osm_addresses |>
    select(-osm_id) |>
    dplyr::rename(`addr:postcode` = addr.postcode, `addr:housenumber` = addr.housenumber,
                  `addr:city` = addr.city, `addr:street` = addr.street, `addr:unit` = addr.unit)

st_write(osm_addresses, "~/Desktop/Buildings/NAD_address/NAD_r6_TXT/TXT/filled_zipCode_townName.geojson")
