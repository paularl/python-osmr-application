from funcs import *
import pandas as pd
#start_server("C:\\Users\\paula.romero.lopes\\Projects\\route_optimization\\", "spain-latest.osrm")

data = read_input("C:\\Users\\paula.romero.lopes\\Projects\\route_optimization\\Mock_Addresses.csv", sep=";")

print("------------Time Matrix---------------")

coords_array, coords_str = prepare_coords(data, "Latitude", "Longitude")
time_mat = time_matrix(coords_str, list(data.ID), save=True)
print(time_mat)

print("-------Distance Matrix----------------")

dist_matrix, routes = distance_matrix(coords_array,list(data.ID), save=True)
print(dist_matrix)
print("-------Routes-------------------------")
print(routes)
print("-------add new point -----------------")
data = add_new_point(data, ([999, "Portugal", 11, "08027", "Barcelona", "Spain", 41.408578, 2.159751],
                            [9999, "Providencia", 89, "08024", "Barcelona", "Spain", 41.426214, 2.190551]))
coords_array, coords_str = prepare_coords(data, "Latitude", "Longitude")
time_mat = time_matrix(coords_str, list(data.ID), save=True)

print(time_mat)
data_matrix, geom = update_matrix(data, "output\\distance_matrix.csv", save=True)
rutas = create_json()
feat_collection = {"type": "FeatureCollection",
                   "features": rutas}
create_maps(data,list(data.ID),feat_collection,central_coords = [41.387273, 2.170111])
print("---------------")
#print(geom)
i = list(data.ID)
l = [9,5,1,4,2,6,3,8,7,13,16,12,11,10,14,15]
route_order = pd.DataFrame({'ID':i,'Pos':l})
print(route_order)
final_routes = calculated_route(data, route_order)
rutas = create_json_final_route("output\\final_route.txt")

feat_collection = {"type": "FeatureCollection",
                   "features": rutas}

create_maps(data,list(data.ID),feat_collection,central_coords = [41.387273, 2.170111])
