# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 12:54:34 2018

@author: paula.romero.lopes

Data source: abrcelona Open Data. Comercial Locals in barcelona.
"""
from random import shuffle
from funcs import *
### 0000. Remember to start the server in the terminal!

# osrm-routed.exe --max-table-size=1200 \data\spain-latest.osrm --port 5000
# max table size is the max points you can introduce to calculate the time matrix.

## 0. read and prepare data

df = pd.read_csv("locals.csv", encoding="latin1")
data = df.sample(n=1000)
data = data[["ID_BCN","N_CARRER", "N_LOCAL", "LATITUD", "LONGITUD"]]
data.rename(columns={"ID_BCN":"ID",'LONGITUD': 'Longitude', 'LATITUD': 'Latitude'},inplace=True)

## 1. Calculate time matrix 

print("------------Time Matrix---------------")
coords_array, coords_str = prepare_coords(data, "Latitude", "Longitude")
time_mat = time_matrix(coords_str, list(data.ID), save=True)

## 2. Calculate distance matrix and routes between all points. Go take a coffee!

print("------- Distance Matrix --------------")
dist_matrix, routes = distance_matrix(coords_array,list(data.ID), save=True)
print("-------Routes-------------------------")

## 3. add a new point

data = add_new_point(data, ([1002, "Portugal", 11, 41.408578, 2.159751],
                            [1003, "Providencia", 89, 41.426214, 2.190551]))

## 3.1 Recalculate time matrix

coords_array, coords_str = prepare_coords(data, "Latitude", "Longitude")
time_mat = time_matrix(coords_str, list(data.ID), save=True)

## 3.2 Update distance matrix. Another coffee?

data_matrix, geom = update_matrix(data, "output\\distance_matrix.csv", save=True)

## 4. Prepare data for mapping

## 4.1 Create geojson from routes.txt file

rutas = create_json()

## 4.2 Create feature collection from rutas

feat_collection = {"type": "FeatureCollection",
                   "features": rutas}

## 4.3 Finally create the map

create_maps(data,list(data.ID),feat_collection,central_coords = [41.387273, 2.170111])

### 5. OR create a route with already defined orders points

i = list(data.ID)
l = [i for i in range(len(data))]
shuffle(l) ### -> your order for the points to follow 
route_order = pd.DataFrame({'ID':i,'Pos':l})

# calculate unique optimal route
final_routes = calculated_route(data, route_order)
with open("output\\final_route.geojson", 'w') as filehandle:
        rutas = json.dump(final_routes,filehandle)

rutas = create_json_final_route("output\\final_routes.txt")
feat_collection = {"type": "FeatureCollection",
                   "features": rutas}
# and generate the map
create_maps(data,list(data.ID),rutas,"N_CARRER",central_coords = [41.387273, 2.170111], map_name="map_locals")

data.to_csv("sample_data.csv")




