import pandas as pd
import requests
import os
import pickle
import json
import numpy as np
import random

# a function to start the local server. it does not work properly yet, so better to do in the terminal

def start_server(path, osrm_file, port=5000):
    
    os.chdir(path)
    os.chdir("osrm_Release")
    os.system("osrm-routed.exe " + "--max-table-size=1000 "+ "..\\data\\" + osrm_file  +  " --port " + str(port))
    input("Press Enter...")
    print("cmd /K osrm-routed.exe " + "..\\data\\" + osrm_file + " --verbosity NONE")
    print("............Server Starting on port %s" % port)
    os.chdir(path)

# read input data -> id, lat, long as the minimal. Read is as pandas dataframe
    
def read_input(input_file,sep):

    data = pd.read_csv(input_file, sep=sep)
    return data

# add new point to the dataframe
    
def add_new_point(data, new_point_array):

    if len(new_point_array) > 1:
        for point in new_point_array:
            data.loc[len(data)] = point
    else:
        data.loc[len(data)] = new_point_array

    return data

# prepare the coordinates as a string to put in the url to request to the server
    
def prepare_coords(data, col_lat, col_lon):

    # all coords as string in the order of the the dataframe
    coords_array_str = ''
    # an array of coordiantes (numeric) for other analysis
    
    coords_array = []
    for i in list(data.index):
        coords_s = "%s,%s" % (data[col_lon][i], data[col_lat][i])
        coords_n = [data[col_lon][i], data[col_lat][i]]
        coords_array_str = coords_array_str + coords_s + ";"
        coords_array.append(coords_n)
    coords_array_str = coords_array_str[:-1]

    return coords_array, coords_array_str

#   
def time_matrix(coords_array_str, idxs, save=True, path_to_save= "", file_name="time_matrix.csv"):

    """ request the time matrix data to the local server. """
    
    print("requesting time matrix from local server..............")
    response_matrix = requests.get('http://localhost:5000/table/v1/driving/' + coords_array_str)
    print(response_matrix.json()['durations'])
    df = pd.DataFrame(response_matrix.json()['durations'], index=idxs, columns=idxs)
    for c in df.columns:
        df[c] = np.round(df[c] / 60, 2)

    print(df)
    if save == True:

        df.to_csv(path_to_save + file_name)

    return df

def distance_matrix(coords_array, idxs, save=True, path_to_save= "output"):

    """ Calculate distance matrix for each pair of points AND the routes netween the pairs. Very slow due its pair-wise character """
    
    l_geom = []
    dist_matrix = []
    for j in coords_array:

        l_dist = []

        for i in coords_array:

            q = (str(j[0]) + ',' + str(j[1]) + ";" + str(i[0]) + ',' + str(i[1]))
            response = requests.get('http://localhost:5000/route/v1/driving/' + q + "?geometries=geojson")
            content = response.json()
            # save distance
            l_dist.append(content["routes"][0]['distance'])
            # save routes
            l_geom.append(content["routes"][0])

        dist_matrix.append(np.round(l_dist,2))
    dist_df = pd.DataFrame(dist_matrix, index=idxs, columns=idxs)

    if save==True:

     with open(path_to_save + "\\routes.txt", 'w') as filehandle:
         json.dump(l_geom, filehandle)
    dist_df.to_csv(path_to_save + "\\distance_matrix.csv")

    print(len(l_geom))
    return dist_df, l_geom

def update_matrix(new_data, matrix_csv, save = True):

    """ Update the distance matrix for a new point added. """
    old_data = pd.read_csv(matrix_csv, header=0, index_col=0)

    old_data_pts = [int(i) for i in old_data.columns]
    new_data_pts = [int(i) for i in list(new_data.ID)]

    temp = [i for i in new_data_pts if i not in old_data_pts]


    if old_data_pts == new_data_pts:
        print("data already updated")

    else:
        l_geom = []
        data = old_data
        for t in temp:
            data[t] = ""
        # From new point to others
        new_line_distance = []
        for i in temp:

            l_dist = []

            point = (new_data.loc[new_data.ID==i])
            #other_data = (new_data.loc[new_data.Number!=i])
            other_data = new_data
            coords_point = float(point["Longitude"]), float(point["Latitude"])
            print(coords_point)
            coords_array,_ = prepare_coords(other_data, "Latitude", "Longitude")

            for c in coords_array:

                q = (str(coords_point[0]) + ',' + str(coords_point[1]) + ";" + str(c[0]) + ',' + str(c[1]))
                response = requests.get('http://localhost:5000/route/v1/driving/' + q + "?geometries=geojson")
                content = response.json()

                l_dist.append(content["routes"][0]['distance'])
                l_geom.append(content["routes"][0])

            data.loc[len(data)] = np.round(l_dist,2)

    # From other points to new

    l_dist = []
    for c in coords_array:

        for i in temp:

            point = (new_data.loc[new_data.ID == i])
            coords_point = float(point["Longitude"]), float(point["Latitude"])

            q = (str(c[0]) + ',' + str(c[1]) + ";" + str(coords_point[0]) + ',' + str(coords_point[1]))
            response = requests.get('http://localhost:5000/route/v1/driving/' + q + "?geometries=geojson")
            content = response.json()
            l_dist.append(content["routes"][0]['distance'])
            l_geom.append(content["routes"][0])


    l_dist = np.array(l_dist)
    l_dist = l_dist.reshape(len(coords_array),len(temp))

    data_list = []
    for t in range(len(temp)):
        for l in range(len(new_data)):
            data_list.append(l_dist[l][t])
    data_list = np.array(data_list).reshape(len(temp),len(new_data))

    for i,t in enumerate(temp):
        data[t] = data_list[i]

    print("--------------------")
    print(len(l_geom))
    if save==True:

     with open("output" + "\\routes.txt", 'r') as filehandle:
         rutas = json.load(filehandle)

         [rutas.append(g) for g in l_geom]
     with open("output" + "\\routes.txt", 'w') as filehandle:
        r = json.dump(rutas,filehandle)

     data.to_csv("output" + "\\distance_matrix.csv")

    return data, l_geom

## ----------------- Routes --------------------------------------------------#
    
def calculated_route(data, route_order):

    """ Calcualte the unique `best`route passing at all points in the order of the route order parameters
    :route_order: a vector/list with the order of the points in the datatable"""
    
    df = data.join(route_order, on="ID", how="left", lsuffix="b")
    df = df.sort_values(["Pos"])
    print(df)
    coords_array, coords_array_str = prepare_coords(df, "Latitude", "Longitude")

    q = coords_array_str
    response = requests.get('http://localhost:5000/route/v1/driving/' + q + "?geometries=geojson")
    
    content = response.json()
    print(content)
    
    final_route = content["routes"][0]

    with open("output\\final_route.txt", 'w') as filehandle:
        rutas = json.dump(final_route,filehandle)

    return final_route
# ------------------ MAPS ----------------------------------------------------#
# Create geojson objects to be loaded in any map application. 
def create_json(filein = "output\\routes.txt"):
    """ Use this when there are more than one route to be plotted in the map """
    
    with open(filein, 'r') as filehandle:
        rutas = json.load(filehandle)

    data_dict = []

    for i, ruta in enumerate(rutas):
        color = "#%06x" % random.randint(0, 0xFFFFFF)
        print(color)
        name = "ruta_%d" % i
        dict_geo = {"type": "Feature",
                    "geometry": ruta["geometry"],
                    "properties": {
                        "name": name,
                        "duration": ruta["duration"],
                        "color": color}
                    }
        data_dict.append(dict_geo)

    with open("output\\routes_properties.txt", 'w') as filehandle:
        rutas = json.dump(data_dict, filehandle)

    return data_dict



def create_json_final_route(filein, color="black"):
    """ use this to generate the final route object as geojson to be plotted in the map """    
    with open(filein, 'r') as filehandle:
        ruta = json.load(filehandle)

    data_dict = []
    
    name = "final route"
    dict_geo = {"type": "Feature",
                "geometry": ruta["geometry"],
                    "properties": {
                    "name": name,
                    "duration": ruta["duration"],
                    "distance": ruta["distance"],
                    "color": color}
                    }

    return dict_geo

def create_maps(data, idxs, rutas, prop,central_coords = [41.387273, 2.170111], map_name="map"):

    ''' Create a map object with folium lib. To be implemented colors as geojson attribute'''

    import folium
    import branca

    coords_array, _ = prepare_coords(data, "Latitude", "Longitude")

    map_object = folium.Map(location=central_coords, zoom_start=12)

    data.apply(lambda row: folium.Marker(location=[row["Latitude"],
                                                   row["Longitude"]],
                                         popup=folium.Popup(branca.element.IFrame(
                                               html="<p>ID: %i</p><p>%s</p>" % (row["ID"], row[prop]),
                                               width=180, height=65),
                                               parse_html=True)).add_to(map_object), axis=1)


    folium.GeoJson(rutas, name = "routes", style_function = lambda feature: {
                 'color': feature['properties']['color']}).add_to(map_object)

    folium.Map.save(map_object, map_name+".html")




# Find trip - similar to calculated route function but with onther method of the api
def find_trip(data):
    
    coords_array, coords_array_str = prepare_coords(data, "Latitude", "Longitude")

    q = coords_array_str
    response = requests.get('http://localhost:5000/trip/v1/driving/' + q + "?geometries=geojson")
    content = response.json()
    final_trip = content["trips"][0]

    with open("output\\final_trip.txt", 'w') as filehandle:
        rutas = json.dump(final_trip,filehandle)

    return final_trip

